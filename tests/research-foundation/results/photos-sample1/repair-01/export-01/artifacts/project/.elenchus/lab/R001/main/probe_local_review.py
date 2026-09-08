"""Exercise scanner and review output with Python socket entry points denied.

This is a runtime dependency check, not an OS-level network sandbox proof.
"""
import hashlib
import json
from pathlib import Path
import socket
from unittest.mock import patch

import photo_materials
from render_review import render_review, orientation_interpretation
from generate_fixtures import generate
from review_contract import compare_reports

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
baseline=json.loads((HERE/'original-before.json').read_text(encoding='utf-8'))
def originals():
    return {name:hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in baseline}
before=originals()
calls=[]
def no_network(*args,**kwargs):
    calls.append('socket entry point attempted')
    raise AssertionError('local analysis must not require network')
with patch.object(socket,'socket',no_network),patch.object(socket,'create_connection',no_network),patch.object(socket,'getaddrinfo',no_network):
    report=photo_materials.scan_directory(PROJECT/'inputs')
    rendered=render_review(report)
    repeated=render_review(photo_materials.scan_directory(PROJECT/'inputs'))
    fixture=HERE/'fixtures/offset-date.jpg'
    if not fixture.exists():
        generate(HERE/'fixtures')
    fraction_row={'path':'offset-date.jpg',**photo_materials.inspect_bytes(fixture.read_bytes(),'.jpg')}
    fraction_report={**report,'records':[fraction_row],'exact_groups':[],
        'candidates':photo_materials.build_candidates([fraction_row],[])}
    fraction_rendered=render_review(fraction_report)
rows={row['path']:row for row in report['records']}
comparison=compare_reports(report,json.loads((HERE/'sample-report-final.json').read_text(encoding='utf-8')))
checks={
    'no_python_network_entry_points_used':not calls,
    'portable_scanner_output_matches_verified_sample':comparison['portable_equal'],
    'filesystem_mtime_values_reflect_current_inputs':all(row['filesystem_mtime_ns']==(PROJECT/'inputs'/row['path']).stat().st_mtime_ns for row in report['records']),
    'local_review_deterministic':rendered==repeated,
    'matches_saved_review':rendered==(HERE/'review.md').read_text(encoding='utf-8'),
    'original_ten_files_unchanged':before==originals()==baseline,
    'date_day_groups_present':'### 2024-07-15' in rendered and '### 날짜 미지정' in rendered,
    'only_dated_pair_assigned_day':{candidate['path'] for candidate in report['candidates'] if candidate['date_bucket']}=={'copies/duplicate.jpg','session A/dated.jpg'},
    'raw6_interpreted_clockwise90':rows['회전/rotated.jpg']['orientation']==6 and orientation_interpretation(rows['회전/rotated.jpg'])=='시계 방향 90도 회전',
    'raw8_interpreted_counterclockwise90':rows['formats/sample.tiff']['orientation']==8 and orientation_interpretation(rows['formats/sample.tiff'])=='반시계 방향 90도 회전',
    'tiff_actual_display_and_raw_dimensions_distinct':rows['formats/sample.tiff']['encoded_size']==[8,6] and rows['formats/sample.tiff']['display_size']==[6,8],
    'all_candidates_review_only':all(row['action']=='review_only' for row in report['candidates']),
    'synthetic_subsecond_evidence_visible':'subsec=123456789' in fraction_rendered,
}
result={'checks':checks,'network_calls':calls,'summary':report['summary'],
        'snapshot_comparison':comparison,
        'review_sha256':hashlib.sha256(rendered.encode('utf-8')).hexdigest(),
        'scope':'Python socket entry points denied during existing local scan and Markdown rendering; not OS network isolation proof'}
(HERE/'local-review-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'passed':sum(checks.values()),'network_calls':len(calls)}))
if not all(checks.values()):
    raise SystemExit(1)
