"""Optional dataframe comparison on exactly the same preserved NOAA fixture."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import sqlite3
import pandas as pd
from archive_sqlite import EXPECTED_SHA, RAW
from fetch_probe import log

ROOT = Path(__file__).resolve().parent

def run():
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == EXPECTED_SHA
    cols = ['year','month','day','hour','temp','dew','pressure','direction','wind','cloud','rain1','rain6']
    frame = pd.read_csv(RAW,sep=r'\s+',header=None,names=cols,compression='gzip',na_values=[-9999])
    frame['time'] = pd.to_datetime(frame[['year','month','day','hour']],utc=True)
    frame['temperature_c'] = frame.temp/10
    frame['wind_m_s'] = frame.wind/10
    result = {'pandas_version':pd.__version__,'rows':len(frame),'wind_nulls':int(frame.wind.isna().sum()),
              'rain_nulls':int(frame.rain1.isna().sum()),'rain_trace':int((frame.rain1==-1).sum()),
              'naive_precipitation_min_mm':float((frame.rain1/10).min())}
    con = sqlite3.connect(':memory:')
    pd.DataFrame({'station':['X'],'time':[1704067200],'temperature_c':[0.6]}).to_sql('obs',con,index=False)
    con.execute('DELETE FROM obs')
    con.commit()
    sample = pd.DataFrame({'station':['X'],'time':[1704067200],'temperature_c':[0.6]})
    sample.to_sql('obs',con,index=False,if_exists='append')
    sample.to_sql('obs',con,index=False,if_exists='append')
    result['to_sql_auto_schema'] = con.execute("SELECT sql FROM sqlite_master WHERE name='obs'").fetchone()[0]
    result['to_sql_append_repeat_rows'] = con.execute('SELECT count(*) FROM obs').fetchone()[0]
    # to_sql(sqlite3.Connection) commits inserts even inside the caller's transaction.
    con.execute('CREATE TABLE atomicity(t INTEGER)')
    con.execute('BEGIN')
    pd.DataFrame({'t':[1]}).to_sql('atomicity',con,index=False,if_exists='append')
    con.rollback()
    result['to_sql_after_caller_rollback_rows'] = con.execute('SELECT count(*) FROM atomicity').fetchone()[0]
    try:
        pd.to_datetime(['2024-11-03 01:30:00-0400','2024-11-03 01:30:00-0500'])
    except ValueError as exc:
        result['mixed_offsets_default_error'] = str(exc)
    result['mixed_offsets_utc'] = [str(t) for t in pd.to_datetime(['2024-11-03 01:30:00-0400','2024-11-03 01:30:00-0500'],utc=True)]
    result['unit_epoch_ms_misread_as_ns'] = str(pd.to_datetime(1704067200000,utc=True))
    result['unit_epoch_ms_explicit'] = str(pd.to_datetime(1704067200000,unit='ms',utc=True))
    con.close()
    std = json.loads((ROOT/'archive-results.json').read_text(encoding='utf-8'))
    assert result['rows'] == std['input_rows']
    assert result['wind_nulls'] == std['summary']['wind_missing']
    assert result['rain_trace'] == std['summary']['rain_trace']
    assert result['naive_precipitation_min_mm'] == -0.1
    assert result['to_sql_append_repeat_rows'] == 2
    assert result['to_sql_after_caller_rollback_rows'] == 1
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == EXPECTED_SHA
    (ROOT/'pandas-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    log('pandas_experiment_result', **result)
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    run()
