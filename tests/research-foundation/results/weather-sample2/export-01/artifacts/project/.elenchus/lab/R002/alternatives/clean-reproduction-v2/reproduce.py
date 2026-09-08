"""Portable offline reproduction; writes only under the chosen output directory."""
import argparse
from pathlib import Path
import json
import platform
import sqlite3
import weather_path as w

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=ROOT / 'output/reproduction')
parser.add_argument('--timezone', default='UTC')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
database = args.out / 'weather.sqlite'
runs = []
for name in ('seoul-era5', 'seoul-era5-imperial'):
    runs.append(w.ingest(ROOT / f'fixtures/{name}.json', ROOT / f'fixtures/{name}.meta.json', database))
# Replaying the first immutable fixture should not add logical rows.
runs.append(w.ingest(ROOT / 'fixtures/seoul-era5.json', ROOT / 'fixtures/seoul-era5.meta.json', database))
result = w.query(database, display_timezone=args.timezone)
assert len(result['rows']) == 432
assert runs[-1]['rows_total'] == 432
(args.out / 'query.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
summary = dict(python=platform.python_version(), sqlite=sqlite3.sqlite_version, runs=runs,
               measurements=len(result['rows']), summaries=result['summary'], database=str(database))
(args.out / 'reproduction.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=True, indent=2))
