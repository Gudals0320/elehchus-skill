"""Regression for real file copies with equal bytes and different mtimes."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import photo_materials
from review_contract import compare_reports

HERE = Path(__file__).resolve().parent
INPUTS = HERE.parents[3] / 'inputs'


def bytes_hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class PortableReviewTests(unittest.TestCase):
    def test_copied_inputs_with_changed_mtimes_preserve_semantics_and_live_values(self):
        original_hashes = bytes_hashes(INPUTS)
        report = photo_materials.scan_directory(INPUTS)
        with tempfile.TemporaryDirectory(prefix='photo-mtime-') as tmp:
            clone = Path(tmp) / 'inputs'
            shutil.copytree(INPUTS, clone)
            for p in clone.rglob('*'):
                if p.is_file():
                    info = p.stat()
                    os.utime(p, ns=(info.st_atime_ns, info.st_mtime_ns + 10_000_000_000))
            replay = photo_materials.scan_directory(clone)
            self.assertNotEqual(replay, report)
            compared = compare_reports(replay, report)
            self.assertTrue(compared['portable_equal'])
            self.assertEqual(len(compared['filesystem_mtime_differences']), 8)
            for row in replay['records']:
                self.assertEqual(row['filesystem_mtime_ns'], (clone / row['path']).stat().st_mtime_ns)
            self.assertEqual(bytes_hashes(clone), original_hashes)
        self.assertEqual(bytes_hashes(INPUTS), original_hashes)

    def test_real_same_length_byte_change_is_still_detected(self):
        report = photo_materials.scan_directory(INPUTS)
        with tempfile.TemporaryDirectory(prefix='photo-content-') as tmp:
            clone = Path(tmp) / 'inputs'
            shutil.copytree(INPUTS, clone)
            target = clone / 'README.md'
            data = target.read_bytes()
            target.write_bytes(bytes([data[0] ^ 1]) + data[1:])
            self.assertFalse(compare_reports(photo_materials.scan_directory(clone), report)['portable_equal'])

    def test_semantic_date_change_and_missing_timestamp_field_are_not_masked(self):
        report = photo_materials.scan_directory(INPUTS)
        changed = deepcopy(report)
        changed['candidates'][0]['date_bucket'] = '1900-01-01'
        self.assertFalse(compare_reports(changed, report)['portable_equal'])
        changed = deepcopy(report)
        del changed['records'][0]['filesystem_mtime_ns']
        self.assertFalse(compare_reports(changed, report)['portable_equal'])


if __name__ == '__main__':
    unittest.main()
