"""Compare replay evidence without changing supplied or copied product code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'project'
COPY = ROOT / 'execution/project'
REL = Path('.elenchus/lab/R001/main')
MAIN = COPY / REL

def differences(left, right, path=''):
    if type(left) is not type(right):
        return [{'field': path, 'saved': left, 'replayed': right}]
    if isinstance(left, dict):
        found = []
        for key in sorted(left.keys() | right.keys()):
            found.extend(differences(left.get(key), right.get(key), f'{path}.{key}' if path else key))
        return found
    if isinstance(left, list) and len(left) == len(right):
        found = []
        for index, (a, b) in enumerate(zip(left, right)):
            found.extend(differences(a, b, f'{path}[{index}]'))
        return found
    return [] if left == right else [{'field': path, 'saved': left, 'replayed': right}]

saved = json.loads((SOURCE/REL/'sample-report-final.json').read_text(encoding='utf-8'))
live = json.loads((MAIN/'my-report.json').read_text(encoding='utf-8'))
delta = differences(saved, live)
checks = json.loads((MAIN/'local-review-results.json').read_text(encoding='utf-8'))
paths = [
    '.elenchus/lab/R001/main/tests-ifd-final.log',
    '.elenchus/lab/R001/main/tests-first.log',
    '.elenchus/lab/R001/metadata-research/reproduction/notes.md',
    '.elenchus/lab/R001/metadata-research/reproduction/audit-results.json',
    '.elenchus/lab/R001/metadata-research/reproduction/local-review-notes.md',
    '.elenchus/lab/R002/identity-research/junction-fixtures/source/linked-target',
]
result = {
    'saved_vs_replay_equal': saved == live,
    'saved_vs_replay_differences': delta,
    'all_differences_are_filesystem_mtime_ns': bool(delta) and all(d['field'].endswith('.filesystem_mtime_ns') for d in delta),
    'local_review_failed_checks': [key for key, value in checks['checks'].items() if not value],
    'local_review_network_calls': checks['network_calls'],
    'rendered_review_equals_saved_text': (MAIN/'my-review.md').read_text(encoding='utf-8') == (SOURCE/REL/'review.md').read_text(encoding='utf-8'),
    'input_and_saved_report_mtime': [
        {'path': row['path'], 'source_input_mtime_ns': (SOURCE/'inputs'/row['path']).stat().st_mtime_ns,
         'copied_input_mtime_ns': (COPY/'inputs'/row['path']).stat().st_mtime_ns,
         'saved_report_mtime_ns': row['filesystem_mtime_ns']}
        for row in saved['records']
    ],
    'referenced_artifacts_exist': {name:(SOURCE/name).exists() for name in paths},
    'representative_summary': live['summary'],
    'exact_groups': live['exact_groups'],
    'candidate_date_buckets': {c['path']:c['date_bucket'] for c in live['candidates']},
    'generated_review_sha256_bytes': hashlib.sha256((MAIN/'my-review.md').read_bytes()).hexdigest(),
}
(ROOT/'evidence/report-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
