"""Validate saved outputs of the handoff reproduction, without network access."""
import hashlib
import json
import math
from pathlib import Path
import platform
import sqlite3
import sys
import tzdata

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))

first = read('ingest-si.json')
repeat = read('reingest-si.json')
imperial = read('ingest-imperial.json')
query = read('query-seoul.json')
assert first['rows'] == 48 and first['inserted'] is True
assert repeat['rows'] == 48 and repeat['inserted'] is False
assert first['dataset_id'] == repeat['dataset_id']
assert imperial['rows'] == 48 and imperial['dataset_id'] != first['dataset_id']
assert len(query['rows']) == query['summary']['row_count'] == 24
assert math.isclose(query['summary']['temperature_mean_c'], 3.345833333333333, abs_tol=1e-12)
assert query['rows'][0]['time_local'] == '2024-01-02T00:00:00+09:00'
assert query['rows'][-1]['time_local'] == '2024-01-02T23:00:00+09:00'
assert 'Ran 17 tests' in (ROOT / 'test.log').read_text(encoding='utf-8-sig')
assert (ROOT / 'test.log').read_text(encoding='utf-8-sig').strip().endswith('OK')
connection = sqlite3.connect((ROOT / 'lab/R002/output/replay.sqlite').as_uri() + '?mode=ro', uri=True)
try:
    counts = dict(connection.execute('SELECT dataset_id, COUNT(*) FROM hourly GROUP BY dataset_id'))
    integrity = connection.execute('PRAGMA integrity_check').fetchall()
    foreign_key_issues = connection.execute('PRAGMA foreign_key_check').fetchall()
    kinds = list(connection.execute('SELECT DISTINCT data_kind FROM datasets'))
finally:
    connection.close()
assert counts == {first['dataset_id']: 48, imperial['dataset_id']: 48}
assert integrity == [('ok',)] and foreign_key_issues == []
assert kinds == [('reanalysis',)]
file_hashes = []
for entry in read('input-manifest.json'):
    digest = hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest()
    assert digest == entry['original_sha256'] == entry['copy_sha256']
    file_hashes.append({'path': entry['path'], 'sha256': digest})
summary = {
    'status': 'passed',
    'environment': {'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
                    'tzdata': tzdata.__version__, 'executable': sys.executable,
                    'tzdata_path': tzdata.__file__, 'independent_venv': True},
    'unittest_count': 17, 'unittest_status': 'OK',
    'si_ingest': first, 'si_reingest': repeat, 'imperial_ingest': imperial,
    'seoul_query': query['summary'],
    'seoul_first_label': query['rows'][0]['time_local'],
    'seoul_last_label': query['rows'][-1]['time_local'],
    'database_counts': counts, 'database_integrity': integrity,
    'foreign_key_issues': foreign_key_issues, 'data_kinds': kinds,
    'copied_inputs_unchanged': True, 'file_hashes': file_hashes,
    'network_scope': 'Only public PyPI setup; weather tests and replay use copied preserved samples. No fresh weather GET.'
}
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: summary[k] for k in ('status','unittest_count','seoul_query','database_counts','copied_inputs_unchanged')}, ensure_ascii=False, indent=2))
