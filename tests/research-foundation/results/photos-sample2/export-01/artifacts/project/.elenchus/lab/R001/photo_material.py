"""Read-only photo research material. No rename/move/delete implementation.

The bounded in-memory snapshot is shared by hashing and decoding. This is a
small-corpus experiment, not a bulk ingest engine or an atomic filesystem scan.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError, __version__ as pillow_version

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_FRAMES = 32
MAX_FILES = 10000
SUPPORTED = {"JPEG", "PNG", "TIFF"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".heif", ".raw", ".cr2", ".nef", ".dng", ".webp", ".gif"}
DATE_TAGS = {36867: ("DateTimeOriginal", 36881, 37521),
             36868: ("DateTimeDigitized", 36882, 37522),
             306: ("DateTime", 36880, 37520)}
DATE_RE = re.compile(r"[0-9]{4}:[0-9]{2}:[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\Z")


def error_message(error):
    # Memory addresses in BytesIO errors are incidental and break rerun diffs.
    return re.sub(r"0x[0-9A-Fa-f]+", "<address>", str(error))


def text_value(value):
    if isinstance(value, bytes):
        return value.decode("ascii", errors="replace").rstrip("\x00 ")
    return str(value).rstrip("\x00 ")


def parse_date(raw, offset=None, subsecond=None):
    result = {"raw": text_value(raw), "offset_raw": None if offset is None else text_value(offset),
              "subsecond_raw": None if subsecond is None else text_value(subsecond),
              "status": "invalid", "local": None, "utc": None, "timezone": "unknown", "issues": []}
    try:
        if not DATE_RE.fullmatch(result["raw"]):
            raise ValueError("invalid EXIF date syntax")
        date = datetime.strptime(result["raw"], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        result["issues"].append("invalid_date")
        return result
    result["status"] = "valid"
    fraction = result["subsecond_raw"]
    if fraction:
        if re.fullmatch(r"[0-9]{1,6}", fraction):
            date = date.replace(microsecond=int(fraction.ljust(6, "0")))
        else:
            result["issues"].append("invalid_or_unsupported_subsecond")
    result["local"] = date.isoformat()
    zone = result["offset_raw"]
    if zone:
        match = re.fullmatch(r"([+-])([0-9]{2}):([0-9]{2})", zone)
        if not match or int(match[2]) > 23 or int(match[3]) > 59:
            result["issues"].append("invalid_offset")
        elif zone == "-00:00":
            result["issues"].append("offset_negative_zero_ambiguous")
        else:
            minutes = (int(match[2]) * 60 + int(match[3])) * (1 if match[1] == "+" else -1)
            try:
                aware = date.replace(tzinfo=timezone(timedelta(minutes=minutes)))
                result["utc"] = aware.astimezone(timezone.utc).isoformat()
                result["timezone"] = "explicit_offset"
            except (OverflowError, ValueError):
                result["issues"].append("utc_conversion_out_of_range")
    return result


def extract_metadata(image):
    exif = image.getexif()
    groups = {"IFD0": dict(exif)}
    if 34665 in exif:
        groups["ExifIFD"] = dict(exif.get_ifd(34665))
    dates = []
    for group, values in groups.items():
        for tag, (name, offset, subsec) in DATE_TAGS.items():
            if tag in values:
                companions = groups.get("ExifIFD", {}) if group == "IFD0" and tag == 306 else values
                dates.append({"tag": name, "source": f"{group}:{name}",
                              **parse_date(values[tag], companions.get(offset), companions.get(subsec))})
    originals = [date for date in dates if date["tag"] == "DateTimeOriginal"]
    usable = [date for date in originals if date["status"] == "valid"]
    # Do not turn ambiguous/conflicting duplicates of a capture tag into a fact.
    conflict = len({(date["local"], date["offset_raw"], tuple(date["issues"])) for date in usable}) > 1
    selected = usable[0].copy() if usable and len(usable) == len(originals) and not conflict else None
    orientation = exif.get(274)
    if orientation is not None:
        try:
            orientation = int(orientation)
        except (TypeError, ValueError):
            orientation = text_value(orientation)
    if image.format == "TIFF" and 256 in exif and 257 in exif:
        stored_size = [int(exif[256]), int(exif[257])]
    else:
        stored_size = list(image.size)
    return {"dates": dates, "capture_date": selected, "capture_conflict": conflict,
            "orientation": orientation, "stored_size": stored_size}


def analyze_bytes(data: bytes, name: str):
    result = {"format": None, "status": "unidentified", "decode_status": "not_attempted",
              "verify_status": "not_attempted", "warnings": [], "errors": [],
              "dates": [], "capture_date": None, "capture_conflict": False,
              "orientation": None, "stored_size": None, "display_size": None,
              "frame_count": None, "decoded_frames": 0, "metadata_status": "not_attempted"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(data)) as image:
                result["format"] = image.format
                result["header_size"] = list(image.size)
                if image.format not in SUPPORTED:
                    result["status"] = "unsupported_format"
                    return result
                result["status"] = "identified"
                try:
                    result.update(extract_metadata(image))
                    result["metadata_status"] = "passed"
                except Exception as error:
                    result["metadata_status"] = "failed"
                    result["errors"].append({"stage": "metadata", "type": type(error).__name__, "message": error_message(error)})
                count = getattr(image, "n_frames", 1)
                result["frame_count"] = count
                if count > MAX_FRAMES:
                    result["status"] = "resource_limit"
                    result["errors"].append({"stage": "decode", "type": "FrameLimit", "message": str(count)})
                    return result
            # verify can pass an incomplete JPEG; full decoding is separate.
            try:
                with Image.open(io.BytesIO(data)) as image:
                    image.verify()
                result["verify_status"] = "passed"
            except Exception as error:
                result["verify_status"] = "failed"
                result["errors"].append({"stage": "verify", "type": type(error).__name__, "message": error_message(error)})
            try:
                pixels = 0
                with Image.open(io.BytesIO(data)) as image:
                    for index in range(count):
                        image.seek(index)
                        pixels += image.width * image.height
                        if pixels > MAX_PIXELS:
                            raise ValueError("decoded pixel budget exceeded")
                        image.load()
                        if index == 0:
                            # TIFF's decoder already applies its orientation; ImageOps
                            # reads the post-load EXIF, avoiding a second transpose.
                            corrected = ImageOps.exif_transpose(image)
                            result["display_size"] = list(corrected.size)
                            result["display_rgba_sha256"] = hashlib.sha256(
                                str(corrected.size).encode("ascii") + corrected.convert("RGBA").tobytes()).hexdigest()
                            corrected.close()
                        result["decoded_frames"] += 1
                result["decode_status"] = "passed"
            except Exception as error:
                result["decode_status"] = "failed"
                result["errors"].append({"stage": "decode", "type": type(error).__name__, "message": error_message(error)})
            result["status"] = "ok" if result["decode_status"] == "passed" and result["verify_status"] == "passed" else "damaged"
        except UnidentifiedImageError as error:
            result["status"] = "unidentified_image" if Path(name).suffix.lower() in IMAGE_EXTENSIONS else "not_image_or_unknown"
            result["errors"].append({"stage": "open", "type": type(error).__name__, "message": error_message(error)})
        except Exception as error:
            result["status"] = "damaged_or_unreadable"
            result["errors"].append({"stage": "open", "type": type(error).__name__, "message": error_message(error)})
        finally:
            result["warnings"] = [str(warning.message) for warning in caught]
    if result["orientation"] is not None and result["orientation"] not in range(1, 9):
        result["warnings"].append("invalid_orientation")
    expected = {"JPEG": {".jpg", ".jpeg"}, "PNG": {".png"}, "TIFF": {".tif", ".tiff"}}
    if result["format"] in expected and Path(name).suffix.lower() not in expected[result["format"]]:
        result["warnings"].append("extension_format_mismatch")
    return result


def signature(info):
    # Windows Python 3.12 can expose different ctime meanings from stat/fstat.
    # Cross-API comparisons use common identity, length and content mtime only.
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def mutation_signature(info):
    # ctime is still useful when comparing the SAME API before and after read.
    return (*signature(info), info.st_ctime_ns)


def blocked_link(path: Path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def snapshot_file(path: Path, limit=MAX_FILE_BYTES):
    if blocked_link(path):
        raise ValueError("links are excluded")
    before = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("not a regular file")
    if before.st_size > limit:
        raise ValueError("file byte budget exceeded")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if signature(opened) != signature(before):
            raise ValueError("file changed before read")
        data = stream.read(limit + 1)
        after_handle = os.fstat(stream.fileno())
    after = path.stat(follow_symlinks=False)
    if (len(data) != before.st_size or len(data) > limit
            or mutation_signature(after) != mutation_signature(before)
            or mutation_signature(after_handle) != mutation_signature(opened)):
        raise ValueError("file changed during read or byte budget exceeded")
    return data, before


def exact_groups(records, blobs):
    buckets = defaultdict(list)
    for record in records:
        if record.get("sha256"):
            buckets[(record["size"], record["sha256"])].append(record)
    groups = []
    for (_, digest), bucket in sorted(buckets.items()):
        partitions = []
        for record in bucket:
            for partition in partitions:
                if blobs[record["path"]] == blobs[partition[0]["path"]]:
                    partition.append(record)
                    break
            else:
                partitions.append([record])
        for partition in partitions:
            if len(partition) > 1:
                groups.append({"sha256": digest, "paths": [record["path"] for record in partition],
                               "evidence": "same_size_sha256_and_snapshot_bytes",
                               "unique_file_objects": len({tuple(record["file_identity"]) for record in partition})})
    return groups


def make_candidates(records, duplicates):
    candidates = [{"kind": "exact_duplicate_review", "paths": group["paths"], "sha256": group["sha256"],
                   "reason": group["evidence"], "unique_file_objects": group["unique_file_objects"]} for group in duplicates]
    for record in records:
        path = record["path"]
        if record.get("status") != "ok":
            candidates.append({"kind": "input_review", "path": path, "reason": record.get("status")})
            continue
        reasons = list(record["warnings"])
        if record["metadata_status"] == "failed":
            reasons.append("metadata_read_failed")
        capture = record["capture_date"]
        if record["capture_conflict"]:
            reasons.append("conflicting_capture_dates")
        elif capture is None:
            reasons.append("no_valid_capture_date")
        else:
            if capture["timezone"] == "unknown":
                reasons.append("capture_timezone_unknown")
            reasons += capture["issues"]
            candidates.append({"kind": "date_bucket_candidate", "path": path,
                               "bucket": capture["local"][:10].replace("-", "/"),
                               "basis": capture["source"], "calendar_basis": "recorded_local_date",
                               "timezone": capture["timezone"], "sha256": record["sha256"]})
        for date in record["dates"]:
            if date["status"] == "invalid":
                reasons.append("invalid_date:" + date["source"])
        if record["frame_count"] > 1:
            reasons.append("multiple_frames")
        if reasons:
            candidates.append({"kind": "metadata_review", "path": path, "reasons": sorted(set(reasons))})
    return candidates


def scan(root: Path):
    root = Path(root)
    if blocked_link(root):
        raise ValueError("input root must not be a link")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("input root must be a directory")
    records, blobs = [], {}
    total_bytes = 0
    errors = []
    def walk_error(error):
        errors.append({"stage": "enumerate", "type": type(error).__name__, "message": str(error)})
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        dirs.sort()
        for name in list(dirs):
            child = Path(directory) / name
            if blocked_link(child):
                dirs.remove(name)
                records.append({"path": child.relative_to(root).as_posix(), "status": "skipped_link"})
        for name in sorted(names):
            path = Path(directory) / name
            record = {"path": path.relative_to(root).as_posix()}
            if len(records) >= MAX_FILES:
                raise ValueError("file count budget exceeded")
            try:
                data, info = snapshot_file(path, min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - total_bytes))
                total_bytes += len(data)
                record.update({"size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                               "file_identity": [info.st_dev, info.st_ino],
                               "filesystem_mtime_ns": info.st_mtime_ns,
                               "filesystem_time_is_capture_date": False})
                record.update(analyze_bytes(data, record["path"]))
                blobs[record["path"]] = data
            except Exception as error:
                record.update({"status": "read_error", "errors": [{"stage": "snapshot", "type": type(error).__name__, "message": str(error)}]})
            records.append(record)
    records.sort(key=lambda record: record["path"])
    duplicates = exact_groups(records, blobs)
    return {"schema": "photo-research-v1", "read_only": True, "pillow_version": pillow_version,
            "scope": "JPEG PNG TIFF; snapshots are not an atomic filesystem view",
            "limits": {"file_bytes": MAX_FILE_BYTES, "total_bytes": MAX_TOTAL_BYTES,
                       "pixels_per_file": MAX_PIXELS, "frames_per_file": MAX_FRAMES},
            "files": records, "scan_errors": errors, "exact_duplicates": duplicates,
            "candidates": make_candidates(records, duplicates)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    input_root = args.input.resolve(strict=True)
    lab_root = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    if not output.is_relative_to(lab_root) or output.is_relative_to(input_root):
        parser.error("output must be outside input and inside the research lab")
    if output.exists():
        parser.error("output exists; choose a new output file")
    report = scan(args.input)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation avoids overwriting an existing result or input alias.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"files": len(report["files"]), "exact_groups": len(report["exact_duplicates"]),
                      "candidates": len(report["candidates"]), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
