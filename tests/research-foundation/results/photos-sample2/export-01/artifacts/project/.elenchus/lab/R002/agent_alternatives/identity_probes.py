"""Read-only input inspection and isolated, deliberately injected counterexamples.

Run with the local venv interpreter and -I -B. No original is modified or linked.
Writes only a new run directory under this file's directory and the assigned log.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone

import PIL
from PIL import Image, ImageOps, PngImagePlugin

LAB = Path(__file__).resolve().parent
PROJECT = LAB.parents[3]
INPUTS = PROJECT / "inputs"
RECORD = PROJECT.parent / "records" / "agent_alternatives.jsonl"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN = LAB / ("run_" + STAMP)
RUN.mkdir()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(root):
    return {str(p.relative_to(root)).replace("\\", "/"): {
        "sha256": sha(p), "size": p.stat().st_size,
        "mtime_ns": p.stat().st_mtime_ns,
    } for p in sorted(root.rglob("*")) if p.is_file()}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def date_evidence(value, offset=None):
    """Keep wall time unzoned unless a valid explicit offset exists."""
    if value is None:
        return {"status": "missing", "raw": None, "utc": None}
    try:
        if not re.fullmatch(r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", str(value)):
            raise ValueError("unexpected format")
        parsed = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return {"status": "invalid", "raw": value, "utc": None}
    result = {"raw": value, "wall_time": parsed.isoformat(), "raw_offset": offset,
              "status": "valid_wall_time_unknown_zone", "utc": None}
    if offset is None:
        return result
    if not re.fullmatch(r"[+-](0\d|1[0-4]):[0-5]\d", str(offset)):
        result["status"] = "invalid_offset"
        return result
    hours, minutes = map(int, str(offset)[1:].split(":"))
    if hours == 14 and minutes != 0:
        result["status"] = "invalid_offset"
        return result
    delta = timedelta(hours=hours, minutes=minutes)
    if str(offset)[0] == "-":
        delta = -delta
    result.update(status="explicit_offset", utc=parsed.replace(
        tzinfo=timezone(delta)).astimezone(timezone.utc).isoformat())
    return result


def image_evidence(path):
    row = {"path": str(path), "byte_sha256": sha(path)}
    try:
        with Image.open(path) as im:
            im.load()
            exif = im.getexif()
            exif_ifd = exif.get_ifd(34665) if 34665 in exif else {}
            original = exif_ifd.get(36867, exif.get(36867))
            offset = exif_ifd.get(36881, exif.get(36881))
            row.update(format=im.format, mode=im.mode, size=im.size,
                       frames=getattr(im, "n_frames", 1), orientation=exif.get(274),
                       datetime_original=date_evidence(original, offset))
            row["decode"] = "success"
    except Exception as exc:
        row.update(decode="failure", error_type=type(exc).__name__, error=str(exc))
    return row


def pixel_key(path, normalize_orientation=False, all_frames=False):
    """Explicit experimental contract: 8-bit RGBA; no ICC conversion."""
    with Image.open(path) as im:
        keys = []
        count = getattr(im, "n_frames", 1) if all_frames else 1
        for i in range(count):
            im.seek(i)
            frame = ImageOps.exif_transpose(im) if normalize_orientation else im.copy()
            frame = frame.convert("RGBA")
            keys.append((frame.size, frame.tobytes()))
        return tuple(keys)


def ahash(path):
    # Independent small implementation of the published luminance-average method.
    with Image.open(path) as im:
        values = list(im.convert("L").resize((8, 8), Image.Resampling.LANCZOS).getdata())
    total = sum(values)
    bits = 0
    for value in values:
        bits = (bits << 1) | (value * 64 > total)
    return bits


def pair(a, b):
    return {"a": str(a.relative_to(RUN)), "b": str(b.relative_to(RUN)),
            "bytes_equal": a.read_bytes() == b.read_bytes(),
            "sha256_equal": sha(a) == sha(b),
            "raw_first_frame_rgba_equal": pixel_key(a) == pixel_key(b),
            "oriented_first_frame_rgba_equal": pixel_key(a, True) == pixel_key(b, True),
            "all_raw_frames_rgba_equal": pixel_key(a, all_frames=True) == pixel_key(b, all_frames=True),
            "ahash_hamming_distance": (ahash(a) ^ ahash(b)).bit_count()}


before = manifest(INPUTS)
write_json(RUN / "input_manifest_before.json", before)
copied = RUN / "input_copies"
shutil.copytree(INPUTS, copied, copy_function=shutil.copyfile)
observations = [image_evidence(p) for p in sorted(copied.rglob("*")) if p.is_file()]
write_json(RUN / "input_observations.json", observations)

fixtures = RUN / "generated"
fixtures.mkdir()
pattern = Image.new("RGB", (32, 20))
pattern.putdata([((x * 31 + y * 7) % 256, (x * 3 + y * 41) % 256,
                  (x * 11 + y * 17) % 256) for y in range(20) for x in range(32)])
plain = fixtures / "pattern.png"
pattern.save(plain)
metadata = fixtures / "pattern_metadata.png"
pnginfo = PngImagePlugin.PngInfo()
pnginfo.add_text("Description", "Synthetic metadata-only change")
pattern.save(metadata, pnginfo=pnginfo)

orientation = Image.Exif()
orientation[274] = 6
tag_rotated = fixtures / "tag_orientation6.png"
pattern.save(tag_rotated, exif=orientation)
physical_rotated = fixtures / "physically_rotated.png"
pattern.transpose(Image.Transpose.ROTATE_270).save(physical_rotated)

red = fixtures / "solid_red.png"
blue = fixtures / "solid_blue.png"
Image.new("RGB", (32, 20), "red").save(red)
Image.new("RGB", (32, 20), "blue").save(blue)

jpeg = fixtures / "pattern_q95.jpg"
reencoded = fixtures / "pattern_q65.jpg"
pattern.save(jpeg, quality=95)
with Image.open(jpeg) as im:
    im.save(reencoded, quality=65)

multi_a = fixtures / "two_frames_a.tiff"
multi_b = fixtures / "two_frames_b.tiff"
pattern.save(multi_a, save_all=True, append_images=[Image.new("RGB", pattern.size, "red")])
pattern.save(multi_b, save_all=True, append_images=[Image.new("RGB", pattern.size, "blue")])

cases = {"metadata_only": pair(plain, metadata),
         "orientation_equivalent": pair(tag_rotated, physical_rotated),
         "perceptual_false_positive": pair(red, blue),
         "jpeg_reencode": pair(jpeg, reencoded),
         "first_frame_false_positive": pair(multi_a, multi_b)}

# A real TIFF/PNG header can open successfully while later decode fails.
truncated = fixtures / "lazy_decode_truncated.png"
truncated.write_bytes(plain.read_bytes()[:60])
lazy_result = {}
try:
    with Image.open(truncated) as im:
        lazy_result["open"] = "success"
        try:
            im.load()
            lazy_result["load"] = "success"
        except Exception as exc:
            lazy_result.update(load="failure", error_type=type(exc).__name__, error=str(exc))
except Exception as exc:
    lazy_result.update(open="failure", error_type=type(exc).__name__, error=str(exc))

# Similarity within a threshold is not transitive: generate actual 8x8 images.
chain = []
for count in range(3):
    im = Image.new("L", (8, 8), 0)
    for j in range(count):
        im.putpixel((7-j, 7), 255)
    path = fixtures / f"chain_{count}.png"
    im.save(path)
    chain.append(path)
distances = {f"{i}-{j}": (ahash(a)^ahash(b)).bit_count()
             for (i,a),(j,b) in itertools.combinations(enumerate(chain), 2)}

# Read/write races are deliberately injected only into newly generated files.
fsdir = RUN / "filesystem"
fsdir.mkdir()
mutable = fsdir / "mutable.bin"
mutable.write_bytes(b"AAAA")
old_stat = mutable.stat()
old_hash = sha(mutable)
mutable.write_bytes(b"BBBB")
os.utime(mutable, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
new_stat = mutable.stat()
cache_probe = {"same_inode": old_stat.st_ino == new_stat.st_ino,
               "same_size": old_stat.st_size == new_stat.st_size,
               "same_mtime_ns": old_stat.st_mtime_ns == new_stat.st_mtime_ns,
               "same_ctime_ns": old_stat.st_ctime_ns == new_stat.st_ctime_ns,
               "hash_changed": old_hash != sha(mutable),
               "kind": "injected_same_size_content_mutation_and_timestamp_restore"}

alias = fsdir / "hardlink_alias.bin"
try:
    os.link(mutable, alias)
    hardlink_probe = {"status": "success", "samefile": os.path.samefile(mutable, alias),
                      "nlink": mutable.stat().st_nlink, "same_inode": mutable.stat().st_ino == alias.stat().st_ino}
    alias.write_bytes(b"CCCC")
    hardlink_probe["alias_edit_visible_through_first_path"] = mutable.read_bytes() == b"CCCC"
except OSError as exc:
    hardlink_probe = {"status": "unavailable", "error": str(exc)}

dates = [date_evidence(None), date_evidence("2024:02:30 12:00:00"),
         date_evidence("2024:01:01 00:30:00"),
         date_evidence("2024:01:01 00:30:00", "+09:00"),
         date_evidence("2024:01:01 00:30:00", "-08:00"),
         date_evidence("2024:01:01 00:30:00", "+99:99")]

# Synthetic colliding prefilter, not a collision of SHA-256.
collision_guard = {"kind": "injected_constant_digest_prefilter", "a": "AAAA", "b": "BBBB",
                   "prefilter_equal": True, "byte_comparison_equal": b"AAAA" == b"BBBB"}
checks = {
    "metadata_does_not_imply_different_pixels": not cases["metadata_only"]["bytes_equal"] and cases["metadata_only"]["raw_first_frame_rgba_equal"],
    "orientation_changes_pixel_identity_contract": not cases["orientation_equivalent"]["raw_first_frame_rgba_equal"] and cases["orientation_equivalent"]["oriented_first_frame_rgba_equal"],
    "zero_ahash_distance_is_not_pixel_equality": cases["perceptual_false_positive"]["ahash_hamming_distance"] == 0 and not cases["perceptual_false_positive"]["raw_first_frame_rgba_equal"],
    "first_frame_is_not_whole_image": cases["first_frame_false_positive"]["raw_first_frame_rgba_equal"] and not cases["first_frame_false_positive"]["all_raw_frames_rgba_equal"],
    "threshold_relation_is_not_transitive": distances == {"0-1": 1, "0-2": 2, "1-2": 1},
    "size_mtime_inode_cache_can_miss_mutation": all(cache_probe[k] for k in ("same_inode", "same_size", "same_mtime_ns", "hash_changed")),
    "unknown_date_stays_unknown": dates[0]["status"] == "missing" and dates[2]["utc"] is None,
    "invalid_date_rejected": dates[1]["status"] == "invalid" and dates[5]["status"] == "invalid_offset",
    "byte_compare_rejects_injected_hash_prefilter_collision": not collision_guard["byte_comparison_equal"],
}
after = manifest(INPUTS)
write_json(RUN / "input_manifest_after.json", after)
checks["input_content_size_mtime_unchanged"] = before == after
result = {"time": datetime.now(timezone.utc).isoformat(),
          "environment": {"python": sys.version, "pillow": PIL.__version__, "platform": platform.platform()},
          "input_file_count": len(before), "input_preserved": before == after,
          "synthetic_pairs": cases, "truncated_lazy_decode": lazy_result,
          "similarity_chain_hamming_distances": distances,
          "cache_probe": cache_probe, "hardlink_probe": hardlink_probe,
          "synthetic_date_cases": dates, "synthetic_digest_collision": collision_guard,
          "checks": checks, "all_checks_passed": all(checks.values()),
          "unverified": ["ICC/HDR/16-bit rendering equality", "HEIC/RAW", "real-photo similarity thresholds",
                         "large corpus performance", "network filesystem semantics", "symbolic link/junction traversal",
                         "concurrent mutation safety guarantee", "real SHA-256 collision", "Restic/fdupes executable integration"]}
write_json(RUN / "results.json", result)
RECORD.parent.mkdir(parents=True, exist_ok=True)
with RECORD.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"time": result["time"], "question": "동일성 정의와 파일시스템·날짜 추정의 반례는 무엇인가?",
                        "url": [], "command": "local .venv/Scripts/python.exe -I -B identity_probes.py",
                        "result": {"all_checks_passed": result["all_checks_passed"], "checks": checks,
                                   "hardlink": hardlink_probe, "lazy_decode": lazy_result},
                        "path": str(RUN / "results.json")}, ensure_ascii=False) + "\n")
print(json.dumps({"path": str(RUN / "results.json"), "checks": checks,
                  "hardlink": hardlink_probe, "lazy_decode": lazy_result}, ensure_ascii=False, indent=2))
sys.exit(0 if all(checks.values()) else 1)
