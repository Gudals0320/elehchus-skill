"""Independent replay harness; supplied project files are never written."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'project'
COPY = ROOT / 'execution' / 'project'
LOGS = ROOT / 'evidence'
MAIN = COPY / '.elenchus/lab/R001/main'
META = COPY / '.elenchus/lab/R001/metadata-research'
IDENTITY = COPY / '.elenchus/lab/R002/identity-research'
PYTHON = MAIN / '.venv/Scripts/python.exe'

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def snapshot(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError(f'Unexpected original link: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'size': path.stat().st_size,
                'mtime_ns': path.stat().st_mtime_ns,
            }
    return result

def initialize():
    LOGS.mkdir(exist_ok=True)
    before = snapshot(SOURCE)
    write_json(LOGS / 'source-before.json', before)
    shutil.copytree(SOURCE, COPY, copy_function=shutil.copy2,
                    ignore=shutil.ignore_patterns('.venv', '.pip-cache', 'pip-cache', 'deps', '__pycache__', 'test-runs'))
    copied = snapshot(COPY)
    write_json(LOGS / 'copy-before.json', copied)
    write_json(LOGS / 'environment-initial.json', {
        'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'architecture': platform.machine(),
        'copied_files': len(copied), 'supplied_files': len(before),
        'copy_content_and_mtime_match': all(before[name] == value for name, value in copied.items()),
        'excluded_names': ['.venv', '.pip-cache', 'pip-cache', 'deps', '__pycache__', 'test-runs'],
    })
    print(json.dumps({'supplied_files': len(before), 'copied_files': len(copied),
                      'copy_content_and_mtime_match': all(before[name] == value for name, value in copied.items())}))

def run(name):
    p = str(PYTHON)
    definitions = {
        'venv': (COPY, [sys.executable, '-m', 'venv', str(MAIN / '.venv')]),
        'pip-pillow': (COPY, [p, '-m', 'pip', 'install', '--disable-pip-version-check', '--cache-dir', str(MAIN / '.pip-cache'), '--retries', '0', '--timeout', '20', '-r', str(MAIN / 'requirements.txt')]),
        'pip-context': (COPY, [p, '-B', '-c', 'import os,json; from urllib.parse import urlsplit; print(json.dumps({"PIP_NO_INDEX":os.environ.get("PIP_NO_INDEX"), "PIP_CONFIG_FILE":os.environ.get("PIP_CONFIG_FILE"), "index_hosts":{k:urlsplit(os.environ[k]).hostname for k in ("PIP_INDEX_URL","PIP_EXTRA_INDEX_URL") if k in os.environ}, "venv_isolation":__import__("sys").prefix != __import__("sys").base_prefix}))']),
        'pip-pillow-public': (COPY, [p, '-m', 'pip', '--isolated', 'install', '--index-url', 'https://pypi.org/simple', '--disable-pip-version-check', '--cache-dir', str(MAIN / '.pip-cache'), '--retries', '0', '--timeout', '20', '-r', str(MAIN / 'requirements.txt')]),
        'environment': (COPY, [p, '-I', '-B', '-c', 'import sys, PIL; print(sys.version); print(sys.executable); print("Pillow", PIL.__version__); print(PIL.__file__)']),
        'scan': (COPY, [p, '-B', str(MAIN / 'photo_materials.py'), 'inputs', '--output', str(MAIN / 'my-report.json')]),
        'render': (COPY, [p, '-I', '-B', str(MAIN / 'render_review.py'), str(MAIN / 'my-report.json'), '--output', str(MAIN / 'my-review.md')]),
        'tests': (MAIN, [p, '-B', '-m', 'unittest', '-v', 'test_photo_materials']),
        'local-review': (COPY, [p, '-B', str(MAIN / 'probe_local_review.py')]),
        'verify-originals': (COPY, [p, '-B', str(MAIN / 'verify_originals.py')]),
        'pip-exifread': (COPY, [p, '-B', '-m', 'pip', '--isolated', 'install', '--target', str(META / 'deps'), '--cache-dir', str(META / 'pip-cache'), '--disable-pip-version-check', '--retries', '0', '--timeout', '20', '--no-compile', '--only-binary=:all:', '--require-hashes', '-r', str(META / 'requirements.txt')]),
        'exifread': (COPY, [p, '-B', str(META / 'probe_exifread.py')]),
        'identity': (COPY, [p, '-I', '-B', str(IDENTITY / 'probe_identity.py'), '--inputs', 'inputs']),
        'prepare-junction': (ROOT, ['pwsh.exe', '-NoProfile', '-File', str(ROOT / 'prepare_junction.ps1')]),
        'identity-review': (COPY, [p, '-I', '-B', str(IDENTITY / 'review_main.py'), '--main-lab', str(MAIN)]),
    }
    cwd, argv = definitions[name]
    attempts = list(LOGS.glob(name + '-*.json'))
    stem = f'{name}-{len(attempts) + 1:02}'
    started = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    temp = ROOT / 'execution' / 'tmp'
    temp.mkdir(exist_ok=True)
    env['TEMP'] = str(temp)
    env['TMP'] = str(temp)
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True)
    (LOGS / (stem + '.stdout.txt')).write_bytes(result.stdout)
    (LOGS / (stem + '.stderr.txt')).write_bytes(result.stderr)
    write_json(LOGS / (stem + '.json'), {
        'command': argv, 'cwd': str(cwd), 'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'exit_code': result.returncode, 'environment_overrides': {
            k: env[k] for k in ['PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING', 'TEMP', 'TMP']},
    })
    print(json.dumps({'step': name, 'exit_code': result.returncode, 'evidence': stem}))
    sys.stdout.write(result.stdout.decode('utf-8', errors='replace'))
    sys.stdout.write(result.stderr.decode('utf-8', errors='replace'))
    raise SystemExit(result.returncode)

def audit():
    before = json.loads((LOGS / 'source-before.json').read_text(encoding='utf-8'))
    after = snapshot(SOURCE)
    write_json(LOGS / 'source-after.json', after)
    differences = [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
    copy_before = json.loads((LOGS / 'copy-before.json').read_text(encoding='utf-8'))
    copied_changes = []
    for name, item in copy_before.items():
        target = COPY / name
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
            copied_changes.append(name)
    copied_originals = {name: hashlib.sha256((COPY/name).read_bytes()).hexdigest() for name in before
                        if name.startswith('inputs/') or name in ['existing-product.txt', 'inputs.sha256.json']}
    core = '.elenchus/lab/R001/main/photo_materials.py'
    result = {
        'source_file_count': len(before), 'source_unchanged_content_size_mtime': before == after,
        'source_differences': differences, 'copied_existing_files_with_content_changes': copied_changes,
        'copied_protected_files': len(copied_originals),
        'copied_protected_sha_matches_source': all(before[n]['sha256'] == sha for n, sha in copied_originals.items()),
        'core_sha256': before[core]['sha256'],
        'copied_core_unchanged': hashlib.sha256((COPY/core).read_bytes()).hexdigest() == before[core]['sha256'],
    }
    write_json(LOGS / 'preservation-audit.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if differences or not result['copied_protected_sha_matches_source'] or not result['copied_core_unchanged']:
        raise SystemExit(1)

if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'init':
        initialize()
    elif action == 'run':
        run(sys.argv[2])
    elif action == 'audit':
        audit()
    else:
        raise SystemExit('unknown action')
