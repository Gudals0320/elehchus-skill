"""Independent, offline, bounded processing probes; writes only below alternatives/."""
from __future__ import annotations

from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sqlite3
import sys
import warnings
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R002 = HERE.parent
RESPONSES = R002.parent / "R001" / "responses"
RUN = HERE / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN.mkdir(parents=True)
snapshot = RUN / "weather_path_reviewed.py"
snapshot.write_bytes((R002 / "weather_path.py").read_bytes())
spec = importlib.util.spec_from_file_location("weather_review", snapshot)
weather = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather)
import pandas as pd

results = {"recorded_at": datetime.now(timezone.utc).isoformat(),
           "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                           "pandas": pd.__version__},
           "module_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
           "module_snapshot": str(snapshot.relative_to(HERE)), "probes": {}}


def capture(name, operation):
    try:
        results["probes"][name] = {"status": "observed", "result": operation()}
    except Exception as exc:
        results["probes"][name] = {"status": "probe_error", "error": type(exc).__name__, "message": str(exc)}


def real_input(stem):
    raw = (RESPONSES / f"{stem}.json").read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    metas = [json.loads(p.read_text(encoding="utf-8")) for p in RESPONSES.glob(f"{stem}.meta.*.json")]
    metadata = next(m for m in metas if m.get("sha256") == sha)
    return raw, metadata


input_before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in RESPONSES.glob("seoul-era5*.json")}
raw, metadata = real_input("seoul-era5")
original = json.loads(raw)


def compare_pandas(stem):
    data, meta = real_input(stem)
    payload = json.loads(data)
    _, _, main_rows = weather.contract(data, meta)
    df = pd.DataFrame(payload["hourly"])
    df["time_utc"] = pd.to_datetime(df["time"], unit="s", utc=True)
    tunit = payload["hourly_units"]["temperature_2m"]
    wunit = payload["hourly_units"]["wind_speed_10m"]
    punit = payload["hourly_units"]["precipitation"]
    temp = df["temperature_2m"] if tunit == "°C" else (df["temperature_2m"] - 32) / 1.8
    wind = df["wind_speed_10m"] / 3.6 if wunit == "km/h" else df["wind_speed_10m"] * 1609.344 / 3600
    precip = df["precipitation"] if punit == "mm" else df["precipitation"] * 25.4
    independent = dict(zip(weather.VARIABLES, [temp.tolist(), precip.tolist(), wind.tolist()]))
    expected = {(row[1], row[2]): row[5] for row in main_rows}
    deltas = [abs(independent[v][i] - expected[t, v]) for i, t in enumerate(df["time"]) for v in independent]
    assert max(deltas) < 1e-12
    assert df["time_utc"].iloc[0].isoformat().replace("+00:00", "Z") == weather.utc_iso(int(df["time"].iloc[0]))
    return {"actual_response": f"{stem}.json", "sha256": meta["sha256"], "hour_count": len(df),
            "compared_values": len(deltas), "maximum_absolute_difference": max(deltas),
            "time_start": str(df["time_utc"].iloc[0]), "source_units": payload["hourly_units"]}


def dst_probe():
    rows = []
    for raw_time in ["2025-11-02T05:30:00+00:00", "2025-11-02T06:30:00+00:00"]:
        utc = datetime.fromisoformat(raw_time)
        local = utc.astimezone(ZoneInfo("America/New_York"))
        via_pd = pd.Timestamp(utc).tz_convert("America/New_York")
        assert local.isoformat() == via_pd.isoformat()
        rows.append({"utc": raw_time, "local": local.isoformat(), "fold": local.fold})
    errors = []
    for local_time in ["2025-11-02 01:30", "2025-03-09 02:30"]:
        naive = datetime.fromisoformat(local_time)
        attached = naive.replace(tzinfo=ZoneInfo("America/New_York"))
        try:
            pd.Timestamp(local_time).tz_localize("America/New_York")
        except ValueError as exc:
            errors.append({"input": local_time, "pandas_error": type(exc).__name__, "message": str(exc),
                           "stdlib_attach_without_validation": attached.isoformat(),
                           "roundtrip_local": attached.astimezone(timezone.utc).astimezone(ZoneInfo("America/New_York")).isoformat()})
    assert len(errors) == 2
    return {"safe_utc_conversions": rows, "naive_local_hazards": errors}


def missing_probe():
    frame = pd.DataFrame({"value": [1.0, None, float("nan"), 0.0, -999.0]})
    with closing(sqlite3.connect(":memory:")) as con:
        frame.to_sql("pandas_missing", con, index=False)
        stored = con.execute("SELECT value, typeof(value) FROM pandas_missing").fetchall()
        con.execute("CREATE TABLE native(value REAL)")
        con.executemany("INSERT INTO native VALUES(?)", [(None,), (float("nan"),), (float("inf"),)])
        native = [(repr(v), kind) for v, kind in con.execute("SELECT value, typeof(value) FROM native")]
        sql_null_sum = con.execute("SELECT sum(value) FROM pandas_missing WHERE value IS NULL").fetchone()[0]
    allnull = pd.Series([None, None], dtype="Float64")
    return {"input": ["1.0", "None", "NaN", "0.0", "-999.0"], "pandas_isna": frame["value"].isna().tolist(),
            "to_sql_roundtrip": stored, "sqlite_native_nonfinite": native,
            "all_null": {"pandas_default_sum": float(allnull.sum()), "pandas_min_count_1": str(allnull.sum(min_count=1)),
                         "sqlite_sum": sql_null_sum}, "lesson": "Sentinel -999 remains numeric unless its provider contract maps it explicitly."}


def timestamp_converter_probe():
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with closing(sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)) as con:
            con.execute("CREATE TABLE t(ts timestamp)")
            con.execute("INSERT INTO t VALUES(?)", (datetime.fromisoformat("2025-01-01T00:00:00.123456+09:00"),))
            back = con.execute("SELECT ts FROM t").fetchone()[0]
    return {"input": "2025-01-01T00:00:00.123456+09:00", "roundtrip": back.isoformat(),
            "timezone_preserved": back.tzinfo is not None, "warnings": [str(w.message) for w in captured]}


def persist_fixture(name, payload, completed_at):
    path = RUN / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    meta = deepcopy(metadata)
    meta.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), completed_at=completed_at,
                requested_at=completed_at, synthetic=True, synthetic_scenario=name)
    meta_path = RUN / f"{name}.meta.json"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return path, meta_path


def replay_probe():
    old = persist_fixture("older", original, "2026-09-01T00:00:00+00:00")
    changed = deepcopy(original)
    changed["hourly"]["temperature_2m"][0] += 2.0
    newer = persist_fixture("newer", changed, "2026-09-02T00:00:00+00:00")
    original_seen_later = persist_fixture("original_seen_later", original, "2026-09-03T00:00:00+00:00")
    db = RUN / "replay.sqlite"
    steps = []
    for label, files in [("old", old), ("same_old_again", old), ("newer_revision", newer), ("replay_old", old),
                         ("original_payload_freshly_collected_later", original_seen_later)]:
        outcome = weather.ingest(*files, db)
        rows = weather.query(db)["rows"]
        temp = next(r for r in rows if r["variable"] == "temperature_2m")
        with closing(sqlite3.connect(db)) as con:
            stored_import, stored_fetched_at = con.execute(
                "SELECT m.import_id,i.fetched_at FROM measurements m JOIN imports i ON m.import_id=i.id "
                "WHERE m.variable='temperature_2m' ORDER BY m.timestamp_utc LIMIT 1").fetchone()
        steps.append({"step": label, "rows_total": outcome["rows_total"], "first_temperature": temp["value"],
                      "returned_import_id": outcome["import_id"], "measurement_import_id": stored_import,
                      "measurement_fetched_at": stored_fetched_at})
    assert len({s["rows_total"] for s in steps}) == 1
    return {"synthetic": True, "steps": steps,
            "old_replay_overwrote_newer": steps[3]["first_temperature"] != steps[2]["first_temperature"],
            "fresh_later_same_bytes_applied": steps[4]["first_temperature"] == steps[0]["first_temperature"]}


def validation_probe():
    cases = {}
    for name, mutate in [
        ("nan_temperature", lambda p: p["hourly"]["temperature_2m"].__setitem__(0, float("nan"))),
        ("negative_precipitation", lambda p: p["hourly"]["precipitation"].__setitem__(0, -999.0)),
        ("unknown_temperature_unit", lambda p: p["hourly_units"].__setitem__("temperature_2m", "K")),
        ("timestamp_removed", lambda p: [p["hourly"][k].pop(0) for k in ["time", *weather.VARIABLES]]),
        ("source_null", lambda p: p["hourly"]["temperature_2m"].__setitem__(0, None)),
    ]:
        payload = deepcopy(original)
        mutate(payload)
        raw_test = json.dumps(payload).encode()
        meta = dict(metadata, sha256=hashlib.sha256(raw_test).hexdigest())
        try:
            _, _, rows = weather.contract(raw_test, meta)
            cases[name] = {"accepted": True, "quality_counts": {q: sum(r[9] == q for r in rows) for q in ["valid", "source_null", "absent_timestamp"]}}
        except ValueError as exc:
            cases[name] = {"accepted": False, "error": type(exc).__name__, "message": str(exc)}
    return {"synthetic": True, "cases": cases}


capture("real_metric_pandas", lambda: compare_pandas("seoul-era5"))
capture("real_imperial_pandas", lambda: compare_pandas("seoul-era5-imperial"))
capture("dst", dst_probe)
capture("sqlite_timestamp_converter_before_to_sql", timestamp_converter_probe)
capture("missing", missing_probe)
capture("sqlite_timestamp_converter_after_to_sql", timestamp_converter_probe)
capture("recollection_order", replay_probe)
capture("validation", validation_probe)
input_after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in RESPONSES.glob("seoul-era5*.json")}
results["input_hashes_before"] = input_before
results["input_preserved"] = input_before == input_after
results["finished_at"] = datetime.now(timezone.utc).isoformat()
output = RUN / "results.json"
output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"result": str(output), "input_preserved": results["input_preserved"],
                  "probes": {k: v["status"] for k, v in results["probes"].items()}}, ensure_ascii=True, indent=2))
if any(v["status"] == "probe_error" for v in results["probes"].values()) or not results["input_preserved"]:
    raise SystemExit(1)
