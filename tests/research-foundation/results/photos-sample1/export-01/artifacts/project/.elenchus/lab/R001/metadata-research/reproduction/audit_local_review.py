"""Narrow independent audit of local review artifacts; writes only beside self."""
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parents[4]
MAIN_REL = Path('.elenchus/lab/R001/main')
COPY_MAIN = HERE/'project'/MAIN_REL
sys.dont_write_bytecode = True
sys.path.insert(0, str(COPY_MAIN))
import photo_materials
import render_review


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = json.loads((HERE/'original-before-reproduction.json').read_text(encoding='utf-8-sig'))
original_now = {name: digest(ORIGINAL/name) for name in baseline}
copy_now = {name: digest(HERE/'project'/name) for name in baseline}
report = json.loads((COPY_MAIN/'sample-report-final.json').read_text(encoding='utf-8'))
rendered = render_review.render_review(report)
written = (COPY_MAIN/'independent-local-review-final.md').read_text(encoding='utf-8')
saved = (COPY_MAIN/'review.md').read_text(encoding='utf-8')
probe = json.loads((COPY_MAIN/'local-review-results.json').read_text(encoding='utf-8'))
checks = {
    'original_ten_unchanged': baseline == original_now,
    'copy_ten_unchanged': baseline == copy_now,
    'cli_render_matches_function_and_saved_source_review': rendered == written == saved,
    'twelve_local_probe_checks_pass': len(probe['checks']) == 12 and all(probe['checks'].values()),
    'python_socket_calls_zero': probe['network_calls'] == [],
    'core_scanner_still_matches_source': digest(COPY_MAIN/'photo_materials.py') == digest(ORIGINAL/MAIN_REL/'photo_materials.py'),
}
fixture = COPY_MAIN/'fixtures'/'modified-offset.jpg'
row = photo_materials.inspect_bytes(fixture.read_bytes(), fixture.suffix)
date = row['dates'][0]
human = render_review.date_evidence(row)
subseconds = {'existing_synthetic_fixture': 'modified-offset.jpg',
              'subsecond_raw_in_json': date['subsecond_raw'],
              'date_evidence_rendered': human,
              'raw_subsecond_text_is_visible': date['subsecond_raw'] in human,
              'scope': 'Existing synthetic fixture only; supplied eight inputs have no subsecond tag.'}
result = {'time_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
          'core_scanner_sha256': digest(COPY_MAIN/'photo_materials.py'),
          'render_review_sha256': digest(COPY_MAIN/'render_review.py'),
          'probe_local_review_sha256': digest(COPY_MAIN/'probe_local_review.py'),
          'rendered_review_sha256': hashlib.sha256(rendered.encode('utf-8')).hexdigest(),
          'subsecond_evidence_review': subseconds,
          'original_after_sha256': original_now,
          'scope': 'Installed Windows Python execution; Python socket hooks only, not OS network isolation.'}
(HERE/'local-review-audit-results-final.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':checks, 'subsecond_raw_visible':subseconds['raw_subsecond_text_is_visible']},ensure_ascii=True))
if not all(checks.values()):
    raise SystemExit(1)
