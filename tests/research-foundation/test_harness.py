"""Infrastructure regressions; no model runs, network or access to host auth."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import fixtures
import harness


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="elenchus-foundation-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = {"SKILL.md": b"name: elenchus\r\n", "stages/topology.md": b"topology\n"}
        with patch.object(harness, "runtime_blobs", return_value=("a" * 40, self.source)), patch.object(harness, "git", return_value=b"git test\n"):
            harness.freeze(self.root, "HEAD", self.root / "freeze")

    def prepare(self, case="photos"):
        return harness.prepare(self.root / "freeze", case + "-sample1", self.root / "actor", self.root / "results")

    def export(self, allowlist):
        return harness.export(self.root / "actor", self.root / "results", allowlist, self.root / "export")

    def test_nested_git_runtime_extracts_install_relative_bytes_only(self):
        repo = self.root / "repo"
        repo.mkdir()
        harness.git(repo, "init", "--quiet")
        for name, data in self.source.items():
            path = repo / "skills/elenchus" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (repo / "docs").mkdir()
        (repo / "docs/private-evaluation.md").write_bytes(b"not runtime")
        (repo / ".gitattributes").write_bytes(b"* -text\n")
        harness.git(repo, "add", ".")
        harness.git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture")
        _, source = harness.runtime_blobs(repo, "HEAD", ["SKILL.md", "stages"], "skills/elenchus")
        self.assertEqual(source, self.source)

    def test_freeze_preserves_crlf_blob_bytes_and_method_hashes(self):
        frozen = harness.validate_freeze(self.root / "freeze")
        self.assertEqual((self.root / "freeze/runtime/SKILL.md").read_bytes(), self.source["SKILL.md"])
        self.assertEqual(frozen["source_files"]["SKILL.md"]["crlf_count"], 1)
        self.assertEqual(frozen["source_files"]["stages/topology.md"]["crlf_count"], 0)

    def test_changed_source_or_method_cannot_reuse_freeze(self):
        with patch.object(harness, "method_hashes", return_value={}):
            with self.assertRaisesRegex(ValueError, "method changed"):
                harness.validate_freeze(self.root / "freeze")
        (self.root / "freeze/runtime/SKILL.md").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "runtime bytes"):
            harness.validate_freeze(self.root / "freeze")

    def test_changed_fixture_expectations_are_detected(self):
        (self.root / "freeze/photo-expectations.evaluator.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "fixture expectations"):
            harness.validate_freeze(self.root / "freeze")

    def test_fresh_photo_workspace_has_inputs_but_no_evaluator_or_git(self):
        record = self.prepare()
        self.assertEqual(record["status"], "prepared_not_started")
        self.assertEqual(record["session_limits"], {"seconds": None, "responses": None})
        files = harness.tree(self.root / "actor")
        self.assertTrue(any("회전" in name for name in files))
        self.assertFalse(any("evaluator" in name or "expectations" in name or ".git" in name for name in files))
        self.assertFalse((self.root / "actor/answers.md").exists())
        self.assertFalse((self.root / "actor/reproduction-input.md").exists())
        self.assertTrue((self.root / "results/answers.md").is_file())
        self.assertEqual(harness.sha((self.root / "results/reproduction-input.md").read_bytes()), record["reproduction_input_sha256"])
        self.assertIsNone(record["model_observed"])

    def test_weather_workspace_has_no_predetermined_api_corpus(self):
        self.prepare("weather")
        project = harness.tree(self.root / "actor/project")
        self.assertEqual(set(project), {"README.md", "existing-product.txt"})

    def test_preparation_never_overwrites_a_prior_run(self):
        self.prepare()
        before = (self.root / "results/preparation.json").read_bytes()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual((self.root / "results/preparation.json").read_bytes(), before)

    def test_operator_output_cannot_be_inside_actor_workspace(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            harness.prepare(self.root / "freeze", "weather-sample1", self.root / "actor", self.root / "actor/evaluator")
        self.assertFalse((self.root / "actor").exists())

    def test_export_copies_bytes_and_detects_tampering(self):
        self.prepare()
        result = self.export(["input.md", "project/inputs/회전/rotated.jpg"])
        self.assertEqual(result["status"], "complete_allowlist_copy")
        self.assertTrue(result["initial_files_unchanged"])
        self.assertEqual(harness.verify(self.root / "export")["status"], "verified")
        (self.root / "export/artifacts/input.md").write_bytes(b"tampered")
        self.assertEqual(harness.verify(self.root / "export")["mismatch"], ["input.md"])

    def test_export_keeps_successes_and_errors_without_reading_private_paths(self):
        self.prepare()
        (self.root / "actor/.git").write_text("gitdir: private", encoding="utf-8")
        (self.root / "actor/auth.json").write_text("do not export", encoding="utf-8")
        result = self.export(["input.md", "missing.md", ".git", "auth.json", "../outside.txt", "C:/Users/private/auth.json"])
        self.assertEqual(result["status"], "partial_collection")
        self.assertEqual(set(result["files"]), {"input.md"})
        self.assertEqual(len(result["errors"]), 5)
        self.assertNotIn("C:/Users", json.dumps(result))
        self.assertNotIn("do not export", json.dumps(result))
        self.assertTrue((self.root / "actor").exists())

    def test_initial_original_changes_are_detected_even_if_not_exported(self):
        self.prepare()
        (self.root / "actor/project/inputs/plain.png").write_bytes(b"damaged")
        result = self.export(["input.md"])
        self.assertFalse(result["initial_files_unchanged"])
        self.assertFalse(result["initial_files"]["project/inputs/plain.png"]["unchanged"])

    def test_reproduction_separates_project_from_actor_trace(self):
        self.prepare()
        harness.write(self.root / "actor/records/final.md", b"Actor summary\n")
        self.export(["records/final.md", "project/existing-product.txt", "project/inputs/plain.png"])
        result = harness.reproduce(self.root / "export", self.root / "reproduce")
        self.assertFalse(result["actor_activity_and_observer_records_provided"])
        self.assertFalse((self.root / "reproduce/records").exists())
        self.assertEqual(set(harness.tree(self.root / "reproduce")), {"input.md", "project/existing-product.txt", "project/inputs/plain.png"})

    def test_reproduction_uses_prepared_bytes_after_current_method_drifts(self):
        self.prepare()
        expected = (self.root / "results/reproduction-input.md").read_bytes()
        changed_method = self.root / "changed-method"
        harness.write(changed_method / "evaluator/reproduce.md", b"Changed evaluator instructions must not enter this run.\n")
        with patch.object(harness, "HERE", changed_method):
            exported = self.export(["project/existing-product.txt"])
            result = harness.reproduce(self.root / "export", self.root / "reproduce")
        self.assertEqual(exported["reproduction_input"]["published_sha256"], harness.sha(expected))
        self.assertEqual(result["input_sha256"], harness.sha(expected))
        self.assertEqual((self.root / "reproduce/input.md").read_bytes(), expected)

    def test_modified_prepared_reproduction_input_is_not_exported_or_replaced(self):
        self.prepare()
        (self.root / "results/reproduction-input.md").write_bytes(b"tampered")
        result = self.export(["project/existing-product.txt"])
        self.assertEqual(result["status"], "partial_collection")
        self.assertEqual(result["reproduction_input"]["status"], "unavailable")
        self.assertFalse((self.root / "export/reproduction-input.md").exists())
        self.assertTrue((self.root / "export/artifacts/project/existing-product.txt").is_file())
        with self.assertRaisesRegex(ValueError, "integrity failed"):
            harness.reproduce(self.root / "export", self.root / "reproduce")
        self.assertFalse((self.root / "reproduce").exists())

    def test_missing_prepared_reproduction_input_is_a_collection_error(self):
        self.prepare()
        (self.root / "results/reproduction-input.md").unlink()
        result = self.export(["project/existing-product.txt"])
        self.assertEqual(result["status"], "partial_collection")
        self.assertEqual([error["path"] for error in result["errors"]], ["reproduction-input.md"])
        self.assertEqual(harness.verify(self.root / "export")["status"], "mismatch")

    def test_exported_reproduction_input_tampering_blocks_reproduction(self):
        self.prepare()
        self.export(["project/existing-product.txt"])
        (self.root / "export/reproduction-input.md").write_bytes(b"tampered")
        self.assertEqual(harness.verify(self.root / "export")["mismatch"], ["reproduction-input.md"])
        with self.assertRaisesRegex(ValueError, "integrity failed"):
            harness.reproduce(self.root / "export", self.root / "reproduce")
        self.assertFalse((self.root / "reproduce").exists())

    def test_actor_and_observer_events_remain_distinct(self):
        self.prepare()
        harness.event(self.root / "results", "actor_record", "web_read", "Actor reports retrieval", [])
        harness.event(self.root / "results", "observer_event", "answer", "Public reply received", [])
        records = [json.loads(line) for line in (self.root / "results/events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["source"] for row in records], ["actor_record", "observer_event"])
        with self.assertRaises(ValueError):
            harness.event(self.root / "results", "full_trace", "test", "unknown", [])

    def test_symlink_or_junction_file_is_not_exported(self):
        self.prepare()
        target = self.root / "actor/linked.md"
        try:
            target.symlink_to(self.root / "actor/input.md")
        except OSError:
            self.skipTest("host does not permit test symlinks")
        result = self.export(["linked.md"])
        self.assertEqual(result["status"], "partial_collection")
        self.assertEqual(result["files"], {})

    def test_link_rejection_does_not_depend_on_host_creation_permission(self):
        self.prepare()
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "symlink/junction"):
                harness.checked_path(self.root / "actor", "input.md")


class FixtureTests(unittest.TestCase):
    def test_duplicate_group_and_different_exif_are_distinct(self):
        files = fixtures.photo_files()
        self.assertEqual(files["session A/dated.jpg"], files["copies/duplicate.jpg"])
        self.assertNotEqual(files["session A/dated.jpg"], files["회전/rotated.jpg"])
        self.assertEqual(fixtures.photo_expectations()["sha256"], {name: harness.sha(data) for name, data in sorted(files.items())})

    def test_tiff_ifd_points_to_original_fixture_date_and_pixels(self):
        data = fixtures.tiff()
        count = struct.unpack_from("<H", data, 8)[0]
        tags = {}
        for at in range(10, 10 + count * 12, 12):
            tag, kind, items, value = struct.unpack_from("<HHII", data, at)
            tags[tag] = (kind, items, value)
        self.assertEqual(tags[274][2], 8)
        at = tags[306][2]
        self.assertEqual(data[at:at + tags[306][1]], b"2024:07:15 10:20:30\0")
        self.assertEqual(len(data) - tags[273][2], 8 * 6 * 3)

    def test_jpeg_exif_subifd_has_offset_date_without_changing_image_stream(self):
        data = fixtures.jpeg_with_exif(1, "2024:07:15 10:20:30", "+09:00")
        length = struct.unpack_from(">H", data, 4)[0]
        self.assertEqual(data[6:12], b"Exif\0\0")
        self.assertEqual(data[4 + length:], fixtures.JPEG[2:])
        self.assertIn(b"+09:00\0", data)
        self.assertNotIn(b"2024:", fixtures.jpeg_with_exif(6))


if __name__ == "__main__":
    unittest.main()
