"""Independent reproduction helpers; read only the supplied project materials."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "project"
RUN = ROOT / "run" / "project"
EVIDENCE = ROOT / "evidence"


def inventory():
    return {
        path.relative_to(PROJECT).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(PROJECT.rglob("*")) if path.is_file()
    }


def save(name, value):
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare():
    if RUN.exists():
        raise RuntimeError("Fresh execution copy already exists")
    baseline = inventory()
    save("original-before.json", baseline)
    shutil.copytree(PROJECT, RUN)
    lab = RUN / ".elenchus" / "lab" / "R002"
    if (lab / "output").exists():
        (lab / "output").rename(lab / "provided-output")
    alt = lab / "alternative-research"
    provided = alt / "provided-output"
    provided.mkdir()
    for name in ["observations.sqlite3", "archive-results.json", "query-48h.json", "failure-results.json", "pandas-results.json", "ghcnh-probe-results.json"]:
        if (alt / name).exists():
            (alt / name).rename(provided / name)
    manifest = json.loads((PROJECT / ".elenchus" / "material-manifest.json").read_text(encoding="utf-8"))
    missing = []
    mismatch = []
    matched = 0
    for entry in manifest["files"]:
        name = ".elenchus/" + entry["path"]
        if name not in baseline:
            missing.append(entry["path"])
        elif baseline[name] != {"bytes": entry["bytes"], "sha256": entry["sha256"]}:
            mismatch.append(entry["path"])
        else:
            matched += 1
    result = {"project_files": len(baseline), "execution_copy": str(RUN), "manifest_entries": len(manifest["files"]), "manifest_matching_files": matched, "manifest_missing_files": missing, "manifest_mismatched_files": mismatch, "product_source_edits": 0}
    save("preparation.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run(label, relative_cwd, command):
    cwd = (ROOT / relative_cwd).resolve()
    cwd.relative_to(ROOT)
    if cwd == PROJECT or PROJECT in cwd.parents:
        raise RuntimeError("Commands may not mutate the original project")
    command = list(command)
    if not Path(command[0]).is_absolute() and ("/" in command[0] or "\\" in command[0]):
        command[0] = str((cwd / command[0]).resolve())
    started = datetime.now(timezone.utc).isoformat()
    process = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / f"{label}.stdout.txt").write_bytes(process.stdout)
    (EVIDENCE / f"{label}.stderr.txt").write_bytes(process.stderr)
    record = {"label": label, "started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(), "cwd": str(cwd), "argv": command, "exit_code": process.returncode, "stdout": f"evidence/{label}.stdout.txt", "stderr": f"evidence/{label}.stderr.txt"}
    with (EVIDENCE / "commands.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.stdout.buffer.write(process.stdout)
    sys.stderr.buffer.write(process.stderr)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return process.returncode


def finish():
    before = json.loads((EVIDENCE / "original-before.json").read_text(encoding="utf-8"))
    after = inventory()
    changed = [name for name in before.keys() & after.keys() if before[name] != after[name]]
    result = {"files_before": len(before), "files_after": len(after), "changed_files": changed, "removed_files": sorted(before.keys() - after.keys()), "added_files": sorted(after.keys() - before.keys()), "all_original_files_unchanged": before == after}
    save("original-after.json", after)
    save("preservation.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare()
    elif sys.argv[1] == "finish":
        finish()
    elif sys.argv[1] == "run":
        sys.exit(run(sys.argv[2], sys.argv[3], sys.argv[4:]))
    else:
        raise ValueError("Unknown runner action")
