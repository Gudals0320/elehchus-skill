"""Compare all protected original contents to the captured and supplied baselines."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
baseline=json.loads((HERE/'original-before.json').read_text(encoding='utf-8'))
paths=sorted(p for p in (PROJECT/'inputs').rglob('*') if p.is_file())
paths += [PROJECT/'existing-product.txt',PROJECT/'inputs.sha256.json']
actual={p.relative_to(PROJECT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
supplied=json.loads((PROJECT/'inputs.sha256.json').read_text(encoding='utf-8-sig'))
result={'protected_files':len(actual), 'matches_before':actual==baseline,
        'matches_supplied_manifest':all(actual.get('inputs/'+p)==digest for p,digest in supplied.items()),
        'sha256':actual}
with (HERE/'original-after.json').open('w',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='sha256'}))
if not result['matches_before'] or not result['matches_supplied_manifest']:
    raise SystemExit(1)
