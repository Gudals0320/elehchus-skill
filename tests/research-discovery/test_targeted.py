"""Preparation selection and preservation checks; no model calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import targeted


class TargetedPreparationTests(unittest.TestCase):
    def test_default_path_remains_original_frozen_file(self):
        self.assertEqual(targeted.preparation_path(), targeted.TARGET / "frozen.json")
        with self.assertRaises(ValueError):
            targeted.preparation_path("../escape")

    def test_separate_preparation_does_not_overwrite_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "frozen.json"
            original.write_text("ORIGINAL", encoding="utf-8")
            for name in ("manifest.json", "fixtures.json", "protocol.md"):
                (root / name).write_text("fixed input", encoding="utf-8")
            snapshot = root / "candidate.json"
            snapshot.write_text(json.dumps({"revision": "new", "files": {}}), encoding="utf-8")
            with patch.object(targeted, "TARGET", root), patch.object(targeted.runner, "verify_snapshot"):
                result = targeted.prepare(snapshot, "separate")
                self.assertEqual(original.read_text(encoding="utf-8"), "ORIGINAL")
                self.assertEqual(result, root / "preparations/separate.json")
                self.assertEqual(json.loads(result.read_text(encoding="utf-8"))["source_snapshot"]["revision"], "new")
                snapshot.write_text(json.dumps({"revision": "different", "files": {}}), encoding="utf-8")
                with self.assertRaises(FileExistsError):
                    targeted.prepare(snapshot, "separate")

    def test_run_cannot_switch_snapshot_after_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "preparations").mkdir()
            (root / "preparations/probe.json").write_text(json.dumps({"source_snapshot": {"revision": "one"}}), encoding="utf-8")
            other = root / "other.json"
            other.write_text(json.dumps({"revision": "two"}), encoding="utf-8")
            with patch.object(targeted, "TARGET", root):
                with self.assertRaisesRegex(ValueError, "differs"):
                    targeted.verified_source(other, "probe")


if __name__ == "__main__":
    unittest.main()
