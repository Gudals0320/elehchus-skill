"""Portable offline reproduction; writes only under the chosen output directory."""
import argparse
from pathlib import Path
import json
import platform
import sqlite3
import weather_path as w

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=ROOT / 'output/requested-reproduction')
parser.add_argument('--timezone', default='UTC')
parser.add_argument('--preset', choices=('requested', 'legacy'), default='requested')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
database = args.out / 'weather.sqlite'
runs = []
names = ('seoul-requested-20260901',) if args.preset == 'requested' else ('seoul-era5', 'seoul-era5-imperial')
expected = 96 if args.preset == 'requested' else 432
for name in names:
    runs.append(w.ingest(ROOT / f'fixtures/{name}.json', ROOT / f'fixtures/{name}.meta.json', database))
# Replaying the first immutable fixture should not add logical rows.
runs.append(w.ingest(ROOT / f'fixtures/{names[0]}.json', ROOT / f'fixtures/{names[0]}.meta.json', database))
result = w.query(database, display_timezone=args.timezone)
assert len(result['rows']) == expected, 'Use a separate database directory for each preset'
assert runs[-1]['rows_total'] == expected
(args.out / 'query.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
summary = dict(preset=args.preset, python=platform.python_version(), sqlite=sqlite3.sqlite_version, runs=runs,
               measurements=len(result['rows']), summaries=result['summary'], database=str(database))
(args.out / 'reproduction.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=True, indent=2))
