"""Build a portable research-material archive without environments/caches."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1]
out = ROOT / 'delivery'
out.mkdir(exist_ok=True)
excluded = {'.venv', '.pip-cache', '__pycache__', 'test-runs', 'delivery'}
files = [p for p in BASE.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(BASE).parts)]
manifest = dict(created_at=datetime.now(timezone.utc).isoformat(),
                entrypoint='.elenchus/lab/R002/README.md',
                note='Generated research materials only. No environment, package cache, credentials, or original product files.',
                files={'.elenchus/' + p.relative_to(BASE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
target = out / 'weather-materials.zip'
with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, '.elenchus/' + path.relative_to(BASE).as_posix())
    archive.writestr('MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
with ZipFile(target) as archive:
    assert archive.testzip() is None
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == digest, name
(out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(archive=str(target), bytes=target.stat().st_size, files=len(files),
                     sha256=hashlib.sha256(target.read_bytes()).hexdigest()), indent=2))
