import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import photo_materials as pm
from generate_fixtures import generate

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]


class MaterialsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = generate(HERE/'fixtures')
        cls.actual = pm.scan_directory(PROJECT/'inputs')
        cls.rows = {r['path']:r for r in cls.actual['records']}
        cls.candidates = {r['path']:r for r in cls.actual['candidates']}

    def inspect(self, name, **kwargs):
        path = self.fixture/name
        return pm.inspect_bytes(path.read_bytes(), path.suffix, **kwargs)

    def scratch(self):
        root = HERE/'test-runs'
        root.mkdir(exist_ok=True)
        return Path(tempfile.mkdtemp(dir=root))

    def test_inputs_and_product_unchanged(self):
        before = json.loads((HERE/'original-before.json').read_text(encoding='utf-8'))
        for name, digest in before.items():
            self.assertEqual(hashlib.sha256((PROJECT/name).read_bytes()).hexdigest(), digest, name)
        expected = json.loads((PROJECT/'inputs.sha256.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(len(expected), 8)
        for name,digest in expected.items():
            self.assertEqual(hashlib.sha256((PROJECT/'inputs'/name).read_bytes()).hexdigest(), digest)

    def test_all_inputs_and_actual_duplicate(self):
        self.assertEqual(self.actual['summary']['statuses'], {'invalid_image':1,'non_image_or_unsupported':2,'ok':5})
        self.assertEqual(len(self.actual['exact_groups']),1)
        self.assertEqual(self.actual['exact_groups'][0]['members'], ['copies/duplicate.jpg','session A/dated.jpg'])

    def test_actual_date_offset_and_no_mtime_fallback(self):
        capture = self.rows['session A/dated.jpg']['capture']
        self.assertEqual(capture['utc'],'2024-07-15T01:20:30Z')
        self.assertEqual(capture['source'],'ExifIFD.DateTimeOriginal')
        self.assertEqual(self.candidates['plain.png']['date_bucket'],None)
        self.assertEqual(self.candidates['formats/sample.tiff']['date_bucket'],None)
        self.assertEqual(self.rows['formats/sample.tiff']['dates'][0]['meaning'],'modified')

    def test_png_metadata_verify_order_regression(self):
        row = self.rows['plain.png']
        self.assertEqual((row['metadata_status'],row['verify_status'],row['decode_status']),('ok','passed','passed'))

    def test_actual_tiff_not_double_rotated(self):
        row = self.rows['formats/sample.tiff']
        self.assertEqual((row['orientation'],row['encoded_size'],row['display_size']),(8,[8,6],[6,8]))
        self.assertEqual(self.rows['회전/rotated.jpg']['display_size'],[6,8])

    def test_all_eight_orientation_sizes_png_and_tiff(self):
        for fmt in ('png','tiff'):
            for orientation in range(1,9):
                with self.subTest(fmt=fmt,orientation=orientation):
                    row = self.inspect(f'orientation-{orientation}.{fmt}')
                    self.assertEqual(row['status'],'ok')
                    self.assertEqual(row['orientation'],orientation)
                    self.assertEqual(row['encoded_size'],[3,2])
                    self.assertEqual(row['display_size'],[2,3] if orientation>=5 else [3,2])

    def test_invalid_orientation_is_explicit(self):
        self.assertEqual(self.inspect('invalid-orientation.png')['orientation_status'],'invalid')

    def test_invalid_and_zero_date(self):
        for name in ('bad-date.jpg','zero-date.jpg'):
            self.assertEqual(self.inspect(name)['capture']['status'],'invalid_date')

    def test_unknown_offset_not_assumed(self):
        capture = self.inspect('naive-date.jpg')['capture']
        self.assertEqual(capture['status'],'timezone_unknown')
        self.assertIsNone(capture['utc'])

    def test_offset_crosses_day_retains_subseconds(self):
        capture = self.inspect('offset-date.jpg')['capture']
        self.assertEqual(capture['utc'],'2024-07-14T15:10:00.123456789Z')
        candidate = pm.build_candidates([{'path':'a',**self.inspect('offset-date.jpg')}],[])[0]
        self.assertEqual(candidate['date_bucket'],'2024-07-15')

    def test_invalid_offset_and_subsecond(self):
        self.assertEqual(self.inspect('bad-offset.jpg')['capture']['status'],'invalid_offset')
        self.assertIn('invalid_subsecond',pm.parse_exif_date('2024:01:01 00:00:00',None,'xx')['warnings'])

    def test_conflicting_ifd_dates_not_grouped(self):
        row = self.inspect('conflicting-date.jpg')
        self.assertEqual(row['capture']['status'],'conflict')
        self.assertIsNone(pm.build_candidates([{'path':'a',**row}],[])[0]['date_bucket'])

    def test_digitized_and_modified_not_capture(self):
        for name in ('digitized-only.jpg','modified-only.tiff'):
            self.assertIsNone(self.inspect(name)['capture'])

    def test_ifd0_modified_date_pairs_exif_ifd_offset(self):
        row=self.inspect('modified-offset.jpg')
        self.assertEqual(row['dates'][0]['utc'],'2024-07-14T15:10:00.25Z')
        self.assertEqual(row['dates'][0]['meaning'],'modified')
        self.assertIsNone(row['capture'])

    def test_content_format_over_extension(self):
        row = self.inspect('filename-is-wrong.jpg')
        self.assertEqual(row['format'],'PNG')
        self.assertEqual(row['status'],'ok')
        self.assertIn('extension_format_mismatch',row['warnings'])

    def test_jpeg_verify_pass_does_not_guarantee_decode(self):
        row = self.inspect('missing-jpeg-eoi.jpg')
        self.assertEqual(row['verify_status'],'passed')
        self.assertEqual(row['decode_status'],'failed')
        self.assertEqual(row['status'],'invalid_image')

    def test_bad_png_crc_rejected(self):
        row = self.inspect('bad-png-crc.png')
        self.assertEqual(row['status'],'invalid_image')
        self.assertTrue(row['errors'])

    def test_multiframe_all_frames_or_explicit_limit(self):
        row = self.inspect('two-frame.tiff')
        self.assertEqual(row['validated_frames'],2)
        self.assertEqual(row['status'],'ok')
        self.assertEqual(self.inspect('two-frame.tiff',max_frames=1)['status'],'resource_limit')

    def test_pixel_file_and_total_limits(self):
        self.assertEqual(self.inspect('plain.png',max_pixels=2)['status'],'resource_limit')
        scan = pm.scan_directory(PROJECT/'inputs',max_file_bytes=1)
        self.assertEqual(scan['summary']['statuses'],{'file_size_limit':8})
        scan = pm.scan_directory(PROJECT/'inputs',max_total_bytes=1)
        self.assertEqual(scan['summary']['statuses'],{'corpus_size_limit':8})

    def test_unrecognized_is_not_false_codec_diagnosis(self):
        self.assertEqual(self.inspect('pretend.heic')['status'],'unrecognized_image')
        self.assertEqual(self.inspect('empty.jpg')['status'],'unrecognized_image')

    def test_metadata_only_change_not_exact(self):
        a,b = [self.fixture/name for name in ('metadata-a.png','metadata-b.png')]
        with Image.open(a) as x, Image.open(b) as y:
            self.assertEqual(x.tobytes(),y.tobytes())
        self.assertNotEqual(a.read_bytes(),b.read_bytes())
        root = self.scratch()
        (root/'a.png').write_bytes(a.read_bytes())
        (root/'b.png').write_bytes(b.read_bytes())
        self.assertEqual(pm.scan_directory(root)['exact_groups'],[])

    def test_hash_collision_still_requires_equal_bytes(self):
        rows=[{'path':x,'size':1,'sha256':'forced_collision'} for x in ('a','b','c')]
        groups=pm.exact_groups(rows,{'a':b'a','b':b'b','c':b'a'})
        self.assertEqual(groups[0]['members'],['a','c'])

    def test_hardlink_is_alias_not_extra_copy(self):
        root=self.scratch()
        (root/'a.png').write_bytes((self.fixture/'plain.png').read_bytes())
        try:
            os.link(root/'a.png',root/'b.png')
        except OSError as exc:
            self.skipTest(f'hardlink unavailable: {exc}')
        scan=pm.scan_directory(root)
        self.assertEqual(scan['records'][1]['status'],'same_file_alias')
        self.assertEqual(scan['exact_groups'],[])

    def test_change_after_enumeration_detected(self):
        root=self.scratch()
        (root/'a.txt').write_bytes(b'first')
        original=pm._walk
        def changed(directory):
            for path,st,skip in original(directory):
                path.write_bytes(b'changed length')
                yield path,st,skip
        with patch.object(pm,'_walk',changed):
            scan=pm.scan_directory(root)
        self.assertEqual(scan['records'][0]['status'],'changed_during_read')
        self.assertIsNone(scan['records'][0]['sha256'])

    def test_read_error_isolated(self):
        root=self.scratch()
        (root/'a.png').write_bytes((self.fixture/'plain.png').read_bytes())
        (root/'b.png').write_bytes((self.fixture/'plain.png').read_bytes())
        original=Path.open
        def denied(path,*args,**kwargs):
            if path.name=='a.png':
                raise PermissionError('injected unreadable fixture')
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',denied):
            result=pm.scan_directory(root)
        self.assertEqual([r['status'] for r in result['records']],['io_error','ok'])

    def test_symlink_skipped_when_platform_allows(self):
        root=self.scratch()
        (root/'a.png').write_bytes((self.fixture/'plain.png').read_bytes())
        try:
            os.symlink(root/'a.png',root/'b.png')
        except OSError as exc:
            self.skipTest(f'symlink unavailable: {exc}')
        result=pm.scan_directory(root)
        self.assertEqual(result['records'][1]['status'],'skipped_link')
        self.assertEqual(result['exact_groups'],[])

    def test_repeatability_and_empty(self):
        self.assertEqual(self.actual,pm.scan_directory(PROJECT/'inputs'))
        self.assertEqual(pm.scan_directory(self.scratch())['summary']['files'],0)

    def test_cli_output_guard_and_no_overwrite(self):
        root=self.scratch()
        command=[sys.executable,'-B',str(HERE/'photo_materials.py'),str(root)]
        inside=root/'report.json'
        denied=subprocess.run(command+['--output',str(inside)],capture_output=True,text=True)
        self.assertNotEqual(denied.returncode,0)
        self.assertFalse(inside.exists())
        outside=self.scratch()/'report.json'
        ok=subprocess.run(command+['--output',str(outside)],capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr)
        before=outside.read_bytes()
        denied=subprocess.run(command+['--output',str(outside)],capture_output=True,text=True)
        self.assertNotEqual(denied.returncode,0)
        self.assertEqual(outside.read_bytes(),before)


if __name__=='__main__':
    unittest.main(verbosity=2)
