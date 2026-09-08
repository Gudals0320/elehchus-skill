"""Fetch only a small public GHCNh PSV prefix, preserving metadata and raw bytes."""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import urllib.request
from fetch_probe import log

ROOT = Path(__file__).resolve().parent
URL = 'https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-year/2023/psv/GHCNh_USW00003812_2023.psv'

def run():
    path = ROOT/'ghcnh-2023-prefix.psv'
    if '--offline' in sys.argv:
        body = path.read_bytes()
        meta = json.loads((ROOT/'ghcnh-probe-results.json').read_text(encoding='utf-8'))
        assert hashlib.sha256(body).hexdigest() == meta['sha256']
    elif path.exists():
        raise FileExistsError('Refuse to overwrite raw prefix')
    else:
        request = urllib.request.Request(URL,headers={'Range':'bytes=0-65535','User-Agent':'weather-research/1.0'})
        with urllib.request.urlopen(request,timeout=25) as response:
            body = response.read(65536)
            meta = {'url':URL,'status':response.status,'requested_range':'bytes=0-65535',
                    'content_range':response.headers.get('Content-Range'),
                    'content_type':response.headers.get('Content-Type'),
                    'bytes_saved':len(body),'sha256':hashlib.sha256(body).hexdigest(),
                    'sample_only':True}
        path.write_bytes(body)
    # Keep only complete lines when parsing the intentionally truncated prefix.
    text = body[:body.rfind(b'\n')+1].decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text), delimiter='|')
    rows = list(reader)
    chosen = ['STATION','Station_name','DATE','Year','Month','Day','Hour','Minute',
              'temperature','temperature_Quality_Code','wind_speed','wind_speed_Quality_Code',
              'precipitation','precipitation_Measurement_Code']
    meta['columns'] = reader.fieldnames
    meta['complete_rows_in_prefix'] = len(rows)
    meta['nonzero_minute_rows'] = sum(r['Minute'] != '00' for r in rows)
    meta['temperature_missing_rows'] = sum(r['temperature'] == '' for r in rows)
    meta['precipitation_missing_rows'] = sum(r['precipitation'] == '' for r in rows)
    meta['first_two_rows_selected'] = [{k:r[k] for k in chosen if k in r} for r in rows[:2]]
    meta['first_row_all_nonempty'] = {k:v for k,v in rows[0].items() if v}
    (ROOT/'ghcnh-probe-results.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    log('ghcnh_offline_replay' if '--offline' in sys.argv else 'ghcnh_partial_download', **meta)
    print(json.dumps({k:v for k,v in meta.items() if k!='columns'},indent=2))

if __name__ == '__main__':
    run()
