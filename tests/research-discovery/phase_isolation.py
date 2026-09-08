#!/usr/bin/env python3
"""One-response Research-ready diagnostic, separate from the main comparisons."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time

import runner

DIAG = runner.HERE / "phase-isolation"
SNAPSHOTS = {"baseline": runner.HERE / "snapshots/baseline.json",
             "candidate-v2": runner.HERE / "snapshots/candidate-v2.json"}
CASES = ["casino", "photo-organizer"]
CONTEXT = ("같은 프로젝트의 이전 assistant 응답은 [Elenchus · 진행 중]이었습니다. 최초 Release 확인은 "
           "완료됐고 현재 버전 사용이 선택됐습니다. 원래 요청의 상위 구성과 범위에 대한 Topology 확인과 "
           "해당 범위의 Research 진행은 이미 끝난 사용자 결정입니다. 현재 단계는 Research입니다. "
           "아래 최초 요구와 선호 답변은 이 대화에서 이미 받은 실제 입력이며, 아직 열린 제품 선택은 미정입니다.")


def inputs(case: str) -> tuple[str, str]:
    original = (runner.HERE / "fixtures" / case / "request.md").read_text(encoding="utf-8")
    preferences = (runner.HERE / "fixtures" / case / "preferences.md").read_text(encoding="utf-8")
    prompt = (CONTEXT + "\n\n## 최초 사용자 요구\n" + original + "\n## 이미 받은 사용자 선호 답변\n" + preferences
              + "\n## 현재 사용자 요청\n이미 요청한 범위의 Research를 진행해 조사 결과를 알려 주세요. "
              "이번 대화는 Research 결론까지이며 전체 Execution 계획의 합의는 다음에 합니다.\n")
    idea = ("# Idea\n상태: 작성 중\n현재 단계: Research\nTopology: 원래 요청의 상위 구성과 범위에 대한 사용자 확인 완료.\n"
            "Research 진행: 현재 대화에서 해당 범위가 이미 허용됨.\n\n## 최초 사용자 요구\n" + original
            + "\n## 이미 받은 사용자 선호 답변\n" + preferences)
    return prompt, idea


def frozen_record() -> dict:
    snapshots = {}
    for label, path in SNAPSHOTS.items():
        value = json.loads(path.read_text(encoding="utf-8"))
        runner.verify_snapshot(value)
        snapshots[label] = value
    cases = {}
    for case in CASES:
        prompt, idea = inputs(case)
        corpus = runner.tree_hashes(runner.HERE / "fixtures" / case / "evidence")
        cases[case] = {"combined_input_sha256": runner.sha(prompt.encode("utf-8")),
                       "idea_seed_sha256": runner.sha(idea.encode("utf-8")),
                       "request_sha256": runner.sha((runner.HERE / "fixtures" / case / "request.md").read_bytes()),
                       "preferences_sha256": runner.sha((runner.HERE / "fixtures" / case / "preferences.md").read_bytes()),
                       "corpus_hashes": corpus}
    return {"kind": "phase_isolation_diagnostic", "not_primary_comparison": True,
            "model": runner.MANIFEST["model"], "reasoning_effort": runner.MANIFEST["reasoning_effort"],
            "max_responses": 1, "max_seconds": 600, "max_concurrent_subprocesses": 2,
            "source_snapshots": snapshots, "cases": cases,
            "script_sha256": runner.sha(Path(__file__).read_bytes()),
            "shared_runner_sha256": runner.sha((runner.HERE / "runner.py").read_bytes()),
            "protocol_sha256": runner.sha((DIAG / "protocol.md").read_bytes())}


def freeze() -> Path:
    value = frozen_record()
    destination = DIAG / "frozen.json"
    if destination.exists() and json.loads(destination.read_text(encoding="utf-8")) != value:
        raise FileExistsError("Diagnostic is already frozen with different bytes")
    runner.write_json(destination, value)
    for case in CASES:
        prompt, idea = inputs(case)
        folder = DIAG / "prepared-inputs" / case
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "input.md").write_text(prompt, encoding="utf-8", newline="")
        (folder / "idea.md").write_text(idea, encoding="utf-8", newline="")
    return destination


def verify() -> dict:
    frozen = json.loads((DIAG / "frozen.json").read_text(encoding="utf-8"))
    if frozen != frozen_record():
        raise ValueError("Diagnostic source, inputs, protocol, or harness changed after freeze")
    return frozen


def run_one(label: str, case: str, cli: str, frozen: dict) -> dict:
    source_snapshot = frozen["source_snapshots"][label]
    source = runner.verify_snapshot(source_snapshot)
    output = DIAG / "results" / f"{label}-{case}"
    output.mkdir(parents=True, exist_ok=False)
    temporary = Path(tempfile.mkdtemp(prefix=f"elenchus-research-eval-phase-{case}-")).resolve()
    runner.under(Path(tempfile.gettempdir()), temporary)
    project = temporary / "project"
    project.mkdir()
    redactor = runner.Redactor({str(project): "<fixture>", str(temporary): "<diagnostic-temp>",
                                str(Path.home()): "<user>", str(runner.REPO): "<repository>"})
    summary = {"kind": "phase_isolation_diagnostic", "status": "running", "source_label": label, "case": case,
               "source_revision": source_snapshot["revision"], "source_sha256": source_snapshot["source_sha256"],
               "source_files": source_snapshot["files"], "model": frozen["model"], "reasoning_effort": frozen["reasoning_effort"],
               "limits": {"max_seconds": 600, "max_responses": 1},
               "preparation_sha256": runner.sha((DIAG / "frozen.json").read_bytes()),
               "digest_basis": runner.DIGEST_BASIS,
               "started_utc": datetime.now(timezone.utc).isoformat(), "quality_verdict": "not_automatically_graded",
               "temporary_workspace": "<os-temp>/" + temporary.name}
    runner.write_json(output / "summary.json", summary)
    print(json.dumps({"started": output.name, "source_revision": source_snapshot["revision"]}, ensure_ascii=True), flush=True)
    try:
        summary["host_read_setup"] = runner.prepare_host_read(project)
        runner.prepare_project(project, source, case)
        prompt, idea = inputs(case)
        (project / ".elenchus").mkdir()
        (project / ".elenchus/idea.md").write_text(idea, encoding="utf-8", newline="")
        before = runner.tree_hashes(project)
        summary["initial_files"] = before
        summary["input_sha256"] = runner.sha(prompt.encode("utf-8"))
        summary["idea_seed_sha256"] = runner.sha(idea.encode("utf-8"))
        runner.write_utf8(output / "input.md", prompt)
        summary["published_input_sha256"] = runner.sha((output / "input.md").read_bytes())
        final = temporary / "final.md"
        command = runner.cli_command(cli, project, final, frozen["model"], frozen["reasoning_effort"])
        summary["cli_version"] = subprocess.run([cli, "--version"], capture_output=True,
                                                 encoding="utf-8", errors="replace", check=False).stdout.strip()
        started = time.monotonic()
        result = runner.call_cli(command, prompt, frozen["max_seconds"])
        events, excluded = runner.public_events(result.pop("stdout"), redactor)
        runner.write_utf8(output / "stderr.txt", redactor.text(result.pop("stderr")))
        event_bytes = "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events).encode("utf-8")
        (output / "events.jsonl").write_bytes(event_bytes)
        answer = final.read_text(encoding="utf-8", errors="replace") if final.exists() else ""
        if not answer:
            visible = [event["item"].get("text", "") for event in events if event.get("type") == "item.completed"
                       and event.get("item", {}).get("type") == "agent_message"]
            answer = visible[-1] if visible else ""
        published = redactor.text(answer)
        runner.write_utf8(output / "answer.md", published)
        status = "timeout" if result["timed_out"] else "cli_error" if result["exit_code"] != 0 or any(
            event.get("type") == "turn.failed" for event in events) else "response_observed" if answer else "empty_response"
        summary.update({**result, "status": status, "elapsed_seconds": round(time.monotonic() - started, 3),
                        "command": redactor.apply(command), "excluded_event_types": excluded,
                        "answer_sha256": runner.sha(answer.encode("utf-8")), "published_answer_sha256": runner.sha((output / "answer.md").read_bytes()),
                        "events_sha256": runner.sha(event_bytes),
                        "usage": [event["usage"] for event in events if event.get("type") == "turn.completed" and "usage" in event],
                        "tool_calls": sum(event.get("type") == "item.completed" and event.get("item", {}).get("type") in
                                          {"command_execution", "file_change", "mcp_tool_call", "web_search"} for event in events)})
        try:
            after = runner.tree_hashes(project)
            summary.update({"artifact_collection": "complete", "artifacts": runner.collect_artifacts(project, output, redactor),
                            "final_files": after, "product_unchanged": before["app.txt"] == after.get("app.txt"),
                            "file_changes": [{"path": name, "before": before.get(name), "after": after.get(name)}
                                             for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]})
        except OSError as error:
            summary.update({"artifact_collection": "incomplete", "artifacts": None, "product_unchanged": None,
                            "collection_error": redactor.text(str(error))})
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    except BaseException as error:
        summary.update({"host_infrastructure_error": redactor.text(str(error))})
        if summary["status"] == "running":
            summary["status"] = "infrastructure_error"
    finally:
        runner.write_json(output / "summary.json", summary)
        if summary.get("artifact_collection") != "complete" or summary.get("host_infrastructure_error"):
            summary["cleanup"] = {"status": "skipped_preserve_incomplete_evidence", "retained_temp": "<os-temp>/" + temporary.name}
        else:
            summary["cleanup"] = redactor.apply(runner.cleanup_temporary(temporary))
        runner.write_json(output / "summary.json", summary)
    result_line = {"result": output.name, "status": summary["status"], "elapsed_seconds": summary.get("elapsed_seconds"),
                   "artifact_collection": summary.get("artifact_collection"), "cleanup": summary["cleanup"]["status"]}
    print(json.dumps(result_line, ensure_ascii=True), flush=True)
    return result_line


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("freeze")
    run = sub.add_parser("run")
    run.add_argument("--cli", default="codex")
    args = parser.parse_args()
    if args.command == "freeze":
        print(str(freeze()))
        return
    frozen = verify()
    outcomes = []
    with ThreadPoolExecutor(max_workers=frozen["max_concurrent_subprocesses"]) as pool:
        futures = [pool.submit(run_one, label, case, args.cli, frozen) for case in CASES for label in SNAPSHOTS]
        for future in as_completed(futures):
            outcomes.append(future.result())
    runner.write_json(DIAG / "run-index.json", {"kind": "phase_isolation_diagnostic", "outcomes": outcomes,
                                              "finished_utc": datetime.now(timezone.utc).isoformat(), "semantic_grading": "not_performed"})


if __name__ == "__main__":
    main()
