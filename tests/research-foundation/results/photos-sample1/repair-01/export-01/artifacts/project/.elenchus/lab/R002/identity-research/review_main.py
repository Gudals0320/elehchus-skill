"""Compare main and independent evidence; verify an existing local Junction."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-lab", required=True, type=Path)
    args = parser.parse_args()
    lab = Path(__file__).resolve().parent
    main_code = args.main_lab / "photo_materials.py"
    before = digest(main_code)
    spec = importlib.util.spec_from_file_location("reviewed_photo_materials", main_code)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    main_report = json.loads((args.main_lab / "sample-report-final.json").read_text(encoding="utf-8"))
    own = json.loads((lab / "observations.json").read_text(encoding="utf-8"))
    main_rows = {r["path"]: r for r in main_report["records"]}
    own_rows = {r["path"]: r for r in own["input_files"]}
    differences = []
    for name, row in own_rows.items():
        other = main_rows[name]
        for own_key, main_key in (("bytes", "size"), ("sha256", "sha256"),
                                  ("detected_format", "format"), ("encoded_size", "encoded_size"),
                                  ("display_size", "display_size"), ("orientation", "orientation")):
            if row.get(own_key) != other.get(main_key):
                differences.append({"path": name, "field": main_key,
                                    "own": row.get(own_key), "main": other.get(main_key)})
        if (row["decode"] == "ok") != (other["status"] == "ok"):
            differences.append({"path": name, "field": "validity"})
    main_groups = sorted((g["sha256"], sorted(g["members"])) for g in main_report["exact_groups"])
    own_groups = sorted((g["sha256"], sorted(g["paths"])) for g in own["original_exact_groups"])
    candidates = {c["path"]: c for c in main_report["candidates"]}
    tiff = main_rows["formats/sample.tiff"]
    tiff_date = [d for d in tiff["dates"] if d["source"] == "IFD0.DateTime"]
    variant_differences = []
    for row in own["synthesized_variants"]:
        path = lab / "fixtures" / row["path"]
        actual = module.inspect_bytes(path.read_bytes(), path.suffix)
        if actual["status"] != "ok" or actual["display_size"] != row["display_size"] or actual["format"] != row["detected_format"]:
            variant_differences.append(row["path"])

    fixture_source = lab / "junction-fixtures" / "source"
    junction = fixture_source / "linked-target"
    target_marker = lab / "junction-fixtures" / "target" / "target-only.txt"
    marker_before = digest(target_marker)
    junction_stat = junction.lstat()
    result = module.scan_directory(fixture_source)
    junction_rows = {r["path"]: r for r in result["records"]}
    rejected = False
    root_error = None
    try:
        module.scan_directory(junction)
    except ValueError as exc:
        rejected, root_error = True, str(exc)
    checks = {
        "same_input_paths": set(main_rows) == set(own_rows),
        "same_core_observations": not differences,
        "same_exact_groups": main_groups == own_groups,
        "all_candidates_review_only": all(c["action"] == "review_only" for c in candidates.values()),
        "dated_pair_bucket_uses_capture": all(candidates[p]["date_bucket"] == "2024-07-15" and candidates[p]["date_source"] == "ExifIFD.DateTimeOriginal" for p in own_groups[0][1]),
        "tiff_ifd0_date_preserved_not_capture": len(tiff_date) == 1 and tiff_date[0]["raw"] == own_rows["formats/sample.tiff"]["date_time_ifd0"] and tiff["capture"] is None,
        "missing_capture_not_assigned_day": all(candidates[p]["date_bucket"] is None for p in ("formats/sample.tiff", "plain.png", "회전/rotated.jpg")),
        "tiff_and_jpeg_transforms_explicit": all("orientation_transform_for_display" in candidates[p]["review_reasons"] for p in ("formats/sample.tiff", "회전/rotated.jpg")),
        "variants_agree_on_format_decode_display": not variant_differences,
        "junction_has_reparse_attribute": bool(junction_stat.st_file_attributes & 0x400),
        "junction_skipped": junction_rows.get("linked-target", {}).get("status") == "skipped_link",
        "junction_target_not_traversed": set(junction_rows) == {"direct.txt", "linked-target"},
        "junction_root_rejected": rejected,
        "target_contents_unchanged": marker_before == digest(target_marker),
        "main_code_unchanged_during_review": before == digest(main_code),
    }
    report = {"main_code_sha256": before, "checks": checks, "differences": differences,
              "variant_differences": variant_differences, "tiff_ifd0_dates": tiff_date,
              "junction_lstat_attributes": junction_stat.st_file_attributes,
              "junction_scan": result, "junction_root_error": root_error}
    (lab / "main-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "differences": differences}, ensure_ascii=False, indent=2))
    assert all(checks.values())


if __name__ == "__main__":
    main()
