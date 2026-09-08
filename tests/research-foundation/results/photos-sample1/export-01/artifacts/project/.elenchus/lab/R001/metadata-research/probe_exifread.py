"""Read scoped synthetic inputs with ExifRead; never write to source images."""
from __future__ import annotations

import hashlib
import io
import json
import logging
from pathlib import Path
import sys
from datetime import datetime, timezone

LAB = Path(__file__).resolve().parent
PROJECT = LAB.parents[3]
INPUTS = PROJECT / "inputs"
sys.dont_write_bytecode = True
sys.path.insert(0, str(LAB / "deps"))
import exifread


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(f"{record.levelname}: {record.getMessage()}")


def inspect(data: bytes, strict: bool) -> dict:
    handler = Capture()
    logger = logging.getLogger("exifread")
    logger.addHandler(handler)
    try:
        # ExifRead receives an in-memory copy, not a writable source handle.
        tags = exifread.process_file(
            io.BytesIO(data), details=False, extract_thumbnail=False, strict=strict
        )
        values = {}
        for name, tag in tags.items():
            values[name] = {
                "display": str(tag),
                "raw": getattr(tag, "values", None),
            }
        return {"returned": "tags" if tags else "empty", "tags": values,
                "warnings": handler.messages}
    except Exception as error:
        return {"returned": "exception", "exception_type": type(error).__name__,
                "message": str(error), "warnings": handler.messages}
    finally:
        logger.removeHandler(handler)


def main():
    manifest = json.loads((PROJECT / "inputs.sha256.json").read_text(encoding="utf-8-sig"))
    results = []
    before = {}
    for relative, expected in sorted(manifest.items()):
        source = (INPUTS / relative).resolve()
        if not source.is_relative_to(INPUTS.resolve()):
            raise ValueError("Input path leaves the scoped inputs directory")
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        before[relative] = digest
        if digest != expected:
            raise ValueError(f"Baseline hash mismatch: {relative}")
        results.append({"path": relative, "bytes": len(data), "sha256": digest,
                        "strict_false": inspect(data, False),
                        "strict_true": inspect(data, True)})
    after = {name: hashlib.sha256((INPUTS / name).read_bytes()).hexdigest()
             for name in before}
    report = {"time_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version, "exifread_version": exifread.__version__,
              "parser_input": "BytesIO copy; original files opened for reading only",
              "baseline_match": before == manifest, "input_hashes_unchanged": before == after,
              "results": results}
    (LAB / "probe-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if not report["input_hashes_unchanged"]:
        raise RuntimeError("Input hashes changed")


if __name__ == "__main__":
    main()
