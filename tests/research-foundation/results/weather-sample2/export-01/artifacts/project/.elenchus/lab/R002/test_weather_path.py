"""Offline behavior tests. Mutated cases are synthetic, fixtures are live bytes."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from urllib.error import HTTPError

import weather_path as w

ROOT = Path(__file__).resolve().parent


class WeatherPathTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((ROOT / 'fixtures/seoul-era5.json').read_bytes())
        self.meta = json.loads((ROOT / 'fixtures/seoul-era5.meta.json').read_text(encoding='utf-8'))
        temporary_root = ROOT / 'test-runs'
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.work = Path(self.temp.name)
        self.db = self.work / 'weather.sqlite'

    def tearDown(self):
        self.temp.cleanup()

    def synthetic_files(self):
        raw = json.dumps(self.payload).encode()
        self.meta['sha256'] = hashlib.sha256(raw).hexdigest()
        raw_path, meta_path = self.work / 'synthetic.json', self.work / 'synthetic.meta.json'
        raw_path.write_bytes(raw)
        meta_path.write_text(json.dumps(self.meta), encoding='utf-8')
        return raw_path, meta_path

    def ingest_synthetic(self):
        return w.ingest(*self.synthetic_files(), self.db)

    def count(self, table='measurements'):
        with closing(sqlite3.connect(self.db)) as conn:
            return conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]

    def test_actual_fixtures_end_to_end(self):
        for name in ('seoul-era5', 'seoul-era5-imperial'):
            result = w.ingest(ROOT / f'fixtures/{name}.json', ROOT / f'fixtures/{name}.meta.json', self.db)
            self.assertEqual(result['processed'], 216)
        results = w.query(self.db, display_timezone='Asia/Seoul')
        self.assertEqual(len(results['rows']), 432)
        row = next(r for r in results['rows'] if r['variable'] == 'wind_speed_10m')
        self.assertAlmostEqual(row['value'], 9.3 / 3.6)
        self.assertEqual(row['time_local'], '2025-01-01T09:00:00+09:00')
        rain = next(r for r in results['summary'] if r['variable'] == 'precipitation')
        self.assertAlmostEqual(rain['sum_available'], 190.2968)

    def test_requested_seoul_two_variables_local_calendar(self):
        raw = ROOT / 'fixtures/seoul-requested-20260901.json'
        meta = ROOT / 'fixtures/seoul-requested-20260901.meta.json'
        result = w.ingest(raw, meta, self.db)
        self.assertEqual(result['processed'], 96)
        self.assertEqual(result['missing'], 0)
        rows = w.query(self.db, display_timezone='Asia/Seoul')['rows']
        self.assertEqual(set(row['variable'] for row in rows), set(w.PRIMARY_VARIABLES))
        self.assertEqual(rows[0]['time_local'], '2026-09-01T00:00:00+09:00')
        self.assertEqual(rows[0]['time_utc'], '2026-08-31T15:00:00Z')
        self.assertEqual(rows[-1]['time_local'], '2026-09-02T23:00:00+09:00')
        self.assertEqual(w.ingest(raw, meta, self.db)['rows_total'], 96)
        with closing(sqlite3.connect(self.db)) as conn:
            metadata = json.loads(conn.execute('SELECT metadata_json FROM series').fetchone()[0])
        self.assertEqual(metadata['requested_latitude'], 37.5665)
        self.assertEqual(metadata['requested_longitude'], 126.978)
        self.assertEqual(metadata['kind'], 'reanalysis')

    def test_empty_response_preserves_previously_imported_data(self):
        self.ingest_synthetic()
        for key in self.payload['hourly']:
            self.payload['hourly'][key] = []
        with self.assertRaises(w.ContractError):
            self.ingest_synthetic()
        self.assertEqual(self.count(), 216)
        self.assertEqual(self.count('imports'), 1)

    def test_request_subset_and_timezone_metadata_validation(self):
        for variables in ((), ('precipitation', 'precipitation'), ('unknown',)):
            with self.subTest(variables=variables), self.assertRaises(w.ContractError):
                w.request_url(37.5665, 126.978, '2026-09-01', '2026-09-02', variables=variables)
        self.payload['utc_offset_seconds'] = 32400
        with self.assertRaises(w.ContractError):
            self.ingest_synthetic()

    def test_reingest_does_not_duplicate(self):
        self.ingest_synthetic()
        self.ingest_synthetic()
        self.assertEqual(self.count(), 216)
        self.assertEqual(self.count('imports'), 1)

    def test_null_is_not_zero_or_imputed(self):
        self.payload['hourly']['temperature_2m'][0] = None
        self.payload['hourly']['precipitation'][1] = None
        self.ingest_synthetic()
        rows = w.query(self.db)['rows']
        self.assertEqual(sum(r['quality'] == 'source_null' for r in rows), 2)
        self.assertEqual(sum(r['value'] is None for r in rows), 2)
        rain = [r for r in rows if r['variable'] == 'precipitation']
        self.assertEqual(rain[0]['value'], 0)
        self.assertIsNone(rain[1]['value'])

    def test_absent_timestamp_expanded_with_quality(self):
        for values in self.payload['hourly'].values():
            del values[2]
        result = self.ingest_synthetic()
        self.assertEqual(result['missing'], 3)
        self.assertEqual(result['processed'], 216)
        self.assertEqual(sum(r['quality'] == 'absent_timestamp' for r in w.query(self.db)['rows']), 3)

    def test_all_missing_aggregate_remains_null(self):
        self.payload['hourly']['precipitation'] = [None] * 72
        self.ingest_synthetic()
        rain = next(r for r in w.query(self.db)['summary'] if r['variable'] == 'precipitation')
        self.assertIsNone(rain['sum_available'])
        self.assertEqual(rain['missing'], 72)

    def test_imperial_units_reference_values(self):
        self.payload['hourly_units'].update(temperature_2m='°F', precipitation='inch', wind_speed_10m='mp/h')
        self.payload['hourly']['temperature_2m'][0] = 32
        self.payload['hourly']['precipitation'][0] = 1
        self.payload['hourly']['wind_speed_10m'][0] = 10
        self.ingest_synthetic()
        result = {r['variable']: r for r in w.query(self.db)['rows'][:3]}
        self.assertAlmostEqual(result['temperature_2m']['value'], 0)
        self.assertAlmostEqual(result['precipitation']['value'], 25.4)
        self.assertAlmostEqual(result['wind_speed_10m']['value'], 4.4704)
        self.assertEqual(result['precipitation']['source_value'], 1)

    def test_precipitation_interval_preserved(self):
        self.ingest_synthetic()
        result = {r['variable']: r for r in w.query(self.db)['rows'][:3]}
        rain = result['precipitation']
        self.assertEqual(rain['timestamp_utc'] - rain['interval_start_utc'], 3600)
        self.assertEqual(result['temperature_2m']['interval_seconds'], 0)

    def test_bad_arrays_leave_existing_database_unchanged(self):
        self.ingest_synthetic()
        self.payload['hourly']['precipitation'].pop()
        with self.assertRaises(w.ContractError):
            self.ingest_synthetic()
        self.assertEqual(self.count(), 216)
        self.assertEqual(self.count('imports'), 1)

    def test_empty_missing_duplicate_unsorted_outside_timestamps(self):
        original = self.payload['hourly']['time'].copy()
        variants = ([], [original[0]] * 72, list(reversed(original)), [original[0]-3600] + original[1:], [original[0]+1] + original[1:])
        for times in variants:
            with self.subTest(times=times[:2]):
                self.payload['hourly']['time'] = times
                with self.assertRaises(w.ContractError):
                    self.ingest_synthetic()

    def test_unsupported_unit_rejected(self):
        self.payload['hourly_units']['temperature_2m'] = 'kelvin'
        with self.assertRaises(w.ContractError):
            self.ingest_synthetic()

    def test_bad_numeric_and_unknown_sentinel_rejected(self):
        for value in (True, '12', float('nan'), float('inf'), -999):
            with self.subTest(value=value):
                self.payload['hourly']['precipitation'][0] = value
                with self.assertRaises(w.ContractError):
                    self.ingest_synthetic()

    def test_hash_mismatch_rejected(self):
        raw_path, meta_path = self.synthetic_files()
        raw_path.write_bytes(b'{}')
        with self.assertRaises(w.ContractError):
            w.ingest(raw_path, meta_path, self.db)
        self.assertFalse(self.db.exists())

    def test_naive_query_and_non_epoch_source_rejected(self):
        with self.assertRaises(w.ContractError):
            w.epoch('2025-01-01T00:00:00')
        self.payload['hourly_units']['time'] = 'iso8601'
        with self.assertRaises(w.ContractError):
            self.ingest_synthetic()

    def test_exclusive_query_end(self):
        self.ingest_synthetic()
        result = w.query(self.db, '2025-01-01T09:00:00+09:00', '2025-01-01T10:00:00+09:00')
        self.assertEqual(len(result['rows']), 3)
        self.assertEqual(result['rows'][0]['time_utc'], '2025-01-01T00:00:00Z')

    def test_dst_fall_ambiguous_local_times_stay_distinct(self):
        self.meta['url'] = w.request_url(40, -74, '2025-11-02', '2025-11-02')
        begin = w.epoch('2025-11-02T00:00:00Z')
        self.payload['hourly']['time'] = list(range(begin, begin + 24 * 3600, 3600))
        for variable in w.VARIABLES:
            self.payload['hourly'][variable] = self.payload['hourly'][variable][:24]
        self.ingest_synthetic()
        result = w.query(self.db, '2025-11-02T05:00:00Z', '2025-11-02T07:00:00Z', 'America/New_York')
        local = sorted(set(r['time_local'] for r in result['rows']))
        self.assertEqual(local, ['2025-11-02T01:00:00-04:00', '2025-11-02T01:00:00-05:00'])

    def test_unknown_timezone_fails_explicitly(self):
        with self.assertRaises(w.ContractError):
            w.get_timezone('Not/AZone')

    def test_revision_replaces_current_and_preserves_import_provenance(self):
        self.ingest_synthetic()
        self.payload['hourly']['temperature_2m'][0] = 15
        self.meta['completed_at'] = '2026-09-09T01:00:00+00:00'
        self.ingest_synthetic()
        self.assertEqual(self.count(), 216)
        self.assertEqual(self.count('imports'), 2)
        rows = w.query(self.db)['rows']
        self.assertEqual(next(r['value'] for r in rows if r['variable'] == 'temperature_2m'), 15)

    def test_replay_old_fixture_does_not_roll_back_latest(self):
        old_payload = json.loads(json.dumps(self.payload))
        old_meta = dict(self.meta)
        self.ingest_synthetic()
        self.payload['hourly']['temperature_2m'][0] = 15
        self.meta['completed_at'] = '2026-09-09T10:00:00+09:00'
        self.ingest_synthetic()
        self.payload, self.meta = old_payload, old_meta
        self.ingest_synthetic()
        rows = w.query(self.db)['rows']
        self.assertEqual(next(r['value'] for r in rows if r['variable'] == 'temperature_2m'), 15)
        self.assertEqual(self.count('imports'), 2)

    def test_fresh_fetch_with_previous_bytes_is_a_new_event(self):
        original = json.loads(json.dumps(self.payload))
        self.ingest_synthetic()
        self.payload['hourly']['temperature_2m'][0] = 15
        self.meta['completed_at'] = '2026-09-09T01:00:00+00:00'
        self.ingest_synthetic()
        self.payload = original
        self.meta['completed_at'] = '2026-09-10T01:00:00+00:00'
        self.ingest_synthetic()
        current = next(r['value'] for r in w.query(self.db)['rows'] if r['variable'] == 'temperature_2m')
        self.assertEqual(current, original['hourly']['temperature_2m'][0])
        self.assertEqual(self.count('imports'), 3)

    def test_grid_changes_are_separate_series(self):
        self.ingest_synthetic()
        self.payload['latitude'] = 37.75
        self.ingest_synthetic()
        self.assertEqual(self.count(), 432)
        self.assertEqual(self.count('series'), 2)
        self.assertEqual(len(w.query(self.db)['summary']), 6)

    def test_missing_db_query_does_not_create_file(self):
        with self.assertRaises(sqlite3.OperationalError):
            w.query(self.db)
        self.assertFalse(self.db.exists())

    def test_request_bounds(self):
        for args in ((91, 0, '2025-01-01', '2025-01-01'), (0, 0, '2025-02-01', '2025-01-01'), (0, 0, '2025-01-01', '2025-02-02')):
            with self.subTest(args=args), self.assertRaises(w.ContractError):
                w.request_url(*args)

    def test_transient_http_retry_and_capture(self):
        class Response:
            status, headers, url = 200, {'Content-Type': 'application/json'}, w.API
            def read(self, limit):
                return b'{"hourly": {}}'
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        calls, sleeps = [], []
        def opener(request, timeout):
            calls.append(timeout)
            if len(calls) == 1:
                raise HTTPError(w.API, 429, 'Too many requests', {'Retry-After': '2'}, io.BytesIO(b'rate limited'))
            return Response()
        raw, meta = w.fetch(w.API, self.work / 'http', opener=opener, sleeper=sleeps.append)
        self.assertEqual(sleeps, [2])
        self.assertEqual(calls, [30, 30])
        self.assertTrue(raw.exists())
        self.assertEqual(len(json.loads(meta.read_text())['attempts']), 2)

    def test_http_400_not_retried_and_error_metadata_saved(self):
        calls = []
        def opener(request, timeout):
            calls.append(1)
            raise HTTPError(w.API, 400, 'Bad Request', {}, io.BytesIO(b'{"error":true}'))
        with self.assertRaises(HTTPError):
            w.fetch(w.API, self.work / 'http', opener=opener)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(list((self.work / 'http').glob('*.meta.json'))), 1)

    def test_long_retry_after_is_not_ignored(self):
        with self.assertRaises(w.ContractError):
            w.retry_seconds('120', 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
