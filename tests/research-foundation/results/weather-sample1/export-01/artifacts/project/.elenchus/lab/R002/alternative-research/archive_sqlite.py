"""Reproduce ISD-Lite normalization and SQLite storage, using stdlib only."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import sqlite3
import sys
from fetch_probe import log

ROOT = Path(__file__).resolve().parent
RAW = ROOT / '471080-99999-2024.gz'
EXPECTED_SHA = '2619321a2fbaf7a472757b9de2b4d777d3c0b2a89d5ee4886a4dd2b5f886c220'
STATION = '471080-99999'
SOURCE_URL = 'https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/2024/471080-99999-2024.gz'
# This constructed migration candidate returned HTTP404; it is not a fallback endpoint.
FAILED_SOURCE_CANDIDATE = 'https://noaa-isd-pds.s3.amazonaws.com/isd-lite/2024/471080-99999-2024.gz'

def scale(value, factor=10):
    return None if value == -9999 else value / factor

def normalize(line):
    fields = list(map(int, line.split()))
    if len(fields) != 12:
        raise ValueError(f'Expected 12 ISD-Lite fields, got {len(fields)}')
    year, month, day, hour, temp, dew, pressure, direction, wind, cloud, rain1, rain6 = fields
    stamp = datetime(year, month, day, hour, tzinfo=timezone.utc)
    # Trace precipitation is a distinct observed state; no exact numeric amount is reported.
    if rain1 < 0 and rain1 not in (-9999, -1):
        raise ValueError('Unexpected negative precipitation')
    state = 'missing' if rain1 == -9999 else 'trace' if rain1 == -1 else 'measured'
    amount = scale(rain1) if state == 'measured' else None
    return (STATION, int(stamp.timestamp()), scale(temp), scale(wind), amount, state)

def run():
    log('command', argv=sys.argv, python=sys.version, sqlite=sqlite3.sqlite_version)
    digest_before = hashlib.sha256(RAW.read_bytes()).hexdigest()
    if digest_before != EXPECTED_SHA:
        raise ValueError('Fixture hash mismatch: review the new input before ingestion')
    lines = gzip.decompress(RAW.read_bytes()).decode('ascii').splitlines()
    rows = [normalize(line) for line in lines if line.strip()]
    con = sqlite3.connect(ROOT / 'observations.sqlite3')
    con.execute('PRAGMA foreign_keys = ON')
    con.execute('''CREATE TABLE IF NOT EXISTS observations (
        station TEXT NOT NULL, time_utc INTEGER NOT NULL,
        temperature_c REAL, wind_m_s REAL CHECK(wind_m_s IS NULL OR wind_m_s >= 0),
        precipitation_1h_mm REAL CHECK(precipitation_1h_mm IS NULL OR precipitation_1h_mm >= 0),
        precipitation_1h_status TEXT NOT NULL CHECK(precipitation_1h_status IN ('missing','trace','measured')),
        CHECK((precipitation_1h_status = 'measured' AND precipitation_1h_mm IS NOT NULL)
              OR (precipitation_1h_status != 'measured' AND precipitation_1h_mm IS NULL)),
        PRIMARY KEY(station, time_utc)) STRICT''')
    statement = '''INSERT INTO observations VALUES (?,?,?,?,?,?)
       ON CONFLICT(station,time_utc) DO UPDATE SET
       temperature_c=excluded.temperature_c, wind_m_s=excluded.wind_m_s,
       precipitation_1h_mm=excluded.precipitation_1h_mm,
       precipitation_1h_status=excluded.precipitation_1h_status'''
    before = con.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
    with con:
        con.executemany(statement, rows)
    first = con.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
    with con:
        con.executemany(statement, rows)
    second = con.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
    assert first == second == len({(r[0],r[1]) for r in rows})
    con.close()
    con = sqlite3.connect(f'file:{(ROOT / "observations.sqlite3").as_posix()}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    summary = dict(con.execute('''SELECT count(*) rows, min(time_utc) first_epoch, max(time_utc) last_epoch,
          count(temperature_c) temperature_valid, sum(temperature_c IS NULL) temperature_missing,
          count(wind_m_s) wind_valid, sum(wind_m_s IS NULL) wind_missing,
          sum(precipitation_1h_status='missing') rain_missing,
          sum(precipitation_1h_status='trace') rain_trace,
          sum(precipitation_1h_status='measured') rain_measured,
          min(temperature_c) min_temp_c, max(temperature_c) max_temp_c FROM observations''').fetchone())
    expected = set(range(int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()),int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()),3600))
    observed = {r[1] for r in rows}
    summary['expected_year_hours'] = len(expected)
    summary['missing_hour_rows'] = len(expected - observed)
    summary['missing_hour_examples_utc'] = [datetime.fromtimestamp(t,timezone.utc).isoformat() for t in sorted(expected-observed)[:5]]
    summary['outside_year_rows'] = len(observed-expected)
    sample = [dict(row) for row in con.execute('SELECT * FROM observations ORDER BY time_utc LIMIT 3')]
    bounds = (int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()),int(datetime(2024,1,3,tzinfo=timezone.utc).timestamp()))
    query48 = [dict(row) for row in con.execute('SELECT * FROM observations WHERE time_utc >= ? AND time_utc < ? ORDER BY time_utc', bounds)]
    con.close()
    assert digest_before == hashlib.sha256(RAW.read_bytes()).hexdigest()
    result = {'python':sys.version,'sqlite':sqlite3.sqlite_version,'input_sha256':digest_before,'input_rows':len(rows),
              'db_rows_before':before,'rows_after_first':first,'rows_after_repeat':second,
              'summary':summary,'first_three':sample,'first_48h_query_rows':len(query48),'raw_unchanged':True}
    (ROOT / 'archive-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (ROOT / 'query-48h.json').write_text(json.dumps(query48,indent=2),encoding='utf-8')
    log('archive_experiment_result', **result)
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    run()
