"""Run the eight explicitly untimed comparisons; operator review controls completion."""
import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import runner

ORDER = [
    ("baseline", "casino", 1), ("candidate-v2", "casino", 1),
    ("candidate-v2", "photo-organizer", 1), ("baseline", "photo-organizer", 1),
    ("baseline", "photo-organizer", 2), ("candidate-v2", "photo-organizer", 2),
    ("candidate-v2", "casino", 2), ("baseline", "casino", 2),
]


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True)
    args = parser.parse_args()
    folder = ROOT / "untimed"
    destination = folder / "execution.json"
    if destination.exists():
        raise FileExistsError("This batch already has an execution record; do not overwrite it")
    snapshots = {}
    for label in ("baseline", "candidate-v2"):
        snapshot = json.loads((ROOT / "snapshots" / f"{label}.json").read_text(encoding="utf-8"))
        runner.verify_snapshot(snapshot)
        snapshots[label] = snapshot
    record = {
        "kind": "untimed_basic_comparison", "started_utc": datetime.now(timezone.utc).isoformat(),
        "max_seconds": None, "max_responses": None, "max_concurrent_subprocesses": 2,
        "operator_review_after_preferences": True, "order": ORDER, "snapshots": snapshots,
        "runner_sha256": runner.sha((ROOT / "runner.py").read_bytes()),
        "batch_sha256": runner.sha(Path(__file__).read_bytes()),
        "protocol_sha256": runner.sha((folder / "protocol.md").read_bytes()),
        "model": runner.MANIFEST["model"], "reasoning_effort": runner.MANIFEST["reasoning_effort"],
        "status": "running", "results": [],
    }
    runner.write_json(destination, record)
    redactor = runner.Redactor({str(runner.REPO): "<repository>", str(Path.home()): "<user>"})

    def execute(spec):
        label, case, sample = spec
        command = [sys.executable, "-B", str(ROOT / "runner.py"), "run", "--snapshot",
                   str(ROOT / "snapshots" / f"{label}.json"), "--label", f"untimed-{label}",
                   "--case", case, "--sample", str(sample), "--cli", args.cli,
                   "--no-time-limit", "--max-responses", "0", "--operator-review"]
        result = subprocess.run(command, cwd=runner.REPO, capture_output=True, encoding="utf-8",
                                errors="replace", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        item = {"source": label, "case": case, "sample": sample, "process_exit_code": result.returncode,
                "command": redactor.apply(command), "finished_utc": datetime.now(timezone.utc).isoformat(),
                "stdout": redactor.text(result.stdout), "stderr": redactor.text(result.stderr)}
        runner.write_json(folder / f"process-{label}-{case}-{sample}.json", item)
        print(json.dumps({key: item[key] for key in ("source", "case", "sample", "process_exit_code")}), flush=True)
        return item

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(execute, spec) for spec in ORDER]
        for future in concurrent.futures.as_completed(futures):
            record["results"].append(future.result())
            runner.write_json(destination, record)
    record.update({"status": "processes_finished", "finished_utc": datetime.now(timezone.utc).isoformat(),
                   "quality_verdict": "requires_per_sample_manual_review"})
    runner.write_json(destination, record)
    if any(item["process_exit_code"] for item in record["results"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
