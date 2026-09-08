import hashlib
import json
from pathlib import Path
import PIL
from PIL import Image, ExifTags, ImageOps
from activity import record

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
rows = []
before = {p.relative_to(PROJECT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted((PROJECT / 'inputs').rglob('*')) if p.is_file()}
for name in ('existing-product.txt', 'inputs.sha256.json'):
    before[name] = hashlib.sha256((PROJECT / name).read_bytes()).hexdigest()
(HERE / 'original-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
for path in sorted((PROJECT / 'inputs').rglob('*')):
    if not path.is_file():
        continue
    row = {'path': path.relative_to(PROJECT / 'inputs').as_posix()}
    try:
        with Image.open(path) as img:
            row.update(format=img.format, size=img.size, frames=getattr(img, 'n_frames', 1),
                       exif={ExifTags.TAGS.get(k, str(k)): str(v) for k,v in img.getexif().items()})
            row['exif_ifd'] = {ExifTags.TAGS.get(k,str(k)): str(v) for k,v in img.getexif().get_ifd(34665).items()}
            img.verify()
            row['verify'] = 'passed'
        with Image.open(path) as img:
            img.load()
            row['decode'] = 'passed'
            row['transposed_size'] = ImageOps.exif_transpose(img).size
    except Exception as exc:
        row['error'] = f'{type(exc).__name__}: {exc}'
    rows.append(row)
payload = {'pillow': PIL.__version__, 'rows': rows}
(HERE / 'probe-results.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(payload, ensure_ascii=True, indent=2))
record('experiment', 'main/.venv/Scripts/python.exe -B main/probe.py',
       'Pillow initial metadata/verify/load/exif_transpose probe, original hashes captured',
       ['project/.elenchus/lab/R001/main/probe-results.json', 'project/.elenchus/lab/R001/main/original-before.json'])
