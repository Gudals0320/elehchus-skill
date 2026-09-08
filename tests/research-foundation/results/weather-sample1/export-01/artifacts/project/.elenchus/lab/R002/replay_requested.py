"""Offline reproduction of the user-selected Seoul/date window from preserved responses."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from weather_pipeline import ingest, query_data, normalize, read_json

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT.parent / 'R001' / 'requested-samples'
FILES = [
    '20260908T082652425301Z-3c0cfd0e9f00.json',
    '20260908T082756854001Z-4fdfd2e8e75c.json',
    '20260908T082801908167Z-905478802dbd.json',
]


def run():
    output = ROOT / 'output'
    output.mkdir(exist_ok=True)
    database = output / 'requested-weather.sqlite'
    ingestions = [ingest(SAMPLES / name, database) for name in FILES]
    same_file = ingest(SAMPLES / FILES[1], database)
    result = query_data(database, ingestions[0]['dataset_id'], '2026-09-01T00:00+09:00',
                        '2026-09-03T00:00+09:00', 'Asia/Seoul')
    (output / 'requested-seoul-query.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    parsed = [read_json((SAMPLES / name).read_bytes()) for name in FILES]
    normal = [normalize(item) for item in parsed]
    assert len(result['rows']) == 48 and not same_file['inserted']
    assert result['rows'][0]['time_local'] == '2026-09-01T00:00:00+09:00'
    assert result['rows'][-1]['time_local'] == '2026-09-02T23:00:00+09:00'
    assert normal[0] == normal[1]
    max_temp_error = max(abs(a[1] - b[1]) for a, b in zip(normal[0], normal[2]))
    max_rain_error = max(abs(a[2] - b[2]) for a, b in zip(normal[0], normal[2]))
    assert max_temp_error <= .08 and max_rain_error <= .02
    with closing(sqlite3.connect(database)) as connection:
        integrity = connection.execute('PRAGMA integrity_check').fetchall()
        foreign_keys = connection.execute('PRAGMA foreign_key_check').fetchall()
        counts = connection.execute('SELECT dataset_id,count(*) FROM hourly GROUP BY dataset_id').fetchall()
    summary = {
        'time': datetime.now(timezone.utc).isoformat(), 'requested_latitude': 37.5665,
        'requested_longitude': 126.9780, 'requested_dates': ['2026-09-01', '2026-09-02'],
        'calendar_timezone': 'Asia/Seoul', 'source': 'Open-Meteo / Copernicus ERA5',
        'data_kind': 'reanalysis', 'final_release_status': 'not indicated in API response; recent ERA5 can be revised',
        'fallback_used': False, 'grid_latitude': parsed[0]['latitude'], 'grid_longitude': parsed[0]['longitude'],
        'ingestions': ingestions, 'same_file_replay': same_file,
        'same_weather_arrays_after_actual_refetch': normal[0] == normal[1],
        'raw_sha256': [hashlib.sha256((SAMPLES / file).read_bytes()).hexdigest() for file in FILES],
        'query_summary': result['summary'],
        'first_label': result['rows'][0]['time_local'], 'last_label': result['rows'][-1]['time_local'],
        'max_unit_conversion_error': {'temperature_c': max_temp_error, 'precipitation_mm': max_rain_error},
        'database_counts': counts, 'database_integrity': integrity, 'foreign_key_errors': foreign_keys,
        'precipitation_note': 'Preceding-hour amounts at selected labels; sum is not a local calendar-day total.',
    }
    (output / 'requested-run-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
