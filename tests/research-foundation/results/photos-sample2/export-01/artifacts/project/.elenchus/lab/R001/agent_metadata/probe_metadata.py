"""Read-only input probe; all generated data and reports stay beside this file."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import logging
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import exifread
from PIL import Image, ImageOps

WORK = Path(__file__).resolve().parent
TAGS = {274: "Orientation", 306: "DateTime", 36867: "DateTimeOriginal", 36868: "DateTimeDigitized", 36880: "OffsetTime", 36881: "OffsetTimeOriginal", 36882: "OffsetTimeDigitized"}


def hashes(root: Path):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def pillow_probe(path: Path):
    result = {}
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        try:
            with Image.open(path) as im:
                result.update(format=im.format, size=list(im.size), frames=getattr(im, "n_frames", 1))
                exif = im.getexif()
                result["ifd0"] = {TAGS[t]: exif[t] for t in TAGS if t in exif}
                nested = exif.get_ifd(0x8769)
                result["exif_ifd"] = {TAGS[t]: nested[t] for t in TAGS if t in nested}
                result["metadata_status"] = "read"
        except Exception as exc:
            result.update(metadata_status="error", metadata_error=f"{type(exc).__name__}: {exc}")
        for step in ("verify", "load"):
            try:
                with Image.open(path) as im:
                    getattr(im, step)()
                result[step] = "ok"
            except Exception as exc:
                result[step] = f"{type(exc).__name__}: {exc}"
        result["warnings"] = [str(w.message) for w in observed]
    return result


class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []
    def emit(self, record):
        self.lines.append(record.getMessage())


def exifread_probe(path: Path, strict: bool):
    capture = Capture()
    logger = logging.getLogger("exifread")
    logger.addHandler(capture)
    try:
        with path.open("rb") as stream:
            tags = exifread.process_file(stream, details=False, strict=strict)
        result = {"status": "returned", "tag_count": len(tags),
                  "fields": {k: str(v) for k, v in tags.items()
                             if any(token in k for token in ("Date", "Time", "Orientation"))}}
    except Exception as exc:
        result = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    finally:
        logger.removeHandler(capture)
    result["messages"] = capture.lines
    return result


def make_variants(inputs: Path):
    variants = WORK / "fixtures"
    variants.mkdir(exist_ok=True)
    dated = inputs / "session A" / "dated.jpg"
    original = dated.read_bytes()
    (variants / "jpeg_with_png_extension.png").write_bytes(original)
    (variants / "metadata_survives_truncated_pixels.jpg").write_bytes(original[:-20])
    for suffix, date in (("png", "2020:02:03 04:05:06"), ("jpg", "2020:02:03 04:05:06"), ("tiff", "2020:02:03 04:05:06"), ("png", "2020:99:99 99:99:99")):
        exif = Image.Exif()
        exif[274] = 6
        exif[0x8769] = {36867: date, 36881: "+09:00"}
        stem = "invalid_date" if "99" in date else "nested_date"
        with Image.new("RGB", (12, 8), (42, 84, 126)) as im:
            im.save(variants / f"{stem}.{suffix}", exif=exif.tobytes())
    return variants


def orientation_probe(path: Path):
    def state(im):
        exif = im.getexif()
        return {"size": list(im.size), "orientation": exif.get(274),
                "ifd_width": exif.get(256), "ifd_height": exif.get(257)}
    result = {}
    with Image.open(path) as im:
        result["after_open"] = state(im)
        im.load()
        result["after_load"] = state(im)
        result["loaded_pixels_sha256"] = hashlib.sha256(im.tobytes()).hexdigest()
        with ImageOps.exif_transpose(im) as transposed:
            result["transpose_after_load"] = state(transposed)
            result["transposed_pixels_sha256"] = hashlib.sha256(transposed.tobytes()).hexdigest()
    with Image.open(path) as im:
        with ImageOps.exif_transpose(im) as transposed:
            result["transpose_direct"] = state(transposed)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    inputs = args.inputs.resolve()
    before = hashes(inputs)
    variants = make_variants(inputs)
    rows = []
    for group, root in (("provided", inputs), ("injected", variants)):
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rows.append({"origin": group, "path": path.relative_to(root).as_posix(),
                         "bytes": path.stat().st_size, "pillow": pillow_probe(path),
                         "exifread": exifread_probe(path, False),
                         "exifread_strict": exifread_probe(path, True)})
    orientations = {path.relative_to(inputs).as_posix(): orientation_probe(path)
                    for path in (inputs / "formats" / "sample.tiff", inputs / "회전" / "rotated.jpg")}
    after = hashes(inputs)
    report = {"time_utc": datetime.now(timezone.utc).isoformat(),
              "question": "Dates, orientation, format and corrupt-input behavior for synthetic JPEG/PNG/TIFF",
              "versions": {"Python": sys.version.split()[0], "Pillow": importlib.metadata.version("Pillow"),
                           "ExifRead": importlib.metadata.version("ExifRead")},
              "inputs": str(inputs), "input_hashes_before": before, "input_hashes_after": after,
              "inputs_unchanged": before == after, "results": rows,
              "orientation": orientations}
    (WORK / "probe_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"versions": report["versions"], "inputs_unchanged": report["inputs_unchanged"],
                      "results": rows, "orientation": report["orientation"]}, ensure_ascii=True, default=str))
    if before != after:
        raise RuntimeError("Input hashes changed")


if __name__ == "__main__":
    main()
