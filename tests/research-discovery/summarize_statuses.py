#!/usr/bin/env python3
"""Summarize recorded core execution/collection facts, without semantic grading."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

import runner


def collect() -> dict:
    rows, errors = [], []
    for path in sorted((runner.HERE / "results").glob("*/summary.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append({"result": path.parent.name, "error_type": type(error).__name__})
            continue
        if value.get("kind") != "controlled":
            continue
        turns = value.get("turns", [])
        collection = value.get("artifact_collection", "not_recorded")
        artifacts = value.get("artifacts")
        rows.append({
            "result": path.parent.name,
            "source_label": value.get("snapshot", {}).get("label"),
            "source_revision": value.get("snapshot", {}).get("revision"),
            "case": value.get("case"), "sample": value.get("sample"),
            "recorded_status": value.get("status", "not_recorded"),
            "response_count": len(turns), "elapsed_seconds": value.get("elapsed_seconds"),
            "last_model_process_exit_code": turns[-1].get("exit_code") if turns else None,
            "artifact_collection": collection,
            "artifact_count": len(artifacts) if isinstance(artifacts, dict) else None,
            "artifact_bytes": sum(item.get("bytes", 0) for item in artifacts.values()) if isinstance(artifacts, dict) else None,
            "product_unchanged_observed": value.get("product_unchanged") if collection == "complete" else None,
            "cleanup_status": value.get("cleanup_status", value.get("cleanup", {}).get("status", "not_recorded")),
            "retained_temp_recorded": bool(value.get("retained_temp")),
            "collection_warning_count": len(value.get("collection_warnings", [])),
            "collection_error_recorded": "collection_error" in value,
            "host_error_recorded": "host_infrastructure_error" in value,
            "runner_sha256": value.get("runner_sha256"),
        })
    return {"kind": "execution_and_collection_inventory", "as_of_utc": datetime.now(timezone.utc).isoformat(),
            "semantic_grading": "not_performed", "read_errors": errors, "rows": rows,
            "totals": {"recorded_runs": len(rows),
                       "statuses": dict(Counter(row["recorded_status"] for row in rows)),
                       "collection": dict(Counter(row["artifact_collection"] for row in rows)),
                       "cleanup": dict(Counter(row["cleanup_status"] for row in rows))},
            "limits": ["Only existing recorded result directories are counted; missing planned runs are not inferred to have executed.",
                       "A timeout with complete collection remains an observed timeout, not a quality pass.",
                       "The original non-strict collector's missing collection status is not proof of absent documents or unchanged files.",
                       "Outer wrapper errors absent from summary.json require the separate infrastructure records."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write a timestamped-in-content JSON inventory to this path")
    parser.add_argument("--require-finished", action="store_true", help="Exit 2 when a recorded run is still running or unreadable")
    args = parser.parse_args()
    report = collect()
    if args.output:
        runner.write_json(args.output, report)
    print(json.dumps(report if not args.output else {"output": str(args.output), **report["totals"]}, ensure_ascii=True))
    if args.require_finished and (report["read_errors"] or any(row["recorded_status"] == "running" for row in report["rows"])):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
