import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from PIL import Image

import photo_material as material
from generate_fixtures import COLORS, build

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
INPUTS = PROJECT / "inputs"
FIXTURES = HERE / "fixtures"


class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURES.exists():
            build()
        cls.original = material.scan(INPUTS)
        cls.files = {record["path"]: record for record in cls.original["files"]}

    def fixture(self, name):
        return material.analyze_bytes((FIXTURES / name).read_bytes(), name)

    def test_originals_match_manifest_and_baseline(self):
        expected = json.loads((PROJECT / "inputs.sha256.json").read_text(encoding="utf-8-sig"))
        actual = {p.relative_to(INPUTS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in INPUTS.rglob("*") if p.is_file()}
        self.assertEqual(expected, actual)
        baseline = json.loads((HERE / "baseline.json").read_text())
        self.assertEqual(baseline["inputs"], actual)
        for name in ("existing-product.txt", "inputs.sha256.json"):
            self.assertEqual(baseline[name], hashlib.sha256((PROJECT / name).read_bytes()).hexdigest())

    def test_original_coverage_and_exact_group(self):
        self.assertEqual(len(self.files), 8)
        self.assertEqual(sum(record["status"] == "ok" for record in self.files.values()), 5)
        self.assertEqual(self.original["exact_duplicates"][0]["paths"], ["copies/duplicate.jpg", "session A/dated.jpg"])
        self.assertEqual(len(self.original["exact_duplicates"]), 1)

    def test_original_date_provenance(self):
        date = self.files["session A/dated.jpg"]["capture_date"]
        self.assertEqual(date["source"], "ExifIFD:DateTimeOriginal")
        self.assertEqual(date["utc"], "2024-07-15T01:20:30+00:00")
        self.assertIsNone(self.files["formats/sample.tiff"]["capture_date"])
        self.assertEqual(self.files["formats/sample.tiff"]["dates"][0]["tag"], "DateTime")
        self.assertIsNone(self.files["plain.png"]["capture_date"])

    def test_tiff_and_jpeg_orientation(self):
        for name, orientation in [("formats/sample.tiff", 8), ("회전/rotated.jpg", 6)]:
            with self.subTest(name=name):
                self.assertEqual(self.files[name]["stored_size"], [8, 6])
                self.assertEqual(self.files[name]["display_size"], [6, 8])
                self.assertEqual(self.files[name]["orientation"], orientation)

    def test_all_orientation_pixel_placements(self):
        # Manual EXIF coordinate expectations for A B C / D E F, not ImageOps.
        expected = {1: ([0, 1, 2, 3, 4, 5], (3, 2)), 2: ([2, 1, 0, 5, 4, 3], (3, 2)),
                    3: ([5, 4, 3, 2, 1, 0], (3, 2)), 4: ([3, 4, 5, 0, 1, 2], (3, 2)),
                    5: ([0, 3, 1, 4, 2, 5], (2, 3)), 6: ([3, 0, 4, 1, 5, 2], (2, 3)),
                    7: ([5, 2, 4, 1, 3, 0], (2, 3)), 8: ([2, 5, 1, 4, 0, 3], (2, 3))}
        for orientation, (order, size) in expected.items():
            pixels = bytes(channel for index in order for channel in (*COLORS[index], 255))
            digest = hashlib.sha256(str(size).encode("ascii") + pixels).hexdigest()
            for extension in ("png", "tiff"):
                with self.subTest(orientation=orientation, extension=extension):
                    result = self.fixture(f"orientation_{orientation}.{extension}")
                    self.assertEqual(result["display_size"], list(size))
                    self.assertEqual(result["display_rgba_sha256"], digest)

    def test_metadata_and_verify_do_not_prove_decode(self):
        result = self.fixture("tail_truncated.jpg")
        self.assertIsNotNone(result["capture_date"])
        self.assertEqual(result["verify_status"], "passed")
        self.assertEqual(result["decode_status"], "failed")
        self.assertEqual(result["status"], "damaged")

    def test_invalid_date_and_offset(self):
        result = self.fixture("invalid_date.jpg")
        self.assertIsNone(result["capture_date"])
        self.assertEqual(result["dates"][0]["status"], "invalid")
        result = self.fixture("invalid_offset.jpg")
        self.assertIn("invalid_offset", result["capture_date"]["issues"])
        self.assertIsNone(result["capture_date"]["utc"])
        self.assertEqual(material.parse_date("0000:00:00 00:00:00")["status"], "invalid")

    def test_unknown_timezone_and_subseconds(self):
        naive = self.fixture("naive_date.jpg")["capture_date"]
        self.assertEqual(naive["timezone"], "unknown")
        self.assertIsNone(naive["utc"])
        explicit = self.fixture("offset_subsecond.jpg")["capture_date"]
        self.assertEqual(explicit["utc"], "2023-12-31T15:15:00.125000+00:00")
        self.assertEqual(explicit["local"], "2024-01-01T00:15:00.125000")

    def test_conflicting_originals_require_review(self):
        result = self.fixture("conflicting_dates.jpg")
        self.assertTrue(result["capture_conflict"])
        self.assertIsNone(result["capture_date"])
        self.assertEqual(len(result["dates"]), 2)

    def test_modify_offset_in_exif_ifd_does_not_mean_capture(self):
        result = self.fixture("modify_date.jpg")
        self.assertIsNone(result["capture_date"])
        self.assertEqual(result["dates"][0]["utc"], "2023-12-31T15:15:00+00:00")

    def test_format_detected_from_bytes(self):
        result = self.fixture("disguised.jpg")
        self.assertEqual(result["format"], "PNG")
        self.assertIn("extension_format_mismatch", result["warnings"])
        self.assertEqual(self.fixture("empty.jpg")["status"], "unidentified_image")

    def test_same_pixels_not_same_file(self):
        first = (FIXTURES / "base.png").read_bytes()
        second = (FIXTURES / "metadata_changed.png").read_bytes()
        self.assertNotEqual(first, second)
        self.assertNotEqual(hashlib.sha256(first).digest(), hashlib.sha256(second).digest())
        self.assertEqual(material.analyze_bytes(first, "base.png")["display_rgba_sha256"],
                         material.analyze_bytes(second, "other.png")["display_rgba_sha256"])

    def test_digest_collision_not_enough(self):
        # Deliberate synthetic digest collision at grouping boundary.
        records = [{"path": "a", "size": 3, "sha256": "forced", "file_identity": [1, 1]},
                   {"path": "b", "size": 3, "sha256": "forced", "file_identity": [1, 2]}]
        self.assertEqual(material.exact_groups(records, {"a": b"abc", "b": b"xyz"}), [])

    def test_multiple_frames_and_budget(self):
        result = self.fixture("multi.tiff")
        self.assertEqual(result["frame_count"], 2)
        self.assertEqual(result["decoded_frames"], 2)
        with patch.object(material, "MAX_FRAMES", 1):
            self.assertEqual(self.fixture("multi.tiff")["status"], "resource_limit")
        with self.assertRaises(ValueError):
            material.snapshot_file(INPUTS / "plain.png", limit=10)

    def test_invalid_orientation(self):
        self.assertIn("invalid_orientation", self.fixture("invalid_orientation.jpg")["warnings"])

    def test_read_failure_does_not_abort_scan(self):
        original = material.snapshot_file
        def deny_one(path, limit):
            if path.name == "plain.png":
                raise PermissionError("injected permission failure")
            return original(path, limit)
        with patch.object(material, "snapshot_file", side_effect=deny_one):
            report = material.scan(INPUTS)
        self.assertEqual(len(report["files"]), 8)
        self.assertEqual(next(record for record in report["files"] if record["path"] == "plain.png")["status"], "read_error")
        self.assertEqual(len(report["exact_duplicates"]), 1)

    def test_scan_rerun_is_stable(self):
        self.assertEqual(material.scan(INPUTS), self.original)

    def test_copied_file_with_preserved_mtime_is_readable(self):
        root = Path(tempfile.mkdtemp(prefix="copytime-", dir=HERE))
        target = root / "dated.jpg"
        shutil.copy2(INPUTS / "session A" / "dated.jpg", target)
        # Give content mtime an older value than the new file creation timestamp.
        # Regression: stat/fstat ctime differ on this Windows/Python runtime.
        os.utime(target, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))
        data, _ = material.snapshot_file(target)
        self.assertEqual(data, (INPUTS / "session A" / "dated.jpg").read_bytes())

    def test_file_mutation_during_read_is_rejected(self):
        original = os.fstat
        calls = 0
        def change_size(fd):
            nonlocal calls
            calls += 1
            current = original(fd)
            if calls == 1:
                return current
            fields = {name: getattr(current, name) for name in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")}
            fields["st_size"] += 1
            return SimpleNamespace(**fields)
        with patch.object(material.os, "fstat", side_effect=change_size):
            with self.assertRaisesRegex(ValueError, "changed during read"):
                material.snapshot_file(INPUTS / "plain.png")

    def test_candidates_retain_uncertainty(self):
        candidates = self.original["candidates"]
        self.assertEqual(sum(item["kind"] == "date_bucket_candidate" for item in candidates), 2)
        self.assertFalse(any(item.get("path") == "broken/truncated.jpg" and item["kind"] == "date_bucket_candidate" for item in candidates))
        report = material.scan(FIXTURES)
        reviews = [item for item in report["candidates"] if item["kind"] == "metadata_review"]
        self.assertTrue(any(item["path"] == "naive_date.jpg" and "capture_timezone_unknown" in item["reasons"] for item in reviews))
        self.assertTrue(any(item["path"] == "conflicting_dates.jpg" and "conflicting_capture_dates" in item["reasons"] for item in reviews))

    def test_cli_rejects_input_or_existing_output(self):
        for output in (INPUTS / "plain.png", HERE / "photo_material.py"):
            result = subprocess.run([sys.executable, "-B", str(HERE / "photo_material.py"), str(INPUTS), "--output", str(output)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 2)

    def test_hardlinks_are_aliases_not_two_storage_objects(self):
        # Both endpoints are new lab files; never link any protected original.
        root = Path(tempfile.mkdtemp(prefix="hardlinks-", dir=HERE))
        source = root / "a.txt"
        source.write_bytes(b"synthetic alias probe")
        try:
            os.link(source, root / "b.txt")
        except OSError as error:
            self.skipTest(f"hardlink unavailable: {error}")
        groups = material.scan(root)["exact_duplicates"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["unique_file_objects"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
