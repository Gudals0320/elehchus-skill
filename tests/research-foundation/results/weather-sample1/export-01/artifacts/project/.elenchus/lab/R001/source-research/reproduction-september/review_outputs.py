"""Independent cross-check of September replay outputs; no network and no source edits."""
from contextlib import closing
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
R002 = ROOT / 'lab/R002'
sys.path.insert(0, str(R002))
import weather_pipeline as weather
import tzdata
assert Path(weather.__file__).resolve() == (R002 / 'weather_pipeline.py').resolve()
assert importlib.metadata.version('tzdata') == '2026.3'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

replay = read(R002 / 'output/requested-run-summary.json')
result = read(R002 / 'output/requested-seoul-query.json')
assert len(replay['ingestions']) == 3
assert all(x['inserted'] is True and x['rows'] == 48 and x['missing_rows'] == 0 for x in replay['ingestions'])
assert replay['same_file_replay']['inserted'] is False
assert result['rows'][0]['epoch_utc'] == 1788188400
assert result['rows'][-1]['epoch_utc'] == 1788357600
assert [row['epoch_utc'] for row in result['rows']] == list(range(1788188400, 1788361200, 3600))
assert all(row['wind_speed_ms'] is None and row['quality'] == 'not_requested:wind_speed_10m' for row in result['rows'])
assert all(row['precipitation_period_end_utc'] == row['epoch_utc'] and row['precipitation_period_start_utc'] == row['epoch_utc'] - 3600 for row in result['rows'])
assert replay['database_integrity'] == [['ok']] and not replay['foreign_key_errors']
url = weather.request_url(37.5665, 126.9780, '2026-09-01', '2026-09-02', request_timezone='Asia/Seoul')
params = parse_qs(urlsplit(url).query)
assert params['hourly'] == ['temperature_2m,precipitation']
assert params['timezone'] == ['Asia/Seoul'] and params['timeformat'] == ['unixtime']
wind_params = parse_qs(urlsplit(weather.request_url(37.5665, 126.9780, '2026-09-01', '2026-09-02', request_timezone='Asia/Seoul', include_wind=True)).query)
assert wind_params['hourly'] == ['temperature_2m,precipitation,wind_speed_10m']
with closing(sqlite3.connect((R002 / 'output/requested-weather.sqlite').as_uri() + '?mode=ro', uri=True)) as db:
    dataset_rows = db.execute('SELECT id, request_json, raw_file, raw_sha256 FROM datasets ORDER BY id').fetchall()
    wind_rows = db.execute("SELECT count(*) FROM hourly WHERE wind_speed_ms IS NULL AND quality='not_requested:wind_speed_10m'").fetchone()[0]
assert len(dataset_rows) == 3 and wind_rows == 144
for _, request_json, raw_file, raw_sha in dataset_rows:
    request = json.loads(request_json)
    assert request['hourly'] == ['temperature_2m,precipitation']
    assert request['timezone'] == ['Asia/Seoul']
    assert request['start_date'] == ['2026-09-01'] and request['end_date'] == ['2026-09-02']
    assert hashlib.sha256((ROOT / 'lab/R001/requested-samples' / raw_file).read_bytes()).hexdigest() == raw_sha
files = sorted((ROOT / 'lab/R001/requested-samples').glob('*.json'))
raws = [path for path in files if not path.name.endswith('.meta.json')]
first, repeat = read(raws[0]), read(raws[1])
changed_top_level_keys = [key for key in first if first[key] != repeat.get(key)]
assert first['hourly'] == repeat['hourly']
assert read(raws[0].with_suffix('.meta.json'))['url'] == read(raws[1].with_suffix('.meta.json'))['url']
for item in read(ROOT / 'input-manifest.json'):
    assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['before_sha256'] == item['copy_sha256']
log = (ROOT / 'test.log').read_text(encoding='utf-8-sig')
assert 'Ran 22 tests' in log and log.strip().endswith('OK')
review = {
    'status': 'passed', 'review_findings': [],
    'review_scope': 'Selected Seoul dates, UTC labels, requested variables, not_requested vs missing, exact-file and changed-byte snapshot policy',
    'unittest_count': 22,
    'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version, 'tzdata': tzdata.__version__,
    'runtime_path': sys.executable, 'imported_source_path': weather.__file__,
    'dependency_environment': 'Reused earlier source-research independent venv; main venv not used',
    'new_weather_gets': 0, 'source_patches': 0,
    'first_epoch': 1788188400, 'last_epoch': 1788357600, 'exclusive_upper_epoch': 1788361200,
    'requested_variables': params['hourly'][0].split(','), 'not_requested_wind_rows': wind_rows,
    'snapshot_count': len(dataset_rows), 'snapshot_rows': [count for _,count in replay['database_counts']],
    'same_file_replay_inserted': replay['same_file_replay']['inserted'],
    'actual_refetch_weather_arrays_equal': True,
    'actual_refetch_changed_top_level_keys': changed_top_level_keys,
    'mean_temperature_c': result['summary']['temperature_mean_c'],
    'precipitation_label_sum_mm': result['summary']['precipitation_observed_sum_mm'],
    'max_unit_conversion_error': replay['max_unit_conversion_error'],
    'db_integrity': replay['database_integrity'], 'foreign_key_errors': replay['foreign_key_errors'],
    'copied_inputs_unchanged': True,
    'limitations': ['No new live availability check performed by this agent.', 'No general security or high-volume/concurrent-writer audit.', 'Preceding-hour label sum is not a local calendar-day precipitation total.']
}
(ROOT / 'review-summary.json').write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(review, indent=2, ensure_ascii=False))
