"""A replay must receive selected materials, not nested actor activity logs."""
from pathlib import Path
import tempfile
import unittest

import harness
import prepare_reproduction


class SelectedReproductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.export = self.root / 'export'
        self.code = 'project/.elenchus/lab/R001/tool.py'
        self.log = 'project/.elenchus/lab/R001/activity.jsonl'
        prompt = b'Replay the supplied materials.'
        files = {self.code: b"print(42)\n", self.log: b'{"claim":"passed"}\n'}
        for name, data in files.items():
            harness.write(self.export / 'artifacts' / name, data)
        harness.write(self.export / 'reproduction-input.md', prompt)
        harness.write(self.export / 'export.json', harness.json_bytes({
            'run_id': 'sample', 'status': 'complete_allowlist_copy', 'initial_files_unchanged': True,
            'reproduction_input': {'status': 'copied_fixed_input', 'expected_sha256': harness.sha(prompt), 'published_sha256': harness.sha(prompt)},
            'files': {name: {'published_sha256': harness.sha(data)} for name, data in files.items()},
        }))

    def test_selected_code_is_exact_and_nested_actor_log_not_provided(self):
        target = self.root / 'replay'
        result = prepare_reproduction.prepare(self.export, target, [self.code])
        self.assertEqual((target / self.code).read_bytes(), b'print(42)\n')
        self.assertFalse((target / self.log).exists())
        self.assertEqual(result['withheld_project_files'], [self.log])
        self.assertFalse(result['actor_activity_and_observer_records_provided'])

    def test_logs_and_paths_outside_project_rejected_before_copy(self):
        for name in (self.log, 'records/final.md', '../outside.py', 'project/reproduction-old/summary.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                prepare_reproduction.prepare(self.export, self.root / 'replay', [name])
            self.assertFalse((self.root / 'replay').exists())

    def test_mutated_prompt_rejected(self):
        (self.export / 'reproduction-input.md').write_bytes(b'changed prompt')
        with self.assertRaises(ValueError):
            prepare_reproduction.prepare(self.export, self.root / 'replay', [self.code])

    def test_partial_or_changed_original_export_not_presented_as_clean_replay(self):
        for changed in ({'status': 'partial_collection'}, {'initial_files_unchanged': False}):
            record = harness.load(self.export / 'export.json')
            record.update({'status': 'complete_allowlist_copy', 'initial_files_unchanged': True}, **changed)
            (self.export / 'export.json').write_bytes(harness.json_bytes(record))
            with self.assertRaises(ValueError):
                prepare_reproduction.prepare(self.export, self.root / 'replay', [self.code])


if __name__ == '__main__':
    unittest.main()
