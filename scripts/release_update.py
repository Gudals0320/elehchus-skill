#!/usr/bin/env python3
"""Check and install stable Elenchus releases with explicit user approval."""

from __future__ import annotations

import argparse
import errno
import json
from pathlib import Path
import re
import shutil
import stat
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen
import zipfile


REPOSITORY = "Gudals0320/elehchus-skill"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
USER_AGENT = "elenchus-release-updater"
SEMVER_PATTERN = re.compile(
    r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
VERSION_PATTERN = re.compile(r'^\s*version:\s*["\']?([0-9][^\s"\']*)["\']?\s*$', re.MULTILINE)
NAME_PATTERN = re.compile(r"^\s*name:\s*elenchus\s*$", re.MULTILINE)
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_PERMISSION_REQUIRED = 2
WINDOWS_NETWORK_ACCESS_DENIED = 10013


class UpdateError(RuntimeError):
    pass


class NetworkPermissionError(UpdateError):
    pass


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _is_network_permission_error(exc: BaseException) -> bool:
    pending: list[BaseException] = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, PermissionError):
            return True
        if getattr(current, "winerror", None) == WINDOWS_NETWORK_ACCESS_DENIED:
            return True
        if getattr(current, "errno", None) in (errno.EACCES, errno.EPERM):
            return True
        for related in (
            getattr(current, "reason", None),
            current.__cause__,
            current.__context__,
        ):
            if isinstance(related, BaseException):
                pending.append(related)
    return False


def _frontmatter(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise UpdateError(f"frontmatter를 읽을 수 없습니다: {skill_md}")
    return parts[1]


def _package_version(root: Path) -> str:
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        raise UpdateError(f"SKILL.md가 없습니다: {root}")
    frontmatter = _frontmatter(skill_md)
    if not NAME_PATTERN.search(frontmatter):
        raise UpdateError("다운로드한 패키지의 skill name이 elenchus가 아닙니다.")
    match = VERSION_PATTERN.search(frontmatter)
    if not match:
        raise UpdateError("SKILL.md metadata.version을 찾을 수 없습니다.")
    version = match.group(1)
    _semver(version)
    return version


def _semver(value: str) -> tuple:
    match = SEMVER_PATTERN.fullmatch(value.strip())
    if not match:
        raise UpdateError(f"지원하지 않는 버전 형식입니다: {value}")
    major, minor, patch, prerelease = match.groups()
    identifiers = []
    for part in prerelease.split(".") if prerelease else []:
        if part.isdigit():
            if len(part) > 1 and part.startswith("0"):
                raise UpdateError(f"지원하지 않는 버전 형식입니다: {value}")
            identifiers.append((0, int(part)))
        else:
            identifiers.append((1, part))
    # Stable follows every prerelease of the same core version. Numeric
    # identifiers sort numerically and before nonnumeric identifiers.
    return (int(major), int(minor), int(patch), int(prerelease is None), tuple(identifiers))


def _require_stable_release(release: dict[str, Any]) -> None:
    if release.get("draft") or release.get("prerelease"):
        raise UpdateError("정식 Release만 확인하거나 설치할 수 있습니다.")
    if not _semver(str(release.get("tag_name", "")))[3]:
        raise UpdateError("prerelease 버전 태그는 정식 업데이트 대상이 아닙니다.")


def _request_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except HTTPError as exc:
        raise UpdateError(f"GitHub API 응답 오류: HTTP {exc.code}") from exc
    except URLError as exc:
        if _is_network_permission_error(exc):
            raise NetworkPermissionError(
                f"GitHub 네트워크 접근 권한이 필요합니다: {exc.reason}"
            ) from exc
        raise UpdateError(f"GitHub에 연결할 수 없습니다: {exc.reason}") from exc


def _latest_release() -> dict[str, Any]:
    release = _request_json(f"{API_ROOT}/releases/latest")
    _require_stable_release(release)
    return release


def _release_by_tag(tag: str) -> dict[str, Any]:
    release = _request_json(f"{API_ROOT}/releases/tags/{quote(tag, safe='')}")
    _require_stable_release(release)
    if release.get("tag_name") != tag:
        raise UpdateError("요청한 tag와 GitHub Release가 일치하지 않습니다.")
    return release


def check_release(root: Path) -> dict[str, Any]:
    current = _package_version(root)
    release = _latest_release()
    tag = str(release.get("tag_name", ""))
    latest_tuple = _semver(tag)
    current_tuple = _semver(current)
    latest = ".".join(str(part) for part in latest_tuple[:3])
    return {
        "status": "update_available" if latest_tuple > current_tuple else "up_to_date",
        "current_version": current,
        "latest_version": latest,
        "tag": tag,
        "release_url": release.get("html_url"),
    }


def _download_archive(tag: str, destination: Path) -> Path:
    archive_url = f"https://codeload.github.com/{REPOSITORY}/zip/refs/tags/{quote(tag, safe='')}"
    archive_path = destination / "release.zip"
    request = Request(archive_url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response, archive_path.open("wb") as output:
            shutil.copyfileobj(response, output)
    except HTTPError as exc:
        raise UpdateError(f"Release 다운로드 오류: HTTP {exc.code}") from exc
    except URLError as exc:
        raise UpdateError(f"Release를 다운로드할 수 없습니다: {exc.reason}") from exc

    extract_root = destination / "extracted"
    extract_root.mkdir()
    resolved_root = extract_root.resolve()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            top_levels: set[str] = set()
            for info in archive.infolist():
                candidate = (extract_root / info.filename).resolve()
                if candidate != resolved_root and resolved_root not in candidate.parents:
                    raise UpdateError("Release archive가 임시 경로 밖의 파일을 포함합니다.")
                mode = (info.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    raise UpdateError("Release archive의 symbolic link는 허용하지 않습니다.")
                parts = Path(info.filename).parts
                if parts:
                    top_levels.add(parts[0])
            if len(top_levels) != 1:
                raise UpdateError("Release archive의 최상위 디렉터리를 판별할 수 없습니다.")
            archive.extractall(extract_root)
    except zipfile.BadZipFile as exc:
        raise UpdateError("Release archive가 올바른 ZIP 파일이 아닙니다.") from exc

    package_root = extract_root / next(iter(top_levels))
    if not package_root.is_dir():
        raise UpdateError("압축을 푼 Release 디렉터리가 없습니다.")
    return package_root


def _validate_package(root: Path, expected_version: str) -> None:
    required = [
        "LICENSE",
        "README.md",
        "SKILL.md",
        "agents/openai.yaml",
        "stages/idea.md",
        "stages/research.md",
        "stages/execution.md",
        "stages/web-evidence-loop.md",
        "scripts/release_update.py",
    ]
    missing = [path for path in required if not (root / path).is_file()]
    if missing:
        raise UpdateError(f"Release에 필요한 파일이 없습니다: {', '.join(missing)}")
    if _package_version(root) != expected_version:
        raise UpdateError("Release tag와 SKILL.md metadata.version이 일치하지 않습니다.")
    for entry in root.rglob("*"):
        if entry.is_symlink():
            raise UpdateError(f"symbolic link는 설치할 수 없습니다: {entry.relative_to(root)}")
    _validate_stage_links(root)


def _markdown_links(document: Path) -> list[str]:
    """Read inline Markdown destinations, excluding fenced output examples.

    Runtime guides use inline links for package dependencies. This is not a
    general Markdown renderer; link labels, prose, and heading fragments do not
    define the package layout.
    """
    lines = []
    fence = ""
    for line in document.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            current = marker.group(1)
            if not fence:
                fence = current
            elif current[0] == fence[0] and len(current) >= len(fence):
                fence = ""
            continue
        if not fence:
            lines.append(line)
    pattern = re.compile(r'\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+"[^"\n]*")?\s*\)')
    return [match.group(1) or match.group(2) for match in pattern.finditer("\n".join(lines))]


def _validate_stage_links(root: Path) -> None:
    """Validate actual guide dependencies instead of guessing from versions.

    Old 3.0.0 metadata was a numbering mistake. Historical Idea/Execution
    packages remain valid; a Topology entrypoint requires its Lab guide to be
    reachable. Legacy shim files remain mandatory for old installed updaters.
    """
    package_root = root.resolve()
    documents = [root / "SKILL.md", *sorted((root / "stages").rglob("*.md"))]
    graph: dict[str, set[str]] = {}
    for document in documents:
        name = document.relative_to(root).as_posix()
        destinations: set[str] = set()
        for link in _markdown_links(document):
            parsed = urlsplit(link)
            if parsed.scheme == "file" or re.match(r"^[A-Za-z]:[\\/]", link):
                raise UpdateError(f"패키지 밖의 로컬 참조입니다: {name} → {link}")
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path).replace("\\", "/")).resolve()
            if target != package_root and package_root not in target.parents:
                raise UpdateError(f"패키지 밖의 로컬 참조입니다: {name} → {link}")
            if not target.is_file():
                raise UpdateError(f"Release의 로컬 참조 파일이 없습니다: {name} → {link}")
            destinations.add(target.relative_to(package_root).as_posix())
        graph[name] = destinations

    entry_links = graph["SKILL.md"]
    if "stages/research.md" not in entry_links or not entry_links.intersection(
        {"stages/idea.md", "stages/topology.md"}
    ):
        raise UpdateError("SKILL.md의 시작 단계와 Research 라우팅이 없습니다.")
    if "stages/topology.md" in entry_links:
        pending = ["SKILL.md"]
        reachable: set[str] = set()
        while pending:
            name = pending.pop()
            if name not in reachable:
                reachable.add(name)
                pending.extend(graph.get(name, set()) - reachable)
        if "stages/lab.md" not in reachable:
            raise UpdateError("Topology 패키지에서 Lab 지침으로 가는 라우팅이 없습니다.")


def _clear_package(root: Path) -> None:
    for entry in root.iterdir():
        if entry.name == ".git":
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def _copy_package(source: Path, destination: Path) -> None:
    for entry in source.iterdir():
        if entry.name == ".git":
            continue
        target = destination / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copy2(entry, target)


def _replace_package(current_root: Path, new_root: Path, expected_version: str) -> None:
    with tempfile.TemporaryDirectory(prefix="elenchus-backup-") as backup_dir:
        backup_root = Path(backup_dir) / "elenchus"
        shutil.copytree(
            current_root,
            backup_root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        try:
            _clear_package(current_root)
            _copy_package(new_root, current_root)
            _validate_package(current_root, expected_version)
        except Exception:
            _clear_package(current_root)
            _copy_package(backup_root, current_root)
            raise


def install_release(root: Path, tag: str) -> dict[str, Any]:
    current = _package_version(root)
    current_tuple = _semver(current)
    release = _release_by_tag(tag)
    target_tuple = _semver(tag)
    target_version = ".".join(str(part) for part in target_tuple[:3])
    if target_tuple <= current_tuple:
        raise UpdateError(f"현재 버전보다 새로운 Release만 설치할 수 있습니다: {current} → {target_version}")

    with tempfile.TemporaryDirectory(prefix="elenchus-release-") as temp_dir:
        package_root = _download_archive(tag, Path(temp_dir))
        _validate_package(package_root, target_version)
        _replace_package(root, package_root, target_version)

    return {
        "status": "updated",
        "previous_version": current,
        "current_version": target_version,
        "tag": tag,
        "release_url": release.get("html_url"),
        "restart_required": True,
    }


def _check_failure_payload(
    root: Path, status: str, exit_code: int, exc: Exception
) -> dict[str, Any]:
    current = None
    try:
        current = _package_version(root)
    except Exception:
        pass
    return {
        "status": status,
        "current_version": current,
        "exit_code": exit_code,
        "message": str(exc),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or update the Elenchus skill.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="Check the latest stable Release.")
    action.add_argument("--install", metavar="TAG", help="Install an explicitly approved stable tag.")
    args = parser.parse_args(argv)
    root = _skill_root()

    if args.check:
        try:
            _emit(check_release(root))
            return EXIT_OK
        except NetworkPermissionError as exc:
            _emit(
                _check_failure_payload(
                    root, "permission_required", EXIT_PERMISSION_REQUIRED, exc
                )
            )
            return EXIT_PERMISSION_REQUIRED
        except Exception as exc:
            _emit(_check_failure_payload(root, "unavailable", EXIT_ERROR, exc))
            return EXIT_ERROR

    try:
        _emit(install_release(root, args.install))
        return EXIT_OK
    except Exception as exc:
        _emit({"status": "error", "message": str(exc)})
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
