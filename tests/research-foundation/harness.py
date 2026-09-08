#!/usr/bin/env python3
"""Prepare/export native evaluation evidence; never invokes an actor or reads host auth."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from fixtures import photo_expectations, photo_files

HERE = Path(__file__).resolve().parent
BLOCKED_PARTS = {".git", ".codex", ".agents", "node_modules", ".venv", "venv", "__pycache__"}
BLOCKED_NAMES = {"auth.json", "config.toml", ".env", "credentials", "credentials.json", "id_rsa", "id_ed25519"}
MAX_FILE_BYTES = 32 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_relative(value: str) -> str:
    part = PurePosixPath(value)
    if not value or value in {".", ".."} or part.is_absolute() or ".." in part.parts or "\\" in value or ":" in value:
        raise ValueError("expected a safe relative POSIX file path")
    if any(p.lower() in BLOCKED_PARTS for p in part.parts) or part.name.lower() in BLOCKED_NAMES or part.name.lower().startswith(".env."):
        raise ValueError("private/configuration/generated-environment path is not exportable")
    return part.as_posix()


def checked_path(root: Path, relative: str) -> Path:
    relative = safe_relative(relative)
    resolved_root = root.resolve(strict=True)
    path = root.joinpath(*PurePosixPath(relative).parts)
    cursor = root
    for component in PurePosixPath(relative).parts:
        cursor = cursor / component
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise ValueError("symlink/junction is not an ordinary evidence file")
    if not path.resolve().is_relative_to(resolved_root):
        raise ValueError("path escapes the intended root")
    return path


def tree(root: Path) -> dict[str, str]:
    found = {}
    def fail(error):
        raise error
    for current, directories, names in os.walk(root, followlinks=False, onerror=fail):
        for name in directories:
            child = Path(current) / name
            if child.is_symlink() or (hasattr(child, "is_junction") and child.is_junction()):
                raise ValueError("symlink/junction in evidence tree")
        for name in names:
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            checked_path(root, relative)
            found[relative] = sha(path.read_bytes())
    return dict(sorted(found.items()))


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True).stdout


def runtime_blobs(repo: Path, revision: str, runtime_paths: list[str], runtime_root: str) -> tuple[str, dict[str, bytes]]:
    # Blob transport is binary. No archive/export attributes, checkout conversion or text mode.
    commit = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode("ascii").strip()
    result = {}
    prefix = PurePosixPath(safe_relative(runtime_root))
    paths = [(prefix / safe_relative(path)).as_posix() for path in runtime_paths]
    entries = git(repo, "ls-tree", "-rz", commit, "--", *paths).split(b"\0")
    for entry in entries:
        if not entry:
            continue
        metadata, raw_name = entry.split(b"\t", 1)
        mode, kind, object_id = metadata.split(b" ")
        name = PurePosixPath(safe_relative(raw_name.decode("utf-8"))).relative_to(prefix).as_posix()
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            raise ValueError("runtime must contain ordinary Git blobs only")
        result[name] = git(repo, "cat-file", "blob", object_id.decode("ascii"))
    if "SKILL.md" not in result:
        raise ValueError("runtime lacks SKILL.md")
    return commit, result


def method_hashes() -> dict[str, str]:
    files = [HERE / name for name in ("manifest.json", "harness.py", "prepare_reproduction.py", "fixtures.py", "README.md", ".gitattributes")]
    for folder in ("actor", "fixtures", "evaluator"):
        files.extend(p for p in (HERE / folder).rglob("*") if p.is_file())
    return {p.relative_to(HERE).as_posix(): sha(p.read_bytes()) for p in sorted(files)}


def freeze(repo: Path, revision: str, output: Path) -> dict:
    if output.exists():
        raise ValueError("freeze destination already exists; choose a new label")
    manifest = load(HERE / "manifest.json")
    commit, source = runtime_blobs(repo, revision, manifest["runtime_paths"], manifest["runtime_root"])
    output.mkdir(parents=True)
    for name, data in source.items():
        write(output / "runtime" / name, data)
    photo_truth = photo_expectations()
    frozen = {
        "schema_version": 1, "created_utc": stamp(), "source_revision": commit,
        "source_files": {name: {"sha256": sha(data), "bytes": len(data), "crlf_count": data.count(b"\r\n"), "lf_count": data.count(b"\n")} for name, data in sorted(source.items())},
        "source_digest_basis": "Exact git cat-file blob bytes copied via binary transport. git archive not used; no CRLF conversion, export-subst or export-ignore. Runtime snapshot differs from checkout line endings when Git converts them.",
        "method_sha256": method_hashes(), "manifest": manifest,
        "fixture_sha256": photo_truth["sha256"], "photo_expectations_sha256": sha(json_bytes(photo_truth)),
        "preparer_environment": {"python": platform.python_version(), "platform": platform.platform(), "git_version": git(repo, "--version").decode("utf-8").strip()},
    }
    write(output / "freeze.json", json_bytes(frozen))
    write(output / "photo-expectations.evaluator.json", json_bytes(photo_truth))
    return frozen


def validate_freeze(folder: Path) -> dict:
    frozen = load(folder / "freeze.json")
    actual = tree(folder / "runtime")
    expected = {name: item["sha256"] for name, item in frozen["source_files"].items()}
    if actual != expected:
        raise ValueError("frozen runtime bytes changed")
    if method_hashes() != frozen["method_sha256"]:
        raise ValueError("evaluation method changed since freeze; make a new freeze")
    if photo_expectations()["sha256"] != frozen["fixture_sha256"]:
        raise ValueError("fixture bytes changed since freeze")
    if sha((folder / "photo-expectations.evaluator.json").read_bytes()) != frozen["photo_expectations_sha256"]:
        raise ValueError("frozen evaluator fixture expectations changed")
    return frozen


def prepare(frozen_dir: Path, run_id: str, workspace: Path, output: Path) -> dict:
    frozen = validate_freeze(frozen_dir)
    reproduction_input = (HERE / "evaluator/reproduce.md").read_bytes()
    reproduction_input_sha256 = frozen["method_sha256"]["evaluator/reproduce.md"]
    if sha(reproduction_input) != reproduction_input_sha256:
        raise ValueError("reproduction input changed since freeze")
    item = next((item for item in frozen["manifest"]["runs"] if item["id"] == run_id), None)
    if not item:
        raise ValueError("run id must be in the frozen manifest")
    if workspace.exists() or output.exists():
        raise ValueError("workspace/result already exists; preserve prior attempts")
    if workspace.resolve().is_relative_to(output.resolve()) or output.resolve().is_relative_to(workspace.resolve()):
        raise ValueError("actor workspace and operator results must be separate")
    workspace.mkdir(parents=True)
    output.mkdir(parents=True)
    shutil.copytree(frozen_dir / "runtime", workspace / "skill")
    write(workspace / "project" / "existing-product.txt", b"Existing product sentinel: preserve exact bytes.\r\n")
    if item["case"] == "photos":
        for name, value in photo_files().items():
            write(workspace / "project" / "inputs" / name, value)
        write(workspace / "project" / "inputs" / "README.md", (HERE / "fixtures/photos-readme.md").read_bytes())
        write(workspace / "project" / "inputs.sha256.json", json_bytes(tree(workspace / "project/inputs")))
    else:
        write(workspace / "project" / "README.md", "# 공개 기상 데이터 연구\n\n이 프로젝트는 비밀키나 기존 데이터가 없는 로컬 연구 작업장이다.\n".encode("utf-8"))
    request = (HERE / "actor" / item["case"] / "request.md").read_text(encoding="utf-8")
    text = (HERE / "actor/session.md").read_text(encoding="utf-8").replace("{{request}}", request)
    write(workspace / "input.md", text.encode("utf-8"))
    (workspace / "records").mkdir()
    initial = tree(workspace)
    record = {
        "schema_version": 1, "run_id": run_id, "case": item["case"], "sample": item["sample"], "prepared_utc": stamp(),
        "source_revision": frozen["source_revision"], "freeze_sha256": sha((frozen_dir / "freeze.json").read_bytes()),
        "source_sha256": {name: meta["sha256"] for name, meta in frozen["source_files"].items()},
        "workspace_initial_sha256": initial,
        "reproduction_input_sha256": reproduction_input_sha256,
        "model_requested": frozen["manifest"]["model_requested"], "reasoning_effort_requested": frozen["manifest"]["reasoning_effort_requested"],
        "model_observed": None, "reasoning_effort_observed": None,
        "session_limits": frozen["manifest"]["session_limits"],
        "input_digest_basis": "SHA-256 of exact UTF-8 input.md bytes. Native tool wire bytes/model internal normalization are not observed.",
        "product_protection": "separate generated workspace and prompt boundary; no technical sandbox or ACL isolation claimed",
        "status": "prepared_not_started", "tokens": None,
    }
    write(output / "preparation.json", json_bytes(record))
    # Evaluator-only snapshot. Never copy this into the actor workspace.
    write(output / "reproduction-input.md", reproduction_input)
    write(output / "input.md", (workspace / "input.md").read_bytes())
    write(output / "answers.md", (HERE / "actor" / item["case"] / "answers.md").read_bytes())
    write(output / "continuation.md", (HERE / "actor/continuation.md").read_bytes())
    write(output / "close.md", (HERE / "actor/close.md").read_bytes())
    write(output / "observer-template.json", (HERE / "evaluator/observation-template.json").read_bytes().replace(b"REPLACE_WITH_RUN_ID", run_id.encode("ascii")))
    return record


def event(output: Path, source: str, kind: str, detail: str, evidence: list[str]) -> dict:
    load(output / "preparation.json")
    if source not in {"actor_record", "observer_event"}:
        raise ValueError("record source must distinguish author from observer")
    record = {"recorded_utc": stamp(), "source": source, "kind": kind, "detail": detail, "evidence": evidence}
    with (output / "events.jsonl").open("ab") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
    return record


def export(workspace: Path, output: Path, allowlist: list[str], destination: Path) -> dict:
    preparation = load(output / "preparation.json")
    if not isinstance(allowlist, list) or not all(isinstance(item, str) for item in allowlist):
        raise ValueError("allowlist must be a JSON array of relative file paths")
    if destination.exists():
        raise ValueError("export already exists; use a new destination")
    if destination.resolve().is_relative_to(workspace.resolve()):
        raise ValueError("export must be outside the actor workspace")
    destination.mkdir(parents=True)
    files, errors, seen = {}, [], set()
    for name in allowlist:
        try:
            name = safe_relative(name)
            if name in seen:
                raise ValueError("duplicate allowlist item")
            seen.add(name)
            path = checked_path(workspace, name)
            if not path.is_file():
                raise ValueError("not a readable regular file")
            if path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("exceeds 32 MiB publication bound; publish a reviewed subset separately")
            with path.open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise ValueError("file grew beyond the 32 MiB publication bound")
            write(destination / "artifacts" / name, data)
            files[name] = {"source_sha256": sha(data), "published_sha256": sha(data), "bytes": len(data), "transformation": "none; byte copy"}
        except (OSError, ValueError) as error:
            # Do not log host absolute paths from OS exception messages.
            public_name = "<invalid-relative-path>" if "\\" in name or ":" in name or name.startswith("/") else name
            errors.append({"path": public_name, "error_type": type(error).__name__, "reason": str(error) if isinstance(error, ValueError) else "file read or publication write failed"})
    reproduction_input = {
        "path": "reproduction-input.md", "source": "operator snapshot fixed at run preparation",
        "expected_sha256": preparation.get("reproduction_input_sha256"),
        "published_sha256": None, "status": "unavailable",
    }
    try:
        data = checked_path(output, "reproduction-input.md").read_bytes()
        if sha(data) != reproduction_input["expected_sha256"]:
            raise ValueError("prepared reproduction input hash mismatch; no current-method fallback")
        write(destination / "reproduction-input.md", data)
        reproduction_input.update(published_sha256=sha(data), status="copied_fixed_input")
    except (OSError, ValueError) as error:
        errors.append({"path": "reproduction-input.md", "error_type": type(error).__name__,
                       "reason": str(error) if isinstance(error, ValueError) else "fixed reproduction input could not be collected; no current-method fallback"})
    protected = {}
    for name, before in preparation["workspace_initial_sha256"].items():
        try:
            path = checked_path(workspace, name)
            after = sha(path.read_bytes())
            protected[name] = {"before": before, "after": after, "unchanged": before == after}
        except (OSError, ValueError) as error:
            protected[name] = {"before": before, "after": None, "unchanged": False, "error_type": type(error).__name__}
    report = {
        "schema_version": 1, "exported_utc": stamp(), "run_id": preparation["run_id"],
        "status": "complete_allowlist_copy" if not errors else "partial_collection",
        "scope": "explicit operator-reviewed files only; not a complete host trace or automatic privacy audit",
        "files": files, "errors": errors, "initial_files": protected,
        "reproduction_input": reproduction_input,
        "initial_files_unchanged": all(item["unchanged"] for item in protected.values()),
        "source_workspace_cleanup": "not_attempted; retained for audit/recovery",
    }
    write(destination / "export.json", json_bytes(report))
    return report


def verify(folder: Path) -> dict:
    record = load(folder / "export.json")
    expected = {name: item["published_sha256"] for name, item in record["files"].items()}
    try:
        actual = tree(folder / "artifacts") if (folder / "artifacts").exists() else {}
        mismatch = sorted(name for name in expected.keys() | actual.keys() if expected.get(name) != actual.get(name))
    except (OSError, ValueError) as error:
        mismatch = ["unreadable_or_unsafe_artifact_tree:" + type(error).__name__]
    reproduction_input = record.get("reproduction_input", {})
    try:
        data = checked_path(folder, "reproduction-input.md").read_bytes()
        actual_prompt_sha256 = sha(data)
        if (reproduction_input.get("status") != "copied_fixed_input"
                or actual_prompt_sha256 != reproduction_input.get("expected_sha256")
                or actual_prompt_sha256 != reproduction_input.get("published_sha256")):
            mismatch.append("reproduction-input.md")
    except (OSError, ValueError):
        mismatch.append("reproduction-input.md")
    return {"status": "verified" if not mismatch else "mismatch", "files": len(expected), "mismatch": mismatch,
            "collection_status": record["status"], "initial_files_unchanged": record["initial_files_unchanged"]}


def reproduce(export_dir: Path, workspace: Path, materials: list[str] | None = None) -> dict:
    from prepare_reproduction import prepare, withheld_record
    if verify(export_dir)["status"] != "verified":
        raise ValueError("export integrity failed")
    if materials is None:
        # Compatibility default remains a safe subset; explicit reviewed
        # selections are preferable for real runs. Archives are checked by prepare.
        materials = [name for name in load(export_dir / "export.json")["files"]
                     if name.startswith("project/") and not withheld_record(name)]
    result = prepare(export_dir, workspace, materials)
    return {**result, "input_sha256": result["reproduction_input_sha256"],
            "project_sha256": tree(workspace / "project"), "collection_status": "complete_allowlist_copy"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("freeze")
    p.add_argument("--repo", type=Path, default=HERE.parents[1])
    p.add_argument("--revision", required=True)
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--run", required=True)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("event")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source", choices=["actor_record", "observer_event"], required=True)
    p.add_argument("--kind", required=True)
    p.add_argument("--detail", required=True)
    p.add_argument("--evidence", nargs="*", default=[])
    p = commands.add_parser("export")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--allowlist", type=Path, required=True, help="JSON array of manually reviewed relative file paths")
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("verify")
    p.add_argument("--export", type=Path, required=True)
    p = commands.add_parser("reproduce-prepare")
    p.add_argument("--export", type=Path, required=True)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--materials", type=Path, help="Reviewed project-file JSON list; defaults to project files without activity/replay records")
    args = parser.parse_args()
    if args.command == "freeze":
        result = freeze(args.repo, args.revision, args.out)
    elif args.command == "prepare":
        result = prepare(args.freeze, args.run, args.workspace, args.out)
    elif args.command == "event":
        result = event(args.out, args.source, args.kind, args.detail, args.evidence)
    elif args.command == "export":
        result = export(args.workspace, args.run, load(args.allowlist), args.out)
    elif args.command == "verify":
        result = verify(args.export)
    else:
        result = reproduce(args.export, args.workspace, load(args.materials) if args.materials else None)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    if result.get("status") in {"mismatch", "partial_collection"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
