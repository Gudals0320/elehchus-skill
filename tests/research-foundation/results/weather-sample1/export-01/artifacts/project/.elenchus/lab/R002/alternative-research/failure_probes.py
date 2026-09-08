"""Controlled synthetic counterexamples, not errors attributed to real NOAA input."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import warnings
from archive_sqlite import normalize
from fetch_probe import log

def run():
    con = sqlite3.connect(':memory:')
    result = {}
    con.execute('CREATE TABLE unsafe(station TEXT, t INTEGER, temperature REAL, PRIMARY KEY(station,t))')
    con.executemany('INSERT INTO unsafe VALUES (?,?,?)', [('X',None,'NA'),('X',None,'NA')])
    result['nullable_compound_pk_duplicates'] = con.execute('SELECT count(*) FROM unsafe').fetchone()[0]
    result['text_in_real_column'] = con.execute('SELECT typeof(temperature), avg(temperature) FROM unsafe').fetchone()
    con.execute('CREATE TABLE safe(station TEXT NOT NULL,t INTEGER NOT NULL,temperature REAL,PRIMARY KEY(station,t)) STRICT')
    for label, row in [('reject_null_key',('X',None,1.0)), ('reject_string_temperature',('X',1,'NA'))]:
        try:
            con.execute('INSERT INTO safe VALUES (?,?,?)',row)
        except sqlite3.IntegrityError as exc:
            result[label] = str(exc)
    # Neither local wall-time strings nor mixed-offset text sort chronologically in general.
    stamps = ['2024-01-01T00:30:00+09:00','2023-12-31T23:00:00+00:00']
    result['mixed_offset_lexical_order'] = sorted(stamps)
    result['mixed_offset_actual_order'] = sorted(stamps,key=lambda s:datetime.fromisoformat(s).timestamp())
    assert result['mixed_offset_lexical_order'] != result['mixed_offset_actual_order']
    aware = datetime(2024,1,1,0,0,0,123456,tzinfo=timezone.utc)
    legacy = sqlite3.connect(':memory:',detect_types=sqlite3.PARSE_DECLTYPES)
    legacy.execute('CREATE TABLE t(stamp TIMESTAMP)')
    with warnings.catch_warnings(record=True) as warns:
        warnings.simplefilter('always')
        legacy.execute('INSERT INTO t VALUES (?)',(aware,))
        output = legacy.execute('SELECT stamp FROM t').fetchone()[0]
    result['legacy_timestamp_adapter'] = {'input':aware.isoformat(),'output':output.isoformat(),'tzinfo':str(output.tzinfo),'warning_count':len(warns)}
    assert output.tzinfo is None
    legacy.close()
    base = '2024 1 1 0 100 20 10100 360 30 0 '
    result['synthetic_missing_precipitation'] = normalize(base+'-9999 -9999')[-2:]
    result['synthetic_trace_precipitation'] = normalize(base+'-1 -9999')[-2:]
    result['synthetic_zero_precipitation'] = normalize(base+'0 -9999')[-2:]
    assert result['synthetic_missing_precipitation'] == (None,'missing')
    assert result['synthetic_trace_precipitation'] == (None,'trace')
    assert result['synthetic_zero_precipitation'] == (0.0,'measured')
    for label, line in [('malformed_row',base+'BAD -9999'),('invalid_hour','2024 1 1 24 100 20 10100 360 30 0 0 -9999')]:
        try:
            normalize(line)
        except ValueError as exc:
            result[label] = str(exc)
    con.close()
    target = Path(__file__).resolve().parent/'failure-results.json'
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    log('synthetic_failure_probe_result', **result)
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    run()
