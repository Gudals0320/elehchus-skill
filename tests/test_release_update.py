from __future__ import annotations

import errno
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "release_update.py"
REPO_ROOT = MODULE_PATH.parents[1]
SPEC = importlib.util.spec_from_file_location("elenchus_release_update", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
release_update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_update)


REQUIRED_PACKAGE_FILES = (
    "LICENSE",
    "README.md",
    "SKILL.md",
    "agents/openai.yaml",
    "stages/idea.md",
    "stages/research.md",
    "stages/execution.md",
    "stages/web-evidence-loop.md",
    "scripts/release_update.py",
)


def _write_valid_package(root: Path, version: str = "0.2.2") -> None:
    for relative in REQUIRED_PACKAGE_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            f'---\nname: elenchus\nmetadata:\n  version: "{version}"\n---\n'
            if relative == "SKILL.md"
            else "fixture\n"
        )
        path.write_text(content, encoding="utf-8")


class NetworkPermissionDetectionTests(unittest.TestCase):
    def test_permission_error_reason_is_classified(self) -> None:
        error = URLError(PermissionError(errno.EACCES, "network denied"))
        self.assertTrue(release_update._is_network_permission_error(error))

    def test_windows_10013_is_classified(self) -> None:
        reason = OSError("network denied")
        reason.winerror = 10013
        self.assertTrue(
            release_update._is_network_permission_error(URLError(reason))
        )

    def test_dns_error_is_not_classified(self) -> None:
        error = URLError(OSError(11001, "host not found"))
        self.assertFalse(release_update._is_network_permission_error(error))

    def test_eperm_reason_is_classified(self) -> None:
        error = URLError(PermissionError(errno.EPERM, "operation not permitted"))
        self.assertTrue(release_update._is_network_permission_error(error))

    def test_request_json_maps_permission_error(self) -> None:
        denied = URLError(PermissionError(errno.EACCES, "network denied"))
        with patch.object(release_update, "urlopen", side_effect=denied):
            with self.assertRaises(release_update.NetworkPermissionError):
                release_update._request_json("https://example.invalid")

    def test_request_json_keeps_http_error_general(self) -> None:
        failure = HTTPError(
            "https://example.invalid", 503, "unavailable", hdrs=None, fp=None
        )
        with patch.object(release_update, "urlopen", side_effect=failure):
            with self.assertRaises(release_update.UpdateError) as raised:
                release_update._request_json("https://example.invalid")
        self.assertNotIsInstance(raised.exception, release_update.NetworkPermissionError)

    def test_request_json_keeps_dns_error_general(self) -> None:
        failure = URLError(OSError(11001, "host not found"))
        with patch.object(release_update, "urlopen", side_effect=failure):
            with self.assertRaises(release_update.UpdateError) as raised:
                release_update._request_json("https://example.invalid")
        self.assertNotIsInstance(raised.exception, release_update.NetworkPermissionError)


class MainExitCodeTests(unittest.TestCase):
    def test_check_success_returns_zero(self) -> None:
        payload = {"status": "up_to_date", "current_version": "0.2.2"}
        with (
            patch.object(release_update, "check_release", return_value=payload),
            patch.object(release_update, "_emit") as emit,
        ):
            result = release_update.main(["--check"])
        self.assertEqual(result, release_update.EXIT_OK)
        emit.assert_called_once_with(payload)

    def test_check_permission_error_returns_two(self) -> None:
        failure = release_update.NetworkPermissionError("network approval required")
        with (
            patch.object(release_update, "check_release", side_effect=failure),
            patch.object(release_update, "_package_version", return_value="0.2.2"),
            patch.object(release_update, "_emit") as emit,
        ):
            result = release_update.main(["--check"])
        self.assertEqual(result, release_update.EXIT_PERMISSION_REQUIRED)
        self.assertEqual(emit.call_args.args[0]["status"], "permission_required")
        self.assertEqual(
            emit.call_args.args[0]["exit_code"],
            release_update.EXIT_PERMISSION_REQUIRED,
        )
        self.assertEqual(emit.call_args.args[0]["current_version"], "0.2.2")

    def test_check_general_failure_returns_one(self) -> None:
        failure = release_update.UpdateError("GitHub API response failed")
        with (
            patch.object(release_update, "check_release", side_effect=failure),
            patch.object(release_update, "_package_version", return_value="0.2.2"),
            patch.object(release_update, "_emit") as emit,
        ):
            result = release_update.main(["--check"])
        self.assertEqual(result, release_update.EXIT_ERROR)
        self.assertEqual(emit.call_args.args[0]["status"], "unavailable")
        self.assertEqual(emit.call_args.args[0]["exit_code"], release_update.EXIT_ERROR)

    def test_install_success_still_returns_zero(self) -> None:
        payload = {"status": "updated", "current_version": "0.2.2"}
        with (
            patch.object(release_update, "install_release", return_value=payload),
            patch.object(release_update, "_emit") as emit,
        ):
            result = release_update.main(["--install", "v0.2.2"])
        self.assertEqual(result, release_update.EXIT_OK)
        emit.assert_called_once_with(payload)

    def test_install_failure_still_returns_one(self) -> None:
        failure = release_update.UpdateError("install failed")
        with (
            patch.object(release_update, "install_release", side_effect=failure),
            patch.object(release_update, "_emit") as emit,
        ):
            result = release_update.main(["--install", "v0.2.2"])
        self.assertEqual(result, release_update.EXIT_ERROR)
        self.assertEqual(emit.call_args.args[0]["status"], "error")


class PackageValidationTests(unittest.TestCase):
    def test_validate_package_accepts_web_evidence_guide(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_valid_package(root)

            release_update._validate_package(root, "0.2.2")

    def test_validate_package_requires_web_evidence_guide(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_valid_package(root)
            (root / "stages" / "web-evidence-loop.md").unlink()

            with self.assertRaises(release_update.UpdateError) as raised:
                release_update._validate_package(root, "0.2.2")

        self.assertIn("stages/web-evidence-loop.md", str(raised.exception))

    def test_current_package_validates(self) -> None:
        release_update._validate_package(REPO_ROOT, "3.0.0")

    def test_current_layout_remains_compatible_with_v021_updater(self) -> None:
        self.assertFalse((REPO_ROOT / "references").exists())
        self.assertTrue((REPO_ROOT / "stages" / "web-evidence-loop.md").is_file())


if __name__ == "__main__":
    unittest.main()
