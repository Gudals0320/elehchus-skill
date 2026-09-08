"""Read-only independent checks of the supplied code's newly produced outputs."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent
LAB = ROOT / "run" / "project" / ".elenchus" / "lab" / "R002"
EVIDENCE = ROOT / "evidence"
sys.path.insert(0, str(LAB))
import weather_pipeline as weather


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_db(path):
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        result = {
            "integrity_check": db.execute("PRAGMA integrity_check").fetchall(),
            "foreign_key_check": db.execute("PRAGMA foreign_key_check").fetchall(),
            "datasets": db.execute("SELECT count(*) FROM datasets").fetchone()[0],
            "hourly_rows": db.execute("SELECT count(*) FROM hourly").fetchone()[0],
        }
    assert result["integrity_check"] == [("ok",)]
    assert not result["foreign_key_check"]
    return result


fixture = LAB.parent / "R001" / "requested-samples" / "20260908T082652425301Z-3c0cfd0e9f00.json"
fetch = read(EVIDENCE / "main-fetch-network.stdout.txt")
raw = (LAB / fetch["raw_file"]).resolve()
meta = read(raw.with_suffix(".meta.json"))
payload = read(raw)
assert meta["status"] == 200
assert hashlib.sha256(raw.read_bytes()).hexdigest() == meta["sha256"]
live_query = read(EVIDENCE / "main-live-query-corrected.stdout.txt")
replay = read(LAB / "output" / "requested-run-summary.json")
original = read(EVIDENCE / "original-before.json")
run_project = ROOT / "run" / "project"
source_names = [name for name in original if name.endswith((".py", ".txt"))]
changed_code = [name for name in source_names if hashlib.sha256((run_project / name).read_bytes()).hexdigest() != original[name]["sha256"]]
assert not changed_code
assert all(item["inserted"] and item["rows"] == 48 for item in replay["ingestions"])
assert not replay["same_file_replay"]["inserted"]
assert live_query["summary"]["row_count"] == 48
assert live_query["rows"][0]["time_local"] == "2026-09-01T00:00:00+09:00"
assert live_query["rows"][-1]["time_local"] == "2026-09-02T23:00:00+09:00"
result = {
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "environment": {
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "sqlite": sqlite3.sqlite_version, "prefix": sys.prefix, "base_prefix": sys.base_prefix,
        "isolated_venv": sys.prefix != sys.base_prefix,
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    },
    "copied_source_files_checked": len(source_names), "changed_source_files": changed_code,
    "live": {
        "raw_file": raw.relative_to(ROOT).as_posix(), "http_status": meta["status"],
        "fetch_time_utc": meta["time"], "request_url": meta["url"], "bytes": len(raw.read_bytes()),
        "sha256": meta["sha256"], "requested_coordinates": [37.5665, 126.978],
        "grid_coordinates": [payload["latitude"], payload["longitude"]],
        "weather_matches_preserved_si_fixture": weather.normalize(payload) == weather.normalize(read(fixture)),
        "raw_matches_preserved_si_fixture": raw.read_bytes() == fixture.read_bytes(),
        "summary": live_query["summary"],
        "first_label": live_query["rows"][0]["time_local"], "last_label": live_query["rows"][-1]["time_local"],
        "db": check_db(LAB / "output" / "live.sqlite"),
        "reingest": read(EVIDENCE / "main-live-reingest.stdout.txt"),
    },
    "offline": {
        "db": check_db(LAB / "output" / "requested-weather.sqlite"),
        "summary": replay["query_summary"], "max_unit_conversion_error": replay["max_unit_conversion_error"],
        "noaa": read(LAB / "alternative-research" / "archive-results.json"),
        "pandas": read(LAB / "alternative-research" / "pandas-results.json"),
        "ghcnh": {key: value for key, value in read(LAB / "alternative-research" / "ghcnh-probe-results.json").items()
                  if key in ["bytes_saved", "sha256", "complete_rows_in_prefix", "nonzero_minute_rows", "temperature_missing_rows", "precipitation_missing_rows"]},
    },
    "original_product_files": {name: original[name] for name in ["README.md", "existing-product.txt"]},
}
assert result["environment"]["isolated_venv"]
assert result["live"]["db"]["hourly_rows"] == 48
assert result["live"]["db"]["datasets"] == 1
assert result["offline"]["db"]["hourly_rows"] == 144
assert result["offline"]["db"]["datasets"] == 3
assert result["offline"]["noaa"]["db_rows_before"] == 0
(EVIDENCE / "review-summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
