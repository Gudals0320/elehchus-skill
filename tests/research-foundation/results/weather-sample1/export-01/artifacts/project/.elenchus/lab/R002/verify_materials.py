"""Main integrator's isolated NOAA replay and protected-original check."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
work = root.parents[3]
destination = root / 'verification' / 'noaa-replay'
destination.mkdir(parents=True, exist_ok=True)
names = ['archive_sqlite.py', 'failure_probes.py', 'fetch_probe.py', '471080-99999-2024.gz']
hashes = {}
for name in names:
    source = root / 'alternative-research' / name
    target = destination / name
    shutil.copyfile(source, target)
    hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
for script in ['archive_sqlite.py', 'failure_probes.py']:
    process = subprocess.run([sys.executable, '-B', script], cwd=destination, capture_output=True, timeout=60)
    (destination / (script + '.stdout.txt')).write_bytes(process.stdout)
    (destination / (script + '.stderr.txt')).write_bytes(process.stderr)
    if process.returncode:
        raise RuntimeError(f'Replay failed: {script}; see logs')
archive = json.loads((destination / 'archive-results.json').read_text())
assert archive['rows_after_first'] == archive['rows_after_repeat'] == 8430
assert archive['first_48h_query_rows'] == 48
assert archive['summary']['missing_hour_rows'] == 354
assert archive['summary']['rain_trace'] == 130
originals = json.loads((work / 'records' / 'original-hashes.json').read_text(encoding='utf-8-sig'))
for original in originals:
    actual = hashlib.sha256(Path(original['Path']).read_bytes()).hexdigest()
    assert actual.upper() == original['Hash'].upper(), original['Path']
result = {'time': datetime.now(timezone.utc).isoformat(), 'event': 'main_isolated_replay',
          'command': 'python -B project/.elenchus/lab/R002/verify_materials.py',
          'result': 'NOAA archive replay and synthetic probes passed; protected originals unchanged',
          'noaa_rows': 8430, 'original_files_unchanged': len(originals), 'copied_input_hashes': hashes,
          'artifact': 'project/.elenchus/lab/R002/verification/noaa-replay/'}
(root / 'verification' / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
with (work / 'records' / 'activity.jsonl').open('a', encoding='utf-8') as log:
    log.write(json.dumps(result) + '\n')
print(json.dumps(result, indent=2))
