"""Prepare an explicitly selected material set, withholding actor/replay logs.

Post-export correction added before the first independent reproduction. It does
not alter the frozen actor inputs, original harness, or exported evidence.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import harness


def prepare(export_dir: Path, workspace: Path, materials: list[str]) -> dict:
    integrity = harness.verify(export_dir)
    if integrity['status'] != 'verified' or integrity['collection_status'] != 'complete_allowlist_copy':
        raise ValueError('complete verified export required')
    if not integrity['initial_files_unchanged']:
        raise ValueError('protected original inputs changed')
    if workspace.exists():
        raise ValueError('reproduction workspace already exists; preserve earlier attempt')
    if not materials or len(materials) != len(set(materials)):
        raise ValueError('nonempty unique material selection required')
    contents = {}
    for name in materials:
        name = harness.safe_relative(name)
        if not name.startswith('project/'):
            raise ValueError('only project materials may enter reproduction')
        parts = Path(name).parts
        if (Path(name).name == 'activity.jsonl' or Path(name).suffix == '.log'
                or any(p.startswith('reproduction') or p == 'verification' for p in parts)):
            raise ValueError('actor activity and prior replay records are withheld')
        contents[name] = harness.checked_path(export_dir / 'artifacts', name).read_bytes()
    prompt = (export_dir / 'reproduction-input.md').read_bytes()
    record = harness.load(export_dir / 'export.json')
    if harness.sha(prompt) != record['reproduction_input']['expected_sha256']:
        raise ValueError('frozen reproduction prompt mismatch')
    workspace.mkdir(parents=True)
    for name, data in contents.items():
        harness.write(workspace / name, data)
    harness.write(workspace / 'input.md', prompt)
    return {
        'created_utc': harness.stamp(), 'source_run': record['run_id'],
        'source_export_sha256': harness.sha((export_dir / 'export.json').read_bytes()),
        'preparer_sha256': harness.sha(Path(__file__).read_bytes()),
        'reproduction_input_sha256': harness.sha(prompt),
        'selected_materials': {name: harness.sha(data) for name, data in sorted(contents.items())},
        'withheld_project_files': sorted(name for name in record['files'] if name.startswith('project/') and name not in contents),
        'actor_activity_and_observer_records_provided': False,
        'scope': 'Operator selected code/data/tests/docs; original HANDOFF and Research may describe earlier results. No original conversation or actor activity/prior replay records supplied.',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--materials', type=Path, required=True)
    p.add_argument('--record', type=Path, required=True)
    args = p.parse_args()
    if args.record.exists():
        raise ValueError('reproduction preparation record already exists')
    result = prepare(args.export, args.workspace, harness.load(args.materials))
    harness.write(args.record, harness.json_bytes(result))
    print(json.dumps({'status': 'prepared', 'materials': len(result['selected_materials']),
                      'withheld': len(result['withheld_project_files']), 'input_sha256': result['reproduction_input_sha256']}))


if __name__ == '__main__':
    main()
