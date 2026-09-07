#!/usr/bin/env python3
"""Check/fix published-file digest metadata without changing evidence or frozen inputs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import runner


def update_fields(summary: dict, root: Path) -> list[dict]:
    updates = []

    def assign(container, key, value, pointer):
        old = container.get(key)
        if old != value:
            updates.append({"field": pointer + key, "before": old, "after": value,
                            "kind": "added" if key not in container else "corrected"})
            container[key] = value

    turns = summary.get("turns", [])
    records = [(f"turns[{index}].", turn, root / f'turn-{turn["number"]:02d}') for index, turn in enumerate(turns)]
    if not records:
        records = [("", summary, root)]
    has_publication = False
    for pointer, record, folder in records:
        mappings = [("input.md", "published_input_sha256"), ("answer.md", "published_answer_sha256"),
                    ("events.jsonl", "published_events_sha256" if turns else "events_sha256")]
        for filename, field in mappings:
            path = folder / filename
            runner.under(root, path)
            if path.exists():
                has_publication = True
                assign(record, field, runner.sha(path.read_bytes()), pointer)
    for name, metadata in (summary.get("artifacts") or {}).items():
        path = root / "artifacts" / name
        runner.under(root, path)
        if metadata.get("published") and path.exists():
            assign(metadata, "published_sha256", runner.sha(path.read_bytes()), f"artifacts[{name}].")
    if has_publication:
        assign(summary, "digest_basis", runner.DIGEST_BASIS, "")
    return updates


def protected_inputs() -> dict[str, str]:
    paths = [runner.HERE / "manifest.json", runner.HERE / "fixtures", runner.HERE / "snapshots",
             *[runner.HERE / "targeted" / name for name in ("manifest.json", "fixtures.json", "protocol.md", "frozen.json", "preparations")],
             *[runner.HERE / "phase-isolation" / name for name in ("protocol.md", "frozen.json", "prepared-inputs")]]
    result = {}
    for path in paths:
        if not path.exists():
            continue
        for item in ([path] if path.is_file() else runner.regular_files(path)):
            result[item.relative_to(runner.HERE).as_posix()] = runner.sha(item.read_bytes())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Correct metadata only and save before/after audit")
    args = parser.parse_args()
    protected_before = protected_inputs()
    audit = []
    mismatches = 0
    additions = 0
    evidence_count = 0
    for results in (runner.HERE / "results", runner.HERE / "targeted/results", runner.HERE / "phase-isolation/results"):
        for path in sorted(results.glob("*/summary.json")):
            root = path.parent
            original_bytes = path.read_bytes()
            summary = json.loads(original_bytes.decode("utf-8"))
            preserved_text_digests = [(item.get("input_sha256"), item.get("answer_sha256"))
                                      for item in [summary, *summary.get("turns", [])]]
            evidence_before = {item.relative_to(root).as_posix(): runner.sha(item.read_bytes())
                               for item in runner.regular_files(root) if item != path}
            updates = update_fields(summary, root)
            mismatches += sum(update["kind"] == "corrected" and update["field"] != "digest_basis" for update in updates)
            additions += sum(update["kind"] == "added" for update in updates)
            assert preserved_text_digests == [(item.get("input_sha256"), item.get("answer_sha256"))
                                              for item in [summary, *summary.get("turns", [])]]
            if args.apply and updates:
                runner.write_json(path, summary)
                audit.append({"metadata": path.relative_to(runner.HERE).as_posix(), "before_sha256": runner.sha(original_bytes),
                              "after_sha256": runner.sha(path.read_bytes()), "updates": updates})
            evidence_after = {item.relative_to(root).as_posix(): runner.sha(item.read_bytes())
                              for item in runner.regular_files(root) if item != path}
            if evidence_before != evidence_after:
                raise RuntimeError("Evidence bytes changed during metadata-only correction")
            evidence_count += len(evidence_before)
    if protected_before != protected_inputs():
        raise RuntimeError("Frozen source/input bytes changed during metadata-only correction")
    report = {"kind": "published_digest_metadata_correction", "recorded_utc": datetime.now(timezone.utc).isoformat(),
              "mismatched_existing_fields": mismatches, "new_metadata_fields": additions,
              "evidence_files_checked_unchanged": evidence_count, "frozen_source_input_files_checked_unchanged": len(protected_before),
              "protected_inputs_sha256": runner.sha(runner.canonical(protected_before)),
              "input_and_answer_text_digests_preserved": True, "model_wire_bytes_or_internal_normalization_claimed": False,
              "corrections": audit}
    if args.apply:
        output = runner.HERE / "infrastructure" / f"publication-digest-audit-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
        runner.write_json(output, report)
        report = {key: value for key, value in report.items() if key != "corrections"}
        report["audit"] = str(output)
    print(json.dumps(report, ensure_ascii=True))
    if not args.apply and mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
