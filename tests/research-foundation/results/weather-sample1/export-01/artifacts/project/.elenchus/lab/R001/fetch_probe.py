"""Bounded public GET probe; preserves raw bytes and selected provenance only."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('url')
args = parser.parse_args()
root = Path(__file__).resolve().parent
out = root / 'samples'
out.mkdir(exist_ok=True)
event = {'time': dt.datetime.now(dt.timezone.utc).isoformat(), 'url': args.url,
         'name': args.name, 'command': 'python fetch_probe.py NAME URL'}
try:
    request = urllib.request.Request(args.url, headers={'User-Agent': 'elenchus-weather-lab/1.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError('Response exceeded 2 MB sample budget')
        event.update(status=response.status, content_type=response.headers.get('Content-Type'))
    path = out / (args.name + '.json')
    path.write_bytes(body)
    event.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), artifact=str(path.relative_to(root)))
except urllib.error.HTTPError as exc:
    body = exc.read(16_384)
    path = out / (args.name + '.error.txt')
    path.write_bytes(body)
    event.update(error=type(exc).__name__, status=exc.code, message=str(exc), artifact=str(path.relative_to(root)))
except Exception as exc:
    event.update(error=type(exc).__name__, message=str(exc))
(out / (args.name + '.meta.json')).write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding='utf-8')
with (root.parents[3] / 'records' / 'activity.jsonl').open('a', encoding='utf-8') as log:
    log.write(json.dumps(event, ensure_ascii=False) + '\n')
print(json.dumps(event, ensure_ascii=False))
raise SystemExit(1 if 'error' in event else 0)
