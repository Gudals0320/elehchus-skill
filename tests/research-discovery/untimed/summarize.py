"""Read-only aggregation of the eight untimed runs; no model calls or grading."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    execution = json.loads((HERE / "execution.json").read_text(encoding="utf-8"))
    assert execution["status"] == "processes_finished"
    assert len(execution["results"]) == 8
    rows = []
    for source, case, sample in execution["order"]:
        name = f"untimed-{source}-{case}-sample{sample}"
        folder = ROOT / "results" / name
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        assessment = json.loads((HERE / "assessments" / f"{name}.json").read_text(encoding="utf-8"))
        assert summary["limits"] == {"max_responses": None, "max_seconds": None}
        assert summary["operator_outcome"] == assessment["execution_outcome"] == "research_result_delivered"
        assert summary["artifact_collection"] == "complete"
        assert summary["product_unchanged"] and not summary["out_of_plan_changes"]
        assert not assessment["remaining_checks"]
        usage = []
        for turn in summary["turns"]:
            td = folder / f"turn-{turn['number']:02d}"
            assert turn["exit_code"] == 0 and not turn["timed_out"]
            for file, key in (("input.md", "published_input_sha256"), ("answer.md", "published_answer_sha256"), ("events.jsonl", "published_events_sha256")):
                assert digest(td / file) == turn[key], (name, file)
            for file, info in turn["artifacts"].items():
                assert info["published"] and digest(td / "artifacts" / file) == info["published_sha256"]
            assert turn["usage"], (name, "missing usage")
            usage.extend(turn["usage"])
        for file, info in summary["artifacts"].items():
            assert info["published"] and digest(folder / "artifacts" / file) == info["published_sha256"]
        endpoint = folder / f"turn-{assessment['reviewed_turn']:02d}" / "answer.md"
        assert digest(endpoint) == assessment["published_answer_sha256"]
        first = assessment["first_comparison_turn"]
        rows.append({
            "run": name, "source": source, "case": case, "sample": sample,
            "responses": len(summary["turns"]), "first_comparison_turn": first,
            "first_comparison_processing_seconds": round(sum(t["elapsed_seconds"] for t in summary["turns"][:first]), 3),
            "model_processing_seconds": summary["model_processing_seconds"],
            "operator_wait_seconds": summary["operator_wait_seconds"],
            "elapsed_seconds": summary["elapsed_seconds"],
            "usage": {key: sum(item[key] for item in usage) if all(key in item for item in usage) else None
                      for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")},
            "tool_calls": sum(t["tool_calls"] for t in summary["turns"]),
            "question_line_candidates": sum(t["question_line_candidates"] for t in summary["turns"]),
            "cleanup_status": summary["cleanup_status"],
            "summary_sha256": digest(folder / "summary.json"),
            "assessment_sha256": digest(HERE / "assessments" / f"{name}.json"),
        })
    print(json.dumps({"runs": rows, "completed": len(rows),
                      "interpretation": "Operator-reviewed delivery of document-scoped findings; not live discovery or quality superiority."}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
