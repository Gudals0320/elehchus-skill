"""Package dependency and byte-preserving update tests for the Topology layout.

Historical updater tests load the actual pinned source from local Git objects.
They make no network requests and skip explicitly when those objects are absent.
They do not claim that a prerelease is installable through the stable updater.
"""
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile

from test_release_update import REPO_ROOT, _write_valid_package, release_update


HISTORICAL_PACKAGES = (
    ("b369a84f388818b79cca86767e13af0574ec03a9", "1.0.0"),
    ("73a7ddfcb25b78dcb9071e50f2dcd875d3bf1850", "1.1.0-beta.1"),
    ("132eea57d10baa68cd6482a9d0d2e170afd7357e", "3.0.0"),
)
RUNTIME_PATHS = ("LICENSE", "README.md", "SKILL.md", "agents", "stages", "scripts")


def _foundation_fixture(root: Path, version: str = "1.1.0") -> None:
    _write_valid_package(root, version)
    skill = root / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace("stages/idea.md", "stages/topology.md"),
        encoding="utf-8",
    )
    (root / "stages/topology.md").write_text("[Research](research.md)\n", encoding="utf-8")
    (root / "stages/research.md").write_text("[Lab](lab.md#execution)\n", encoding="utf-8")
    (root / "stages/lab.md").write_text("# Lab\n", encoding="utf-8")


def _runtime_copy(destination: Path, version: str | None = None) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative in RUNTIME_PATHS:
        source = REPO_ROOT / relative
        if source.is_dir():
            shutil.copytree(source, destination / relative,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copyfile(source, destination / relative)
    if version is not None:
        skill = destination / "SKILL.md"
        content = skill.read_bytes().decode("utf-8")
        content = release_update.VERSION_PATTERN.sub(
            lambda match: match.group(0).replace(match.group(1), version, 1), content, count=1
        )
        skill.write_bytes(content.encode("utf-8"))


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def _historical_copy(commit: str, destination: Path) -> None:
    archive = subprocess.run(
        ["git", "archive", "--format=zip", commit, "--", *RUNTIME_PATHS],
        cwd=REPO_ROOT, check=True, capture_output=True,
    ).stdout
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        # Only the fixed, local commits above are used as test inputs.
        source.extractall(destination)


def _updater(root: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, root / "scripts/release_update.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GuideDependencyTests(unittest.TestCase):
    def test_referenced_topology_or_lab_missing_is_rejected(self) -> None:
        for relative in ("stages/topology.md", "stages/lab.md"):
            with self.subTest(file=relative), TemporaryDirectory() as folder:
                root = Path(folder)
                _foundation_fixture(root)
                (root / relative).unlink()
                with self.assertRaises(release_update.UpdateError):
                    release_update._validate_package(root, "1.1.0")

    def test_missing_required_entry_route_is_rejected(self) -> None:
        for route in ("[Research](stages/research.md)", "[Idea](stages/topology.md)"):
            with self.subTest(route=route), TemporaryDirectory() as folder:
                root = Path(folder)
                _foundation_fixture(root)
                skill = root / "SKILL.md"
                skill.write_text(skill.read_text(encoding="utf-8").replace(route, ""), encoding="utf-8")
                with self.assertRaises(release_update.UpdateError):
                    release_update._validate_package(root, "1.1.0")

    def test_existing_lab_without_a_readable_route_is_rejected(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder)
            _foundation_fixture(root)
            (root / "stages/research.md").write_text("# Research\n", encoding="utf-8")
            with self.assertRaises(release_update.UpdateError):
                release_update._validate_package(root, "1.1.0")

    def test_nested_guide_dependency_is_checked_before_replacement(self) -> None:
        with TemporaryDirectory() as folder:
            root, package = Path(folder) / "installed", Path(folder) / "downloaded"
            _write_valid_package(root, "1.0.0")
            _foundation_fixture(package)
            (package / "stages/lab.md").write_text("[Run guide](missing.md)\n", encoding="utf-8")
            before = _file_bytes(root)
            with (
                patch.object(release_update, "_request_json", return_value={"tag_name": "v1.1.0"}),
                patch.object(release_update, "_download_archive", return_value=package),
                patch.object(release_update, "_replace_package") as replace,
                self.assertRaises(release_update.UpdateError),
            ):
                release_update.install_release(root, "v1.1.0")
            replace.assert_not_called()
            self.assertEqual(_file_bytes(root), before)

    def test_examples_external_urls_and_heading_links_are_not_files(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder)
            _foundation_fixture(root)
            (root / "stages/lab.md").write_text(
                '# Lab\n[Top](topology.md#purpose)\n[Self](#lab)\n'
                '[Web](https://example.invalid/not-a-package.md)\n'
                '```markdown\n[Output](R001-generated.md)\n```\n'
                '~~~markdown\n[Output](another-generated.md)\n~~~\n', encoding="utf-8",
            )
            with patch.object(release_update, "urlopen") as request:
                release_update._validate_package(root, "1.1.0")
            request.assert_not_called()

    def test_angle_links_with_spaces_resolve_inside_package(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder)
            _foundation_fixture(root)
            (root / "stages/run guide.md").write_text("# Run\n", encoding="utf-8")
            (root / "stages/lab.md").write_text('[Run](<run guide.md> "guide")\n', encoding="utf-8")
            release_update._validate_package(root, "1.1.0")
            (root / "stages/run guide.md").unlink()
            with self.assertRaises(release_update.UpdateError):
                release_update._validate_package(root, "1.1.0")

    def test_package_external_file_cannot_satisfy_dependency(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder) / "package"
            _foundation_fixture(root)
            outside = Path(folder) / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            for link in ("../../outside.md", outside.as_posix(), outside.as_uri()):
                with self.subTest(link=link):
                    (root / "stages/lab.md").write_text(f"[Run](<{link}>)\n", encoding="utf-8")
                    with self.assertRaises(release_update.UpdateError):
                        release_update._validate_package(root, "1.1.0")


class CurrentFoundationPackageTests(unittest.TestCase):
    def test_every_new_guide_is_packaged_and_reachable(self) -> None:
        pending = ["SKILL.md"]
        reached = set()
        while pending:
            name = pending.pop()
            if name in reached:
                continue
            reached.add(name)
            document = REPO_ROOT / name
            self.assertTrue(document.is_file(), name)
            for link in release_update._markdown_links(document):
                parsed = release_update.urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (document.parent / release_update.unquote(parsed.path)).resolve()
                if target.suffix == ".md" and target.parent == REPO_ROOT / "stages":
                    pending.append(target.relative_to(REPO_ROOT).as_posix())
        self.assertTrue({"stages/topology.md", "stages/research.md", "stages/discovery.md",
                         "stages/lab.md", "stages/web-evidence-loop.md"}.issubset(reached))

    def test_actual_new_guides_cannot_be_omitted_from_archive(self) -> None:
        for relative in ("stages/topology.md", "stages/lab.md", "stages/discovery.md"):
            with self.subTest(file=relative), TemporaryDirectory() as folder:
                root = Path(folder) / "package"
                _runtime_copy(root)
                (root / relative).unlink()
                with self.assertRaises(release_update.UpdateError):
                    release_update._validate_package(root, "1.1.0-beta.2")

    def test_copy_preserves_all_runtime_and_binary_bytes(self) -> None:
        with TemporaryDirectory() as folder:
            source, destination = Path(folder) / "source", Path(folder) / "copied"
            _runtime_copy(source)
            (source / "fixture.bin").write_bytes(b"\x00\xff\r\nfixture\n")
            destination.mkdir()
            release_update._copy_package(source, destination)
            self.assertEqual(_file_bytes(destination), _file_bytes(source))
            release_update._validate_package(destination, "1.1.0-beta.2")

    def test_incomplete_replacement_restores_original_bytes_and_git(self) -> None:
        with TemporaryDirectory() as folder:
            current, incoming = Path(folder) / "current", Path(folder) / "incoming"
            _write_valid_package(current, "1.0.0")
            (current / "private-fixture.bin").write_bytes(b"\x00\xfe\r\noriginal\n")
            (current / ".git").mkdir()
            (current / ".git/HEAD").write_bytes(b"ref: refs/heads/local\n")
            _runtime_copy(incoming, "1.1.0")
            (incoming / "stages/lab.md").unlink()
            before = _file_bytes(current)
            with self.assertRaises(release_update.UpdateError):
                release_update._replace_package(current, incoming, "1.1.0")
            self.assertEqual(_file_bytes(current), before)


class HistoricalUpdaterCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("git"):
            raise unittest.SkipTest("Historical source checks require local Git objects; git is unavailable.")
        for commit, _ in HISTORICAL_PACKAGES:
            result = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                                    cwd=REPO_ROOT, capture_output=True)
            if result.returncode:
                raise unittest.SkipTest(f"Historical source check unavailable: local commit {commit} is absent.")

    def test_original_historical_packages_still_validate(self) -> None:
        for commit, version in HISTORICAL_PACKAGES:
            with self.subTest(version=version), TemporaryDirectory() as folder:
                root = Path(folder)
                _historical_copy(commit, root)
                before = _file_bytes(root)
                release_update._validate_package(root, version)
                self.assertEqual(_file_bytes(root), before)

    def test_old_updaters_install_new_layout_with_simulated_stable_metadata(self) -> None:
        for commit, version in HISTORICAL_PACKAGES[:2]:
            with self.subTest(updater=version), TemporaryDirectory() as folder:
                current, incoming = Path(folder) / "current", Path(folder) / "incoming"
                _historical_copy(commit, current)
                old = _updater(current, f"historical_updater_{commit}")
                _runtime_copy(incoming, "1.1.0")
                expected = _file_bytes(incoming)
                with (
                    patch.object(old, "_request_json", return_value={"tag_name": "v1.1.0", "prerelease": False}),
                    patch.object(old, "_download_archive", return_value=incoming),
                ):
                    result = old.install_release(current, "v1.1.0")
                self.assertEqual(result["status"], "updated")
                self.assertEqual(result["previous_version"], version)
                self.assertEqual(_file_bytes(current), expected)
                release_update._validate_package(current, "1.1.0")

    def test_old_updaters_keep_rejecting_prerelease_downloads(self) -> None:
        for commit, version in HISTORICAL_PACKAGES[:2]:
            with self.subTest(updater=version), TemporaryDirectory() as folder:
                current = Path(folder)
                _historical_copy(commit, current)
                old = _updater(current, f"historical_beta_rejection_{commit}")
                before = _file_bytes(current)
                with (
                    patch.object(old, "_request_json", return_value={
                        "tag_name": "v1.1.0-beta.2", "prerelease": True}),
                    patch.object(old, "_download_archive") as download,
                    self.assertRaises(old.UpdateError),
                ):
                    old.install_release(current, "v1.1.0-beta.2")
                download.assert_not_called()
                self.assertEqual(_file_bytes(current), before)


if __name__ == "__main__":
    unittest.main()
