"""Small executor-written public activity recorder; no environment capture."""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parents[5] / 'records' / 'activity.jsonl'

def record(kind, query, result, artifacts=()):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'time': datetime.now(timezone.utc).isoformat(), 'kind': kind,
            'query_or_command': query, 'result': result, 'artifacts': list(artifacts)}, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    import sys
    record(*sys.argv[1:4])
