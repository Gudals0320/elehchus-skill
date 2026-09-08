"""Small, audited Open-Meteo ERA5 -> canonical hourly SQLite research adapter."""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
FIELDS = ('temperature_2m', 'precipitation', 'wind_speed_10m')
CONVERSIONS = {
    'temperature_2m': {'°C': (1, 0), '°F': (5 / 9, -32 * 5 / 9)},
    'precipitation': {'mm': (1, 0), 'inch': (25.4, 0)},
    'wind_speed_10m': {'m/s': (1, 0), 'km/h': (1 / 3.6, 0),
                       'mp/h': (0.44704, 0), 'mph': (0.44704, 0), 'kn': (0.5144444444, 0)},
}
MAX_BYTES = 2_000_000
MAX_ROWS = 100_000


def read_json(data):
    def invalid(value):
        raise ValueError(f'Non-standard JSON number: {value}')
    return json.loads(data, parse_constant=invalid)


def request_url(latitude, longitude, start, end, imperial=False):
    if not (math.isfinite(latitude) and -90 <= latitude <= 90
            and math.isfinite(longitude) and -180 <= longitude <= 180):
        raise ValueError('Latitude/longitude out of range')
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first or (last - first).days > 30:
        raise ValueError('Research requests must cover 1 to 31 days')
    return 'https://archive-api.open-meteo.com/v1/archive?' + urlencode({
        'latitude': latitude, 'longitude': longitude, 'start_date': start, 'end_date': end,
        'hourly': ','.join(FIELDS), 'timezone': 'UTC', 'timeformat': 'unixtime',
        'models': 'era5', 'temperature_unit': 'fahrenheit' if imperial else 'celsius',
        'wind_speed_unit': 'mph' if imperial else 'ms',
        'precipitation_unit': 'inch' if imperial else 'mm'})


def fetch(url, directory, attempts=3, opener=urlopen, sleeper=time.sleep):
    """GET only, at most 3 attempts, 25 s socket timeout, bounded response/retry delay."""
    if not 1 <= attempts <= 3:
        raise ValueError('Attempts must be 1..3')
    target = urlsplit(url)
    if target.scheme != 'https' or target.netloc != 'archive-api.open-meteo.com' or target.path != '/v1/archive':
        raise ValueError('Only the public Open-Meteo archive endpoint is supported')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    events = []
    for attempt in range(attempts):
        event = {'time': datetime.now(UTC).isoformat(), 'url': url, 'attempt': attempt + 1}
        try:
            request = Request(url, headers={'User-Agent': 'elenchus-weather-lab/1.0', 'Accept': 'application/json'})
            with opener(request, timeout=25) as response:
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise ValueError('Response exceeds 2 MB research limit')
                event.update(status=response.status, content_type=response.headers.get('Content-Type'))
            digest = hashlib.sha256(body).hexdigest()
            stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
            raw_path = directory / f'{stamp}-{digest[:12]}.json'
            raw_path.write_bytes(body)
            event.update(sha256=digest, bytes=len(body), artifact=raw_path.name)
            raw_path.with_suffix('.meta.json').write_text(json.dumps(event, indent=2), encoding='utf-8')
            events.append(event)
            with (directory / 'fetch-events.jsonl').open('a', encoding='utf-8') as log:
                log.writelines(json.dumps(item) + '\n' for item in events)
            return raw_path
        except HTTPError as exc:
            event.update(error='HTTPError', status=exc.code, message=exc.read(2048).decode('utf-8', 'replace'))
            retryable = exc.code in {429, 500, 502, 503, 504}
            value = exc.headers.get('Retry-After')
            delay = 2 ** attempt
            if value:
                try:
                    delay = float(value)
                except ValueError:
                    try:
                        delay = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
                    except (TypeError, ValueError):
                        pass
            # A long Retry-After is respected by stopping, never retried early.
            if delay > 30:
                retryable = False
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            event.update(error=type(exc).__name__, message=str(exc))
            retryable = isinstance(exc, (URLError, TimeoutError))
            delay = 2 ** attempt
        events.append(event)
        if not retryable or attempt == attempts - 1:
            with (directory / 'fetch-events.jsonl').open('a', encoding='utf-8') as log:
                log.writelines(json.dumps(item) + '\n' for item in events)
            raise RuntimeError(f'Fetch failed: {event}')
        sleeper(max(0, delay))
    raise AssertionError('Unreachable')


def normalize(payload):
    """Return UTC epochs with C/mm/m/s values; reject ambiguous/unknown contracts."""
    if not isinstance(payload, dict) or payload.get('error'):
        raise ValueError('Expected one successful JSON location object')
    units, hourly = payload.get('hourly_units', {}), payload.get('hourly', {})
    if units.get('time') != 'unixtime':
        raise ValueError('Request timeformat=unixtime; naive local ISO strings are ambiguous')
    times = hourly.get('time')
    if not isinstance(times, list) or len(times) > MAX_ROWS:
        raise ValueError('Missing time array or row limit exceeded')
    for field in FIELDS:
        if units.get(field) not in CONVERSIONS[field]:
            raise ValueError(f'Unknown unit for {field}: {units.get(field)}')
        if not isinstance(hourly.get(field), list) or len(hourly[field]) != len(times):
            raise ValueError(f'Array length mismatch: {field}')
    rows = []
    previous = None
    for index, epoch in enumerate(times):
        if type(epoch) is not int:
            raise ValueError('Epoch must be integer seconds, not bool/string/milliseconds')
        datetime.fromtimestamp(epoch, UTC)
        if epoch % 3600 or (previous is not None and epoch <= previous):
            raise ValueError('Expected sorted, distinct UTC hourly timestamps')
        if previous is not None:
            gap_count = (epoch - previous) // 3600 - 1
            if len(rows) + gap_count + 1 > MAX_ROWS:
                raise ValueError('Hourly gaps exceed research row limit')
            for missing in range(previous + 3600, epoch, 3600):
                rows.append((missing, None, None, None, 'missing_timestamp'))
        values, nulls = [], []
        for field in FIELDS:
            value = hourly[field][index]
            if value is None:
                values.append(None)
                nulls.append(field)
                continue
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f'Invalid numeric value in {field}')
            scale, offset = CONVERSIONS[field][units[field]]
            converted = value * scale + offset
            if field != 'temperature_2m' and converted < 0:
                raise ValueError(f'Negative {field}; provider sentinel not supported')
            values.append(converted)
        rows.append((epoch, *values, 'null:' + ','.join(nulls) if nulls else 'ok'))
        previous = epoch
    return rows


SCHEMA = '''
CREATE TABLE IF NOT EXISTS datasets (
 id TEXT PRIMARY KEY, source TEXT NOT NULL, data_kind TEXT NOT NULL,
 request_url TEXT NOT NULL, fetched_at TEXT NOT NULL, raw_sha256 TEXT NOT NULL,
 raw_file TEXT NOT NULL, request_json TEXT NOT NULL, metadata_json TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS hourly (
 dataset_id TEXT NOT NULL REFERENCES datasets(id), epoch_utc INTEGER NOT NULL,
 temperature_c REAL, precipitation_mm REAL CHECK(precipitation_mm >= 0),
 wind_speed_ms REAL CHECK(wind_speed_ms >= 0), quality TEXT NOT NULL,
 PRIMARY KEY(dataset_id,epoch_utc)
) STRICT;
'''


def ingest(raw_file, database):
    raw_file, database = Path(raw_file), Path(database)
    body = raw_file.read_bytes()
    if len(body) > MAX_BYTES:
        raise ValueError('Raw file exceeds research limit')
    meta = read_json(raw_file.with_suffix('.meta.json').read_bytes())
    digest = hashlib.sha256(body).hexdigest()
    if meta.get('sha256') != digest or meta.get('status') != 200:
        raise ValueError('Provenance hash/status mismatch')
    payload = read_json(body)
    rows = normalize(payload)  # Validate entire response before opening/writing database.
    target = urlsplit(meta['url'])
    if target.scheme != 'https' or target.netloc != 'archive-api.open-meteo.com' or target.path != '/v1/archive':
        raise ValueError('Unexpected provenance endpoint')
    query = parse_qs(target.query)
    if query.get('models') != ['era5'] or query.get('timeformat') != ['unixtime']:
        raise ValueError('This adapter supports explicit ERA5 epoch requests only')
    identity = hashlib.sha256((meta['url'] + '\0' + digest).encode()).hexdigest()
    metadata = {key: value for key, value in payload.items() if key != 'hourly'}
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute('PRAGMA foreign_keys=ON')
        connection.executescript(SCHEMA)
        with connection:
            exists = connection.execute('SELECT 1 FROM datasets WHERE id=?', (identity,)).fetchone()
            if not exists:
                connection.execute('INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?)', (
                    identity, 'Open-Meteo / Copernicus ERA5', 'reanalysis', meta['url'], meta['time'],
                    digest, raw_file.name, json.dumps(query), json.dumps(metadata, ensure_ascii=False)))
                connection.executemany('INSERT INTO hourly VALUES (?,?,?,?,?,?)', [(identity, *row) for row in rows])
        return {'dataset_id': identity, 'rows': len(rows), 'inserted': not bool(exists),
                'missing_rows': sum(row[-1] != 'ok' for row in rows)}


def aware_epoch(value):
    instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if instant.tzinfo is None:
        raise ValueError('Query bounds must include UTC Z or a numeric offset')
    return instant.timestamp()


def query_data(database, dataset, start, end, display_timezone='UTC'):
    lower, upper = aware_epoch(start), aware_epoch(end)
    if upper <= lower:
        raise ValueError('End must follow start; interval is [start,end)')
    try:
        zone = UTC if display_timezone == 'UTC' else ZoneInfo(display_timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError('Unknown IANA zone or tzdata missing; install requirements.txt') from exc
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        if not connection.execute('SELECT 1 FROM datasets WHERE id=?', (dataset,)).fetchone():
            raise ValueError('Unknown dataset id')
        rows = connection.execute('SELECT * FROM hourly WHERE dataset_id=? AND epoch_utc>=? AND epoch_utc<? ORDER BY epoch_utc',
                                  (dataset, lower, upper)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item['time_local'] = datetime.fromtimestamp(row['epoch_utc'], UTC).astimezone(zone).isoformat()
        item['precipitation_period_start_utc'] = row['epoch_utc'] - 3600
        item['precipitation_period_end_utc'] = row['epoch_utc']
        result.append(item)
    temps = [r['temperature_c'] for r in result if r['temperature_c'] is not None]
    rain = [r['precipitation_mm'] for r in result if r['precipitation_mm'] is not None]
    expected_hours = (upper - lower) / 3600
    complete = (lower % 3600 == 0 and upper % 3600 == 0 and len(result) == expected_hours
                and len(rain) == len(result) and bool(result))
    return {'rows': result, 'summary': {
        'row_count': len(result), 'expected_hours': expected_hours,
        'temperature_valid_count': len(temps), 'temperature_mean_c': sum(temps) / len(temps) if temps else None,
        'precipitation_valid_count': len(rain), 'precipitation_observed_sum_mm': sum(rain) if rain else None,
        'precipitation_labels_complete': complete}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    download = commands.add_parser('fetch')
    download.add_argument('--latitude', type=float, default=37.5665)
    download.add_argument('--longitude', type=float, default=126.978)
    download.add_argument('--start', default='2024-01-01')
    download.add_argument('--end', default='2024-01-02')
    download.add_argument('--out', required=True)
    download.add_argument('--imperial', action='store_true')
    store = commands.add_parser('ingest')
    store.add_argument('--raw', required=True)
    store.add_argument('--db', required=True)
    show = commands.add_parser('query')
    show.add_argument('--db', required=True)
    show.add_argument('--dataset', required=True)
    show.add_argument('--start', required=True)
    show.add_argument('--end', required=True)
    show.add_argument('--timezone', default='UTC')
    args = parser.parse_args()
    try:
        if args.command == 'fetch':
            result = {'raw_file': str(fetch(request_url(args.latitude, args.longitude, args.start, args.end, args.imperial), args.out))}
        elif args.command == 'ingest':
            result = ingest(args.raw, args.db)
        else:
            result = query_data(args.db, args.dataset, args.start, args.end, args.timezone)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
