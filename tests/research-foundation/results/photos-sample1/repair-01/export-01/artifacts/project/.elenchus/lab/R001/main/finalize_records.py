"""Index only this task's public evidence and selected reusable material hashes."""
import hashlib
import json
from pathlib import Path
from activity import record, LOG

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
records=PROJECT.parent/'records'
sources=[records/'metadata-activity.jsonl', records/'identity-activity.jsonl',
         PROJECT/'.elenchus/lab/R001/metadata-research/reproduction/activity.jsonl']
existing=[json.loads(line) for line in LOG.read_text(encoding='utf-8').splitlines() if line.strip()]
keys={(event.get('source_log'),event.get('source_line')) for event in existing}
count=0
with LOG.open('a',encoding='utf-8') as stream:
    for source in sources:
        if not source.exists():
            continue
        source_name=source.relative_to(PROJECT.parent).as_posix()
        for number,line in enumerate(source.read_text(encoding='utf-8-sig').splitlines(),1):
            if not line.strip() or (source_name,number) in keys:
                continue
            event=json.loads(line)
            stream.write(json.dumps({'kind':'delegated_activity','source_log':source_name,
                'source_line':number,'event':event},ensure_ascii=False)+'\n')
            count+=1

selected=list((PROJECT/'.elenchus').glob('*.md'))+list((PROJECT/'.elenchus/research').glob('*.md'))
selected+=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+[HERE/'requirements.txt',HERE/'original-before.json',
    HERE/'original-after.json',HERE/'sample-report-final.json',HERE/'tests-ifd-final.log',HERE/'local-review-results.json']
selected+=list((HERE/'fixtures').glob('*'))
for relative in ('R001/metadata-research','R002/identity-research'):
    folder=PROJECT/'.elenchus/lab'/relative
    selected+=list(folder.glob('*.py'))+list(folder.glob('*.md'))+list(folder.glob('*.json'))
manifest={path.relative_to(PROJECT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
          for path in sorted(set(selected)) if path.is_file()}
target=PROJECT/'.elenchus/material-manifest.json'
target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
record('handoff','finalize_records.py',f'Indexed {len(manifest)} material hashes and {count} delegated activity events',
       ['project/.elenchus/HANDOFF.md','project/.elenchus/material-manifest.json','records/activity.jsonl'])
print(json.dumps({'material_files':len(manifest),'delegated_events_added':count}))
