"""Offline regression tests; modified payloads and HTTP failures are synthetic."""
import copy
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError

import weather_pipeline as weather

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT.parent / 'R001' / 'samples' / 'seoul-era5-si.json'
IMPERIAL = ROOT.parent / 'R001' / 'adapter-samples' / '20260908T081157522643Z-cd887096aaff.json'


class WeatherTests(unittest.TestCase):
    def setUp(self):
        temp_root = ROOT / 'test-output'
        temp_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'test.sqlite'
        self.payload = weather.read_json(FIXTURE.read_bytes())

    def save(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        file = self.root / 'synthetic.json'
        file.write_bytes(body)
        meta = weather.read_json(FIXTURE.with_suffix('.meta.json').read_bytes())
        meta['sha256'] = hashlib.sha256(body).hexdigest()
        meta['synthetic_test_input'] = True
        file.with_suffix('.meta.json').write_text(json.dumps(meta), encoding='utf-8')
        return file

    def ingest(self, payload=None):
        return weather.ingest(FIXTURE if payload is None else self.save(payload), self.db)

    def query(self, identity, start='2024-01-01T00:00Z', end='2024-01-03T00:00Z', zone='UTC'):
        return weather.query_data(self.db, identity, start, end, zone)

    def test_real_response_round_trip_and_reingestion(self):
        first, second = self.ingest(), self.ingest()
        self.assertTrue(first['inserted'])
        self.assertFalse(second['inserted'])
        result = self.query(first['dataset_id'])
        self.assertEqual(len(result['rows']), 48)
        self.assertEqual(result['rows'][0]['epoch_utc'], 1704067200)
        self.assertEqual(result['rows'][0]['temperature_c'], 0)
        self.assertAlmostEqual(result['summary']['precipitation_observed_sum_mm'], .1)
        self.assertTrue(result['summary']['precipitation_labels_complete'])

    def test_real_imperial_agrees_with_si_with_provider_rounding(self):
        canonical = weather.normalize(self.payload)
        imperial = weather.normalize(weather.read_json(IMPERIAL.read_bytes()))
        self.assertEqual([r[0] for r in canonical], [r[0] for r in imperial])
        # Returned values are rounded independently by the provider in each unit.
        for si, other in zip(canonical, imperial):
            for index, tolerance in ((1, .08), (2, .02), (3, .03)):
                self.assertAlmostEqual(si[index], other[index], delta=tolerance)

    def test_null_and_zero_remain_distinct(self):
        self.payload['hourly']['temperature_2m'][0] = None
        self.payload['hourly']['precipitation'][1] = None
        record = self.ingest(self.payload)
        result = self.query(record['dataset_id'])
        self.assertIsNone(result['rows'][0]['temperature_c'])
        self.assertEqual(result['rows'][0]['precipitation_mm'], 0)
        self.assertIsNone(result['rows'][1]['precipitation_mm'])
        self.assertEqual(result['summary']['temperature_valid_count'], 47)
        self.assertFalse(result['summary']['precipitation_labels_complete'])

    def test_all_missing_is_not_zero_aggregate(self):
        self.payload['hourly']['precipitation'] = [None] * 48
        result = self.query(self.ingest(self.payload)['dataset_id'])
        self.assertIsNone(result['summary']['precipitation_observed_sum_mm'])
        self.assertEqual(result['summary']['precipitation_valid_count'], 0)

    def test_missing_timestamp_flag_without_interpolation(self):
        for values in self.payload['hourly'].values():
            del values[4]
        rows = weather.normalize(self.payload)
        self.assertEqual(len(rows), 48)
        self.assertEqual(rows[4][1:], (None, None, None, 'missing_timestamp'))

    def test_unknown_unit_and_malformed_arrays_do_not_change_database(self):
        self.ingest()
        for broken in ('unit', 'length', 'number', 'negative'):
            bad = copy.deepcopy(self.payload)
            if broken == 'unit':
                bad['hourly_units']['temperature_2m'] = 'kelvin'
            elif broken == 'length':
                bad['hourly']['precipitation'].pop()
            elif broken == 'number':
                bad['hourly']['temperature_2m'][0] = 'NA'
            else:
                bad['hourly']['precipitation'][0] = -9999
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                self.ingest(bad)
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM datasets').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM hourly').fetchone()[0], 48)

    def test_duplicate_or_ambiguous_times_are_rejected(self):
        self.payload['hourly']['time'][1] = self.payload['hourly']['time'][0]
        with self.assertRaises(ValueError):
            weather.normalize(self.payload)
        self.payload['hourly_units']['time'] = 'iso8601'
        with self.assertRaises(ValueError):
            weather.normalize(self.payload)

    def test_nonstandard_json_numbers_rejected(self):
        for value in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                weather.read_json('{"value":' + value + '}')

    def test_empty_response_has_no_fabricated_values(self):
        for field in self.payload['hourly']:
            self.payload['hourly'][field] = []
        result = self.query(self.ingest(self.payload)['dataset_id'])
        self.assertEqual(result['rows'], [])
        self.assertIsNone(result['summary']['temperature_mean_c'])
        self.assertFalse(result['summary']['precipitation_labels_complete'])

    def test_changed_response_retains_distinct_snapshot(self):
        first = self.ingest()
        self.payload['hourly']['temperature_2m'][0] = 2.5
        second = self.ingest(self.payload)
        self.assertNotEqual(first['dataset_id'], second['dataset_id'])
        self.assertEqual(self.query(first['dataset_id'])['rows'][0]['temperature_c'], 0)
        self.assertEqual(self.query(second['dataset_id'])['rows'][0]['temperature_c'], 2.5)

    def test_tampered_raw_hash_is_rejected_before_write(self):
        path = self.save(self.payload)
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'hash'):
            weather.ingest(path, self.db)
        self.assertFalse(self.db.exists())

    def test_korean_day_uses_explicit_offset_bounds(self):
        record = self.ingest()
        result = self.query(record['dataset_id'], '2024-01-02T00:00+09:00', '2024-01-03T00:00+09:00', 'Asia/Seoul')
        self.assertEqual(len(result['rows']), 24)
        self.assertEqual(result['rows'][0]['time_local'], '2024-01-02T00:00:00+09:00')
        self.assertEqual(result['rows'][0]['epoch_utc'], 1704121200)
        self.assertEqual(result['rows'][0]['precipitation_period_start_utc'], 1704117600)

    def test_dst_fall_back_preserves_two_instants(self):
        for key in self.payload['hourly']:
            self.payload['hourly'][key] = self.payload['hourly'][key][:2]
        self.payload['hourly']['time'] = [1730610000, 1730613600]  # 05:00 / 06:00Z
        record = self.ingest(self.payload)
        result = self.query(record['dataset_id'], '2024-11-03T05:00Z', '2024-11-03T07:00Z', 'America/New_York')
        self.assertEqual([r['time_local'] for r in result['rows']],
                         ['2024-11-03T01:00:00-04:00', '2024-11-03T01:00:00-05:00'])

    def test_naive_query_bounds_rejected(self):
        with self.assertRaisesRegex(ValueError, 'offset'):
            weather.aware_epoch('2024-01-01T00:00')

    def test_strict_table_rejects_text_measurement(self):
        record = self.ingest()
        with closing(sqlite3.connect(self.db)) as connection, self.assertRaises(sqlite3.IntegrityError):
            connection.execute('UPDATE hourly SET temperature_c=? WHERE dataset_id=?', ('NA', record['dataset_id']))

    def test_incomplete_edge_window_not_marked_complete(self):
        record = self.ingest()
        result = self.query(record['dataset_id'], '2023-12-31T00:00Z', '2024-01-03T00:00Z')
        self.assertEqual(result['summary']['expected_hours'], 72)
        self.assertFalse(result['summary']['precipitation_labels_complete'])

    def test_http_429_retry_then_success_and_400_no_retry(self):
        url = weather.request_url(37.5665, 126.978, '2024-01-01', '2024-01-02')
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = FIXTURE.read_bytes()
        response.status, response.headers = 200, {'Content-Type': 'application/json'}
        error = HTTPError(url, 429, 'limited', {'Retry-After': '0'}, io.BytesIO(b'limit'))
        opener, sleep = Mock(side_effect=[error, response]), Mock()
        raw = weather.fetch(url, self.root / 'fetch', opener=opener, sleeper=sleep)
        self.assertEqual(raw.read_bytes(), FIXTURE.read_bytes())
        self.assertEqual(opener.call_count, 2)
        sleep.assert_called_once_with(0)
        for status, delay in ((400, '0'), (429, '60')):
            error = HTTPError(url, status, 'error', {'Retry-After': delay}, io.BytesIO(b'error'))
            opener = Mock(side_effect=error)
            with self.assertRaises(RuntimeError):
                weather.fetch(url, self.root / 'failure', opener=opener, sleeper=Mock())
            self.assertEqual(opener.call_count, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
