"""Public read-only fetches; all output is local to this independent lab."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent

def log(event, **kwargs):
    with (ROOT / 'activity.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'time_utc': datetime.now(timezone.utc).isoformat(), 'event': event, **kwargs}, ensure_ascii=False) + '\n')

def fetch(url, filename):
    path = ROOT / filename
    if path.exists():
        raise FileExistsError(f'Refusing overwrite: {path.name}')
    request = urllib.request.Request(url, headers={'User-Agent':'weather-research/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(4_000_001)
            if len(body) > 4_000_000:
                raise ValueError('Input exceeds 4 MB experiment size limit')
            path.write_bytes(body)
            result = {'url':url, 'file':filename, 'status':response.status, 'content_type':response.headers.get('Content-Type'), 'bytes':len(body), 'sha256':hashlib.sha256(body).hexdigest()}
            log('download', **result)
            print(json.dumps(result))
    except Exception as exc:
        result = {'url':url, 'file':filename, 'error':type(exc).__name__, 'detail':str(exc)}
        log('download_failure', **result)
        print(json.dumps(result))

if __name__ == '__main__':
    log('command', argv=sys.argv, python=sys.version)
    fetch(sys.argv[1], sys.argv[2])
