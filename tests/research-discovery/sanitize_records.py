#!/usr/bin/env python3
"""Redact already-published paths; preserve original digests and model evidence hashes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import runner

ORIGINAL_RUNS = ["baseline-casino-sample1", "candidate-v1-casino-sample1",
                 "baseline-photo-organizer-sample1", "candidate-v1-photo-organizer-sample1"]


def sanitize_run(name: str, audit: list[dict]) -> None:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        raise ValueError("Use plain result directory names")
    root = runner.HERE / "results" / name
    runner.under(runner.HERE / "results", root)
    redactor = runner.Redactor({str(Path.home()): "<user>", str(runner.REPO): "<repository>"})
    before = runner.tree_hashes(root)
    for path in runner.regular_files(root):
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        ending = "\r\n" if b"\r\n" in raw else "\n"
        if path.suffix == ".jsonl":
            parsed = [json.loads(line) for line in text.splitlines() if line.strip()]
            clean = redactor.apply(parsed)
            if clean == parsed:
                continue
            updated = ending.join(json.dumps(event, ensure_ascii=False) for event in clean) + ending
        elif path.suffix == ".json":
            parsed = json.loads(text)
            clean = redactor.apply(parsed)
            if clean == parsed:
                continue
            updated = (json.dumps(clean, ensure_ascii=False, indent=2) + "\n").replace("\n", ending)
        else:
            updated = redactor.text(text)
        if updated != text:
            path.write_bytes(updated.encode("utf-8"))
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for turn in summary.get("turns", []):
        folder = root / f'turn-{turn["number"]:02d}'
        for filename, field in (("input.md", "published_input_sha256"), ("answer.md", "published_answer_sha256"),
                                ("events.jsonl", "published_events_sha256")):
            if (folder / filename).exists():
                turn[field] = runner.sha((folder / filename).read_bytes())
    for relative, metadata in (summary.get("artifacts") or {}).items():
        artifact = root / "artifacts" / relative
        if metadata.get("published") and artifact.exists():
            metadata["published_sha256"] = runner.sha(artifact.read_bytes())
    summary["publication_note"] = "User-path redaction strengthened; original input/answer/source hashes preserved. See infrastructure/publication-redaction audit."
    runner.write_json(summary_path, summary)
    after = runner.tree_hashes(root)
    for relative in sorted(before):
        if before[relative] != after[relative]:
            audit.append({"file": f"results/{name}/{relative}", "before_sha256": before[relative],
                          "after_sha256": after[relative], "change": "path redaction or published-hash metadata update"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names", nargs="+", default=ORIGINAL_RUNS)
    args = parser.parse_args()
    audit = []
    for name in args.names:
        sanitize_run(name, audit)
    path = runner.HERE / "infrastructure" / f"publication-redaction-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    runner.write_json(path, {"kind": "publication-only-redaction", "recorded_utc": datetime.now(timezone.utc).isoformat(),
                            "runs": args.names, "not_model_input_corruption": True,
                            "original_model_input_answer_source_hashes_preserved": True, "files": audit})
    print(json.dumps({"changed_files": len(audit), "audit": str(path)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
