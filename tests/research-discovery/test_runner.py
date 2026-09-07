"""Deterministic harness checks; these are not model-compliance evidence."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import runner


class ArchiveAndFixtureTests(unittest.TestCase):
    def test_archive_paths_reject_traversal_and_windows_drives(self):
        for path in ("../auth.json", "/etc/passwd", "C:/private.txt", "stages/../../config", "stages\\file"):
            self.assertFalse(runner.safe_member(path), path)
        self.assertTrue(runner.safe_member("stages/discovery.md"))

    def test_fixture_copy_excludes_rubric_manifest_and_previous_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner.prepare_project(root, {"SKILL.md": b"skill-copy", "stages/discovery.md": b"stage"}, "casino")
            paths = set(runner.tree_hashes(root))
            self.assertIn("skill/stages/discovery.md", paths)
            self.assertIn("evidence/02-tablehaven-developer.md", paths)
            self.assertEqual((root / "app.txt").read_text(), "UNIMPLEMENTED PRODUCT STUB\n")
            self.assertNotIn("manifest.json", paths)
            self.assertNotIn("README.md", paths)
            self.assertFalse(any("results/" in path for path in paths))

    def test_manifest_has_eight_bounded_controlled_cells(self):
        controlled = runner.MANIFEST["controlled"]
        self.assertEqual(len(controlled["cases"]) * len(controlled["variants"]) * controlled["samples_per_cell"], 8)
        self.assertEqual(controlled["max_responses"], 8)
        self.assertEqual(controlled["max_seconds"], 600)
        self.assertFalse(runner.MANIFEST["live"]["included_in_controlled_totals"])

    def test_changed_candidate_bytes_are_rejected(self):
        snapshot = {"revision": None, "files": {"SKILL.md": runner.sha(b"before")}}
        with patch.object(runner, "runtime_bytes", return_value={"SKILL.md": b"after"}):
            with self.assertRaisesRegex(ValueError, "Runtime changed"):
                runner.verify_snapshot(snapshot)

    def test_inaccessible_directory_is_not_treated_as_empty(self):
        with patch.object(runner.os, "walk", side_effect=PermissionError("inaccessible artifact")):
            with self.assertRaises(PermissionError):
                runner.tree_hashes(Path("project"))

    def test_host_read_setup_rejects_non_evaluation_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(runner.subprocess, "run") as command:
                with self.assertRaisesRegex(ValueError, "exact runner-created"):
                    runner.prepare_host_read(Path(temporary) / "project")
            command.assert_not_called()


class PublicationTests(unittest.TestCase):
    def test_reasoning_unknown_and_non_json_are_not_published(self):
        raw = "\n".join([
            json.dumps({"type": "item.completed", "item": {"type": "reasoning", "text": "SECRET_REASONING"}}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "visible"}}),
            json.dumps({"type": "unknown", "text": "UNKNOWN_PAYLOAD"}), "RAW_PAYLOAD"])
        events, excluded = runner.public_events(raw, runner.Redactor())
        output = json.dumps(events)
        self.assertNotIn("SECRET_REASONING", output)
        self.assertNotIn("UNKNOWN_PAYLOAD", output)
        self.assertNotIn("RAW_PAYLOAD", output)
        self.assertIn("visible", output)
        self.assertEqual(excluded, {"reasoning": 1, "unknown": 1, "non_json": 1})

    def test_paths_and_credentials_are_redacted(self):
        redact = runner.Redactor({"C:\\Users\\someone\\AppData\\Local\\Temp\\sample": "<fixture>"})
        result = redact.apply({"access_token": "opaque-secret", "text":
            "C:\\Users\\someone\\AppData\\Local\\Temp\\sample\\a.md C:/Users/someone/x Bearer abcd.123 sk-123456789abcdefgh"})
        text = json.dumps(result)
        self.assertNotIn("opaque-secret", text)
        self.assertNotIn("someone", text)
        self.assertNotIn("abcd.123", text)
        self.assertNotIn("sk-123456789abcdefgh", text)
        self.assertIn("<fixture>", text)
        doubled = redact.text(r"C:\\Users\\someone\\project\\file.md")
        self.assertNotIn("someone", doubled)

    def test_auth_read_output_is_fully_removed(self):
        raw = json.dumps({"type": "item.completed", "item": {"id": "a", "type": "command_execution",
            "command": "Get-Content C:/Users/a/.codex/auth.json", "aggregated_output": "otherwise-unrecognized-secret"}})
        events, _ = runner.public_events(raw, runner.Redactor())
        self.assertTrue(events[0]["item"]["privacy_redacted"])
        self.assertNotIn("otherwise-unrecognized-secret", json.dumps(events))

    def test_host_usage_is_retained_exactly(self):
        usage = {"input_tokens": 120, "cached_input_tokens": 20, "output_tokens": 17, "reasoning_output_tokens": 5}
        events, _ = runner.public_events(json.dumps({"type": "turn.completed", "usage": usage}), runner.Redactor())
        self.assertEqual(events[0]["usage"], usage)


class ExecutionTests(unittest.TestCase):
    @unittest.skipUnless(runner.os.name == "nt", "Windows ACL command decoding")
    def test_localized_acl_output_does_not_require_utf8(self):
        with tempfile.TemporaryDirectory(prefix="elenchus-research-eval-unit-") as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            outputs = [subprocess.CompletedProcess([], 0, b'"\xb8host","S-1-5-21-123-456-789-1001"\r\n', b""),
                       subprocess.CompletedProcess([], 0, b"\xb8\xb8\xb8", b"")]
            with patch.object(runner.subprocess, "run", side_effect=outputs) as run:
                result = runner.prepare_host_read(project)
            self.assertEqual(result["status"], "host_read_ace_prepared")
            self.assertTrue(all("text" not in call.kwargs for call in run.call_args_list))

    def _exercise_sample_cleanup(self, incomplete=False, unlimited=False, reviewed=False):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            fixture = base / "fixtures/casino"
            (fixture / "evidence").mkdir(parents=True)
            (fixture / "request.md").write_text("original request", encoding="utf-8")
            (fixture / "preferences.md").write_text("preferences", encoding="utf-8")
            (base / "fixtures/continuation.md").write_text("continue", encoding="utf-8")
            (base / "README.md").write_text("test protocol", encoding="utf-8")
            snapshot = base / "snapshot.json"
            runner.write_json(snapshot, {"variant": "candidate", "label": "unit"})
            model_root = base / "elenchus-research-eval-unit"
            model_root.mkdir()
            config = {**runner.MANIFEST, "controlled": {**runner.MANIFEST["controlled"], "max_responses": 1}}
            result = {"stdout": json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "visible"}}),
                      "stderr": "", "exit_code": 0, "timed_out": False, "elapsed_seconds": 0.01}
            args = SimpleNamespace(snapshot=snapshot, case="casino", sample=1, label=None, cli="fake-cli")
            if unlimited or reviewed:
                args.no_time_limit = True
                args.max_responses = 0
            args.operator_review = reviewed
            original_hashes = runner.tree_hashes
            original_cleanup = runner.cleanup_temporary
            tree_calls = []

            def observed_hashes(path):
                tree_calls.append(path)
                if incomplete and len(tree_calls) > 1:
                    raise PermissionError("export must remain unobserved")
                return original_hashes(path)

            def attempted_cleanup(path):
                if incomplete:
                    return original_cleanup(path)
                return {"status": "retained_on_error", "error": "access denied"}

            with patch.object(runner, "HERE", base), patch.object(runner, "MANIFEST", config), \
                 patch.object(runner, "verify_snapshot", return_value={"SKILL.md": b"sample"}), \
                 patch.object(runner, "prepare_host_read", return_value={"status": "test_only"}), \
                 patch.object(runner, "call_cli", side_effect=lambda *args: dict(result)) as model_call, \
                 patch.object(runner, "reported_verdict", side_effect=[True] * 3 if reviewed else [False] * 8 + [True]), \
                 patch.object(runner, "await_operator_control", side_effect=[
                     {"action": "continue", "reason": "PRIVATE_OPERATOR_QUALITY_NOTE"},
                     {"action": "stop", "reason": "operator reviewed documents", "outcome": "research_result_delivered"}]) as gate, \
                 patch.object(runner, "tree_hashes", side_effect=observed_hashes), \
                 patch.object(runner.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "fake", "")), \
                 patch.object(runner.tempfile, "mkdtemp", return_value=str(model_root)), \
                 patch.object(runner.tempfile, "TemporaryDirectory", side_effect=AssertionError("automatic cleanup is forbidden")), \
                 patch.object(runner, "cleanup_temporary", side_effect=attempted_cleanup) as cleanup:
                output = runner.run_sample(args)
            if unlimited:
                self.assertEqual(model_call.call_count, 9)
                self.assertTrue(all(call.args[2] is None for call in model_call.call_args_list))
            if reviewed:
                self.assertEqual(model_call.call_count, 3)
                self.assertEqual(gate.call_count, 2)
                self.assertTrue(all("PRIVATE_OPERATOR_QUALITY_NOTE" not in call.args[1] for call in model_call.call_args_list))
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            return summary, model_root.exists(), cleanup.call_count

    def test_sample_records_cleanup_failure_without_automatic_finalizer(self):
        summary, exists, calls = self._exercise_sample_cleanup()
        self.assertEqual(summary["cleanup_status"], "retained_on_error")
        self.assertEqual(summary["artifact_collection"], "complete")
        self.assertTrue(summary["product_unchanged"])
        self.assertEqual(summary["status"], "response_limit")
        self.assertTrue(exists)
        self.assertEqual(calls, 1)

    def test_unlimited_sample_continues_past_eight_responses_and_exports_each_turn(self):
        summary, _, _ = self._exercise_sample_cleanup(unlimited=True)
        self.assertEqual(summary["status"], "reported_research_verdict")
        self.assertEqual(summary["limits"], {"max_responses": None, "max_seconds": None})
        self.assertEqual(len(summary["turns"]), 9)
        self.assertTrue(all(turn["artifact_collection"] == "complete" for turn in summary["turns"]))
        self.assertEqual(summary["quality_verdict"], "not_automatically_graded")

    def test_operator_gate_ignores_verdict_hint_and_keeps_notes_out_of_input(self):
        summary, _, _ = self._exercise_sample_cleanup(reviewed=True)
        self.assertEqual(summary["status"], "operator_stopped")
        self.assertEqual(summary["operator_outcome"], "research_result_delivered")
        self.assertEqual(len(summary["turns"]), 3)
        self.assertTrue(summary["turns"][1]["reported_verdict_hint"])
        self.assertEqual(summary["turns"][1]["operator_control"]["action"], "continue")
        self.assertNotIn("operator_control", summary["turns"][0])
        self.assertEqual(summary["model_processing_seconds"], 0.03)

    def test_operator_gate_waits_without_deadline_and_retains_control(self):
        with tempfile.TemporaryDirectory() as temporary:
            turn_dir = Path(temporary)
            control = {"action": "stop", "reason": "genuine missing preference", "outcome": "needs_user_input"}
            with patch.object(runner.time, "sleep", side_effect=lambda _: runner.write_json(turn_dir / "control.json", control)) as sleep:
                self.assertEqual(runner.await_operator_control(turn_dir), control)
            sleep.assert_called_once_with(0.5)
            self.assertTrue((turn_dir / "control.json").exists())
            for invalid in ({"action": "stop", "reason": "reason"}, {"action": "continue", "reason": ""}, []):
                runner.write_json(turn_dir / "control.json", invalid)
                with self.assertRaises(ValueError):
                    runner.await_operator_control(turn_dir)

    def test_limits_require_separate_explicit_opt_ins(self):
        defaults = runner.MANIFEST["controlled"]
        self.assertEqual(runner.sample_limits(SimpleNamespace()),
                         {"max_responses": defaults["max_responses"], "max_seconds": defaults["max_seconds"]})
        self.assertEqual(runner.sample_limits(SimpleNamespace(no_time_limit=True)),
                         {"max_responses": defaults["max_responses"], "max_seconds": None})
        self.assertEqual(runner.sample_limits(SimpleNamespace(max_responses=0)),
                         {"max_responses": None, "max_seconds": defaults["max_seconds"]})
        self.assertEqual(runner.sample_limits(SimpleNamespace(max_responses=12))["max_responses"], 12)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            runner.sample_limits(SimpleNamespace(max_responses=-1))
        with self.assertRaisesRegex(ValueError, "requires no-time-limit"):
            runner.sample_limits(SimpleNamespace(operator_review=True))

    def test_incomplete_collection_preserves_workspace_without_attempting_cleanup(self):
        summary, exists, calls = self._exercise_sample_cleanup(incomplete=True)
        self.assertEqual(summary["artifact_collection"], "incomplete")
        self.assertEqual(summary["cleanup_status"], "skipped_preserve_incomplete_evidence")
        self.assertIsNone(summary["product_unchanged"])
        self.assertTrue(exists)
        self.assertEqual(calls, 0)

    def test_cli_is_ephemeral_no_user_config_and_restricted(self):
        command = runner.cli_command("codex", Path("project"), Path("final.md"), "gpt-6-astra", "xhigh")
        for flag in ("--ephemeral", "--ignore-user-config", "workspace-write", "never", 'web_search="disabled"', "features.multi_agent=false"):
            self.assertIn(flag, command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)

    def test_prompt_contains_only_same_sample_public_history(self):
        result = runner.prompt_for([("user", "original"), ("assistant", "visible reply"), ("user", "next")])
        for text in ("original", "visible reply", "next"):
            self.assertIn(text, result)
        self.assertNotIn("사전 판정 기준", result)

    def test_partial_template_is_not_a_reported_conclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            document = project / ".elenchus/research/R001-test.md"
            document.parent.mkdir(parents=True)
            document.write_text("상태: 확정\n## Verdict\nTODO\n", encoding="utf-8")
            self.assertFalse(runner.reported_verdict(project, "조사 중", preferences_delivered=True))
            document.write_text("상태: 작성 중\n## Verdict\n판정: 결론 보류\n사진 미제공", encoding="utf-8")
            self.assertTrue(runner.reported_verdict(project, "사진이 없어 결론을 보류합니다.", preferences_delivered=True))

    def test_enum_and_todo_draft_are_not_selected_conclusions(self):
        draft = "상태: 작성 중\n## Verdict\n판정: 결론 가능 | 결론 보류\n근거: TODO"
        self.assertFalse(runner.selected_document_conclusion(draft))
        self.assertFalse(runner.selected_document_conclusion(draft.replace("결론 가능 | ", "")))
        self.assertFalse(runner.conclusion_signal("이제 근거 공백부터 조사하겠습니다."))
        for separator in ("|", "/", "또는", "혹은"):
            self.assertFalse(runner.selected_document_conclusion(f"## 결론\n판정: 결론 가능 {separator} 결론 보류"))

    def test_actual_completed_artifact_accepts_scoped_mixed_verdicts(self):
        record_root = runner.HERE / "phase-isolation/results/candidate-v2-casino"
        relative = ".elenchus/research/R002-animation-production.md"
        artifact = record_root / "artifacts" / relative
        metadata = json.loads((record_root / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(runner.sha(artifact.read_bytes()), metadata["artifacts"][relative]["published_sha256"])
        content = artifact.read_text(encoding="utf-8")
        self.assertIn("탐색 판정: 결론 가능", content)
        self.assertIn("검증 판정: 결론 보류", content)
        self.assertTrue(runner.selected_document_conclusion(content))

    def test_natural_korean_conclusion_requires_preferences_before_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            document = project / ".elenchus/research/R001-test.md"
            document.parent.mkdir(parents=True)
            document.write_text("상태: 작성 중\n## 결론과 다음 행동\n기존 파일을 보존하는 참조 카탈로그를 권고합니다.\n"
                                "화면의 체감은 직접 관찰하지 못해 사용자 판단을 보류합니다.", encoding="utf-8")
            answer = "## 조사 결론\n참조 카탈로그를 권고합니다. 화면의 체감 판단은 보류합니다."
            self.assertTrue(runner.reported_verdict(project, answer, preferences_delivered=True))
            self.assertFalse(runner.reported_verdict(project, answer, preferences_delivered=False))
            self.assertFalse(runner.reported_verdict(project, answer))

    def test_cli_startup_failure_is_preserved(self):
        with patch.object(runner.subprocess, "Popen", side_effect=FileNotFoundError("missing-cli")):
            result = runner.call_cli(["nonexistent"], "test", 1)
        self.assertTrue(result["startup_error"])
        self.assertIsNone(result["exit_code"])
        self.assertFalse(result["timed_out"])

    def test_real_child_output_and_timeout_are_distinct(self):
        normal = runner.call_cli([sys.executable, "-c", "print('READY')"], "", 5)
        self.assertEqual(normal["stdout"].strip(), "READY")
        self.assertFalse(normal["timed_out"])
        timed = runner.call_cli([sys.executable, "-c", "import time; time.sleep(20)"], "", 0.15)
        self.assertTrue(timed["timed_out"])
        self.assertNotEqual(timed["exit_code"], 0)

    def test_untimed_child_receives_none_deadline_without_termination(self):
        process = SimpleNamespace(communicate=lambda *args, **kwargs: ("READY", ""), returncode=0)
        with patch.object(process, "communicate", return_value=("READY", "")) as communicate, \
             patch.object(runner.subprocess, "Popen", return_value=process), \
             patch.object(runner.subprocess, "run") as external:
            result = runner.call_cli(["fake-cli"], "prompt", None)
        communicate.assert_called_once_with("prompt", timeout=None)
        external.assert_not_called()
        self.assertFalse(result["timed_out"])

    def test_real_untimed_child_finishes_normally(self):
        result = runner.call_cli([sys.executable, "-c", "print('UNTIMED_READY')"], "", None)
        self.assertEqual(result["stdout"].strip(), "UNTIMED_READY")
        self.assertEqual(result["exit_code"], 0)
        self.assertFalse(result["timed_out"])


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("research_eval_release_update", runner.REPO / "scripts/release_update.py")
        cls.release = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.release
        spec.loader.exec_module(cls.release)

    def test_current_discovery_survives_existing_package_copy(self):
        version = re.search(r'version:\s*"([^"]+)"', (runner.REPO / "SKILL.md").read_text(encoding="utf-8")).group(1)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "package"
            destination.mkdir()
            self.release._copy_package(runner.REPO, destination)
            self.release._validate_package(destination, version)
            copied = destination / "stages/discovery.md"
            self.assertEqual(copied.read_bytes(), (runner.REPO / "stages/discovery.md").read_bytes())

    def test_baseline_without_discovery_still_validates(self):
        source = runner.runtime_bytes(runner.MANIFEST["baseline_revision"])
        for name in ("LICENSE", "README.md"):
            source[name] = subprocess.run(["git", "show", runner.MANIFEST["baseline_revision"] + ":" + name],
                                          cwd=runner.REPO, capture_output=True, check=True).stdout
        self.assertNotIn("stages/discovery.md", source)
        version = re.search(r'version:\s*"([^"]+)"', source["SKILL.md"].decode()).group(1)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, data in source.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            self.release._validate_package(root, version)


if __name__ == "__main__":
    unittest.main()
