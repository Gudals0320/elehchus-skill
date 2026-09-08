"""Read-only photo evidence and review candidates. No file mutation API.

Small-corpus lab implementation: bounded in-memory byte snapshots ensure metadata,
hash and exact-byte comparison refer to the same observed contents.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
import warnings

import PIL
from PIL import Image, ImageOps, UnidentifiedImageError

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.webp',
                    '.heic', '.heif', '.avif', '.dng', '.cr2', '.cr3', '.nef', '.arw', '.bmp'}
DATE_TAGS = ((36867, 36881, 37521, 'DateTimeOriginal', 'capture'),
             (36868, 36882, 37522, 'DateTimeDigitized', 'digitized'),
             (306, 36880, 37520, 'DateTime', 'modified'))


class BudgetExceeded(ValueError):
    pass


def _text(value):
    if value is None:
        return None
    return (value.decode('ascii', errors='replace') if isinstance(value, bytes)
            else str(value)).rstrip('\x00').strip()


def parse_exif_date(value, offset=None, subsecond=None):
    """Preserve local wall time. Never invent a timezone or use filesystem mtime."""
    raw, off, sub = _text(value), _text(offset), _text(subsecond)
    out = dict(raw=raw, offset_raw=off, subsecond_raw=sub, local=None, utc=None,
               status='missing', warnings=[])
    if not raw:
        return out
    try:
        if not re.fullmatch(r'\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}', raw):
            raise ValueError('not EXIF date syntax')
        wall = datetime.strptime(raw, '%Y:%m:%d %H:%M:%S')
    except ValueError:
        out['status'] = 'invalid_date'
        return out
    fraction = ''
    if sub:
        if re.fullmatch(r'\d+', sub):
            fraction = '.' + sub  # retain precision, no silent microsecond rounding
        else:
            out['warnings'].append('invalid_subsecond')
    out['local'] = wall.isoformat() + fraction
    out['status'] = 'timezone_unknown'
    if off:
        match = re.fullmatch(r'([+-])(\d{2}):(\d{2})', off)
        if not match or int(match[2]) > 23 or int(match[3]) > 59:
            out['status'] = 'invalid_offset'
        else:
            minutes = (int(match[2])*60 + int(match[3])) * (1 if match[1]=='+' else -1)
            try:
                utc = wall.replace(tzinfo=timezone(timedelta(minutes=minutes))).astimezone(timezone.utc)
                out['utc'] = utc.strftime('%Y-%m-%dT%H:%M:%S') + fraction + 'Z'
                out['status'] = 'offset_known'
            except (ValueError, OverflowError):
                out['status'] = 'invalid_offset'
    return out


def _error(row, stage, exc):
    # Pillow's unidentified BytesIO message embeds a process-specific address.
    message = ('cannot identify image from byte snapshot' if isinstance(exc, UnidentifiedImageError)
               else re.sub(r'0x[0-9a-fA-F]+', '<address>', str(exc)))
    row['errors'].append({'stage': stage, 'type': type(exc).__name__, 'message': message})


def _guard_image(img, max_pixels):
    if img.width * img.height > max_pixels:
        raise BudgetExceeded(f'pixel limit {max_pixels} exceeded')


def inspect_bytes(data, suffix, *, max_pixels=20_000_000, max_frames=64):
    """Metadata, structure verification and complete frame decoding are distinct."""
    row = dict(status='unrecognized', format=None, encoded_size=None, reported_size=None,
               display_size=None, orientation=None, orientation_status='missing',
               dates=[], capture=None, frames=None, validated_frames=0,
               metadata_status='not_read', verify_status='not_run', decode_status='not_run',
               warnings=[], errors=[])
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as img:
                row['format'] = img.format
                row['reported_size'] = list(img.size)
                row['encoded_size'] = list(img.size)
                _guard_image(img, max_pixels)
                row['frames'] = getattr(img, 'n_frames', 1)
                try:
                    exif = img.getexif()
                    if img.format == 'TIFF':
                        row['encoded_size'] = [int(img.tag_v2[256]), int(img.tag_v2[257])]
                    orientation = exif.get(274)
                    if orientation is not None:
                        row['orientation'] = orientation if isinstance(orientation, int) else _text(orientation)
                        row['orientation_status'] = 'valid' if isinstance(orientation, int) and 1 <= orientation <= 8 else 'invalid'
                    exif_ifd = exif.get_ifd(34665)
                    groups = [('IFD0', dict(exif)), ('ExifIFD', exif_ifd)]
                    for group, values in groups:
                        for date_tag, offset_tag, sub_tag, name, meaning in DATE_TAGS:
                            if date_tag not in values:
                                continue
                            # DateTime lives in IFD0, its OffsetTime/SubSecTime companions in ExifIFD.
                            companion = exif_ifd if date_tag == 306 and group == 'IFD0' else values
                            parsed = parse_exif_date(values[date_tag], companion.get(offset_tag), companion.get(sub_tag))
                            row['dates'].append(dict(source=f'{group}.{name}', meaning=meaning, **parsed))
                    original = [d for d in row['dates'] if d['meaning'] == 'capture']
                    if original:
                        row['capture'] = original[-1].copy()  # ExifIFD preferred only if no conflict
                        if len({(d['local'], d['utc'], d['status']) for d in original}) > 1:
                            row['capture']['status'] = 'conflict'
                    row['metadata_status'] = 'ok'
                except Exception as exc:
                    row['metadata_status'] = 'error'
                    _error(row, 'metadata', exc)
            row['warnings'].extend(str(w.message) for w in captured)
    except Exception as exc:
        _error(row, 'identify', exc)
        if isinstance(exc, (BudgetExceeded, Image.DecompressionBombError, Image.DecompressionBombWarning)):
            row['status'] = 'resource_limit'
        elif isinstance(exc, UnidentifiedImageError):
            row['status'] = 'unrecognized_image' if suffix.lower() in IMAGE_EXTENSIONS else 'non_image_or_unsupported'
        else:
            row['status'] = 'invalid_image'
        return row

    # getexif() may force PNG load: verify must use an untouched, separately opened object.
    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        row['verify_status'] = 'passed'
    except Exception as exc:
        row['verify_status'] = 'failed'
        _error(row, 'verify', exc)
    try:
        if row['frames'] > max_frames:
            raise BudgetExceeded(f'frame limit {max_frames} exceeded')
        with Image.open(BytesIO(data)) as img:
            total_pixels = 0
            for index in range(row['frames']):
                img.seek(index)
                total_pixels += img.width * img.height
                if total_pixels > max_pixels:
                    raise BudgetExceeded(f'total decoded pixel limit {max_pixels} exceeded')
                img.load()
                if index == 0:
                    # TIFF load already applies its orientation; helper handles current EXIF.
                    with ImageOps.exif_transpose(img) as display:
                        row['display_size'] = list(display.size)
                row['validated_frames'] += 1
        row['decode_status'] = 'passed'
    except Exception as exc:
        row['decode_status'] = 'limited' if isinstance(exc, BudgetExceeded) else 'failed'
        _error(row, 'decode', exc)
    if row['verify_status'] == 'failed' or row['decode_status'] == 'failed':
        row['status'] = 'invalid_image'
    elif row['decode_status'] == 'limited':
        row['status'] = 'resource_limit'
    elif row['metadata_status'] == 'error':
        row['status'] = 'metadata_error'
    else:
        row['status'] = 'ok'
    Image.init()
    extension_format = Image.registered_extensions().get(suffix.lower())
    if extension_format and extension_format != row['format']:
        row['warnings'].append('extension_format_mismatch')
    return row


def _is_link(st):
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, 'st_file_attributes', 0) & 0x400)


def _walk(root):
    """Do not follow symlinks, Windows junctions or other reparse points."""
    with os.scandir(root) as listing:
        entries = sorted(listing, key=lambda entry: entry.name)
    for entry in entries:
        path = Path(entry.path)
        try:
            # DirEntry.stat has zero st_dev/st_ino on Windows; use a fresh lstat.
            st = path.lstat()
            if _is_link(st):
                yield path, st, 'skipped_link'
            elif stat.S_ISDIR(st.st_mode):
                yield from _walk(path)
            elif stat.S_ISREG(st.st_mode):
                yield path, st, None
            else:
                yield path, st, 'skipped_special'
        except OSError:
            yield path, None, 'io_error'


def _stamp(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def scan_directory(root, *, max_file_bytes=16*1024*1024, max_total_bytes=64*1024*1024,
                   max_pixels=20_000_000, max_frames=64):
    original_root = Path(root).absolute()
    if _is_link(original_root.lstat()):
        raise ValueError('input root must not be a symlink or reparse point')
    root = original_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('input root must be a directory')
    records, snapshots, physical = [], {}, {}
    total_bytes = 0
    for path, st, skip in _walk(root):
        name = path.relative_to(root).as_posix()
        row = dict(path=name, size=st.st_size if st else None, sha256=None,
                   filesystem_mtime_ns=st.st_mtime_ns if st else None, status=skip,
                   errors=[], warnings=[])
        records.append(row)
        if skip:
            continue
        identity = (st.st_dev, st.st_ino)
        if st.st_ino and identity in physical:
            row.update(status='same_file_alias', alias_of=physical[identity])
            continue
        if st.st_ino:
            physical[identity] = name
        if st.st_size > max_file_bytes:
            row['status'] = 'file_size_limit'
            continue
        if total_bytes + st.st_size > max_total_bytes:
            row['status'] = 'corpus_size_limit'
            continue
        try:
            with path.open('rb') as stream:
                opened = os.fstat(stream.fileno())
                if _stamp(opened) != _stamp(st):
                    row['status'] = 'changed_during_read'
                    continue
                data = stream.read(max_file_bytes + 1)
                after = os.fstat(stream.fileno())
            if _stamp(opened) != _stamp(after) or _stamp(path.stat()) != _stamp(st) or len(data) != st.st_size:
                row['status'] = 'changed_during_read'
                continue
        except OSError as exc:
            row['status'] = 'io_error'
            _error(row, 'read', exc)
            continue
        total_bytes += len(data)
        row['sha256'] = hashlib.sha256(data).hexdigest()
        snapshots[name] = data
        row.update(inspect_bytes(data, path.suffix, max_pixels=max_pixels, max_frames=max_frames))

    groups = exact_groups(records, snapshots)
    candidates = build_candidates(records, groups)
    return dict(schema_version=1, engine={'name':'Pillow', 'version': PIL.__version__},
                policy={'identity':'size+sha256+byte_comparison', 'date_bucket':'valid DateTimeOriginal local day only',
                        'writes_to_input':False, 'max_file_bytes':max_file_bytes,
                        'max_total_bytes':max_total_bytes, 'max_pixels':max_pixels, 'max_frames':max_frames},
                summary={'files':len(records), 'statuses':dict(sorted(Counter(r['status'] for r in records).items())),
                         'exact_groups':len(groups), 'snapshot_bytes':total_bytes},
                records=records, exact_groups=groups, candidates=candidates)


def exact_groups(records, snapshots):
    buckets = defaultdict(list)
    for row in records:
        if row.get('sha256') and row['path'] in snapshots:
            buckets[(row['size'], row['sha256'])].append(row['path'])
    result = []
    for (size, digest), names in sorted(buckets.items()):
        partitions = []
        for name in sorted(names):
            for partition in partitions:
                if snapshots[name] == snapshots[partition[0]]:
                    partition.append(name)
                    break
            else:
                partitions.append([name])
        for partition in partitions:
            if len(partition) > 1:
                result.append(dict(id=f'exact-{len(result)+1:03d}', sha256=digest, size=size,
                                   evidence='sha256_and_equal_bytes', members=partition))
    return result


def build_candidates(records, groups):
    membership = {name:g['id'] for g in groups for name in g['members']}
    output = []
    for row in records:
        reasons = []
        bucket = None
        capture = row.get('capture')
        if row['status'] != 'ok':
            reasons.append(row['status'])
        if row.get('format'):
            if not capture:
                reasons.append('capture_date_missing')
            elif capture['status'] in ('offset_known', 'timezone_unknown'):
                if row['status'] == 'ok':
                    bucket = capture['local'][:10]
                if capture['status'] == 'timezone_unknown':
                    reasons.append('capture_timezone_unknown')
            else:
                reasons.append('capture_' + capture['status'])
            if capture:
                reasons.extend(capture['warnings'])
            if row.get('orientation_status') in ('missing','invalid'):
                reasons.append('orientation_' + row['orientation_status'])
            if row.get('orientation') in range(2,9):
                reasons.append('orientation_transform_for_display')
        group = membership.get(row['path'])
        if group:
            reasons.append('exact_byte_duplicate')
        reasons.extend(row.get('warnings', []))
        output.append(dict(path=row['path'], date_bucket=bucket, date_source=capture['source'] if capture else None,
                           exact_group=group, review_reasons=reasons, action='review_only'))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_directory', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = args.input_directory.resolve(strict=True)
    destination = args.output.resolve()
    if destination == source or source in destination.parents:
        parser.error('--output must be outside the input directory')
    result = scan_directory(args.input_directory)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation avoids silently overwriting any pre-existing input or artifact.
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result['summary'], ensure_ascii=True))


if __name__ == '__main__':
    main()
