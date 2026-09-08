"""Independent assertions and hash audit; no writes to original project."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parents[4]
REPLICA = HERE / 'project'
MAIN_REL = Path('.elenchus/lab/R001/main')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = json.loads((HERE/'original-before-reproduction.json').read_text(encoding='utf-8-sig'))
after = {name: digest(ORIGINAL/name) for name in before}
replica = {name: digest(REPLICA/name) for name in before}
assert before == after == replica, 'Original or copied inputs/sentinel changed'
files = ('README.md', 'photo_materials.py', 'generate_fixtures.py',
         'test_photo_materials.py', 'requirements.txt', 'original-before.json')
code_hashes = {name: {'source_sha256': digest(ORIGINAL/MAIN_REL/name),
                      'replica_sha256': digest(REPLICA/MAIN_REL/name)} for name in files}
assert all(v['source_sha256'] == v['replica_sha256'] for v in code_hashes.values())
report = json.loads((REPLICA/MAIN_REL/'independent-cli-report-final.json').read_text(encoding='utf-8'))
earlier = json.loads((REPLICA/MAIN_REL/'independent-cli-report.json').read_text(encoding='utf-8'))
assert report == earlier, 'Provided sample output unexpectedly changed after IFD companion fix'
assert report['summary'] == {'files': 8, 'statuses': {'invalid_image': 1, 'non_image_or_unsupported': 2, 'ok': 5}, 'exact_groups': 1, 'snapshot_bytes': 3538}
rows = {row['path']: row for row in report['records']}
candidates = {row['path']: row for row in report['candidates']}
assert len(rows) == len(candidates) == 8
assert all(row['action'] == 'review_only' for row in candidates.values())
dated = {'session A/dated.jpg', 'copies/duplicate.jpg'}
assert {name for name,row in candidates.items() if row['date_bucket']} == dated
assert all(candidates[name]['date_bucket'] == '2024-07-15' for name in dated)
assert rows['session A/dated.jpg']['capture']['utc'] == '2024-07-15T01:20:30Z'
assert rows['formats/sample.tiff']['capture'] is None
assert rows['formats/sample.tiff']['dates'][0]['meaning'] == 'modified'
assert rows['formats/sample.tiff']['orientation'] == 8
assert rows['formats/sample.tiff']['display_size'] == [6,8]
assert rows['회전/rotated.jpg']['orientation'] == 6
assert rows['회전/rotated.jpg']['display_size'] == [6,8]
assert candidates['broken/truncated.jpg']['date_bucket'] is None
assert 'invalid_image' in candidates['broken/truncated.jpg']['review_reasons']
assert set(report['exact_groups'][0]['members']) == dated
output = {'time_utc': datetime.now(timezone.utc).isoformat(),
          'original_before': before, 'original_after': after,
          'replica_after': replica, 'original_unchanged': before == after,
          'replica_matches_original': after == replica,
          'copied_code_sha256': code_hashes, 'copied_code_matches_source': True,
          'independent_output_assertions': 'passed',
          'sample_output_unchanged_by_ifd_fix': report == earlier,
          'summary': report['summary']}
(HERE/'audit-results.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key: output[key] for key in ('original_unchanged','replica_matches_original','copied_code_matches_source','independent_output_assertions','sample_output_unchanged_by_ifd_fix','summary')}, ensure_ascii=True))
