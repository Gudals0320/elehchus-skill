"""A small, audited Open-Meteo ERA5 -> UTC/SI -> SQLite research path.

No credentials, hidden cache, interpolation or observation claims. See README.md.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
API = 'https://archive-api.open-meteo.com/v1/archive'
VARIABLES = ('temperature_2m', 'precipitation', 'wind_speed_10m')
UNITS = {'temperature_2m': 'degC', 'precipitation': 'mm', 'wind_speed_10m': 'm/s'}
CONVERSIONS = {
    'temperature_2m': {'°C': (1, 0), '°F': (5 / 9, -32 * 5 / 9)},
    'precipitation': {'mm': (1, 0), 'inch': (25.4, 0)},
    'wind_speed_10m': {'km/h': (1 / 3.6, 0), 'm/s': (1, 0), 'mp/h': (0.44704, 0), 'mph': (0.44704, 0), 'kn': (1852 / 3600, 0)},
}


class ContractError(ValueError):
    pass


def utc_iso(seconds):
    return datetime.fromtimestamp(seconds, UTC).isoformat().replace('+00:00', 'Z')


def epoch(text):
    parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.microsecond:
        raise ContractError('Time filter must include an offset and whole seconds, e.g. 2025-01-01T00:00:00Z')
    return int(parsed.timestamp())


def get_timezone(name):
    if name in ('UTC', 'GMT'):
        return UTC
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ContractError('Unknown/unavailable IANA timezone; install requirements.txt (tzdata), then verify its name') from exc


def request_url(lat, lon, start, end, imperial=False):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ContractError('Coordinates out of bounds')
    if not 0 <= (last - first).days < 31:
        raise ContractError('Research requests must span 1 to 31 inclusive days')
    params = dict(latitude=lat, longitude=lon, start_date=start, end_date=end,
                  hourly=','.join(VARIABLES), models='era5', timezone='GMT', timeformat='unixtime',
                  temperature_unit='fahrenheit' if imperial else 'celsius',
                  wind_speed_unit='mph' if imperial else 'kmh', precipitation_unit='inch' if imperial else 'mm')
    return API + '?' + urlencode(params)


def retry_seconds(header, attempt):
    if header:
        try:
            delay = float(header)
        except ValueError:
            delay = (parsedate_to_datetime(header) - datetime.now(UTC)).total_seconds()
    else:
        delay = 2 ** attempt
    if delay > 30:
        raise ContractError(f'Retry-After requires {delay:.0f}s; stop and retry later instead of retrying early')
    return max(0, delay)


def fetch(url, destination, *, opener=urlopen, sleeper=time.sleep):
    """At most 3 requests, <=30 s each, <=4 MB. Return raw/provenance paths.

    Dependency injection is only for offline transport tests, not live evidence.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    meta = dict(url=url, requested_at=datetime.now(UTC).isoformat(), attempts=[])
    metadata_path = destination / f'{stamp}.meta.json'
    try:
        for attempt in range(3):
            try:
                request = Request(url, headers={'User-Agent': 'ElenchusPublicWeatherResearch/1.0', 'Accept': 'application/json'})
                with opener(request, timeout=30) as response:
                    raw = response.read(4_000_001)
                    if len(raw) > 4_000_000:
                        raise ContractError('Response exceeds 4 MB sample bound')
                    if response.status != 200:
                        raise ContractError(f'Unexpected HTTP status {response.status}')
                    meta.update(status=response.status, content_type=response.headers.get('Content-Type'), final_url=response.url)
                digest = hashlib.sha256(raw).hexdigest()
                raw_path = destination / f'{stamp}-{digest[:12]}.json'
                raw_path.write_bytes(raw)
                meta.update(sha256=digest, bytes=len(raw), raw_file=raw_path.name)
                payload = json.loads(raw)
                if not isinstance(payload, dict) or payload.get('error'):
                    raise ContractError(f'API did not return a data object: {str(payload)[:200]}')
                meta['attempts'].append(dict(attempt=attempt + 1, status=200))
                return raw_path, metadata_path
            except HTTPError as exc:
                meta['attempts'].append(dict(attempt=attempt + 1, status=exc.code, reason=str(exc.reason), body=exc.read(2048).decode('utf-8', 'replace')))
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
                sleeper(retry_seconds(exc.headers.get('Retry-After'), attempt))
            except URLError as exc:
                meta['attempts'].append(dict(attempt=attempt + 1, error=type(exc).__name__, reason=str(exc)))
                # A permission error requires host authorization, never blind retries.
                if getattr(exc.reason, 'winerror', None) == 10013 or attempt == 2:
                    raise
                sleeper(2 ** attempt)
    except Exception as exc:
        meta['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        meta['completed_at'] = datetime.now(UTC).isoformat()
        metadata_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')


def contract(raw, metadata):
    """Validate all data before DB writes. Epoch seconds carry no guessed offset."""
    if hashlib.sha256(raw).hexdigest() != metadata['sha256']:
        raise ContractError('Raw response checksum mismatch')
    parsed_url = urlparse(metadata['url'])
    if f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}' != API:
        raise ContractError('This adapter only accepts the Open-Meteo archive endpoint')
    query = parse_qs(parsed_url.query)
    def one(key):
        values = query.get(key, [])
        if len(values) != 1:
            raise ContractError(f'Missing/duplicate query field: {key}')
        return values[0]
    if one('models') != 'era5' or one('timeformat') != 'unixtime' or one('timezone') not in ('GMT', 'UTC'):
        raise ContractError('Adapter requires explicit ERA5, unixtime, UTC/GMT request')
    if set(one('hourly').split(',')) != set(VARIABLES):
        raise ContractError('Request must specify the supported three-variable contract')
    latitude, longitude = float(one('latitude')), float(one('longitude'))
    request_url(latitude, longitude, one('start_date'), one('end_date'))
    start = epoch(one('start_date') + 'T00:00:00Z')
    stop = epoch((date.fromisoformat(one('end_date')) + timedelta(days=1)).isoformat() + 'T00:00:00Z')
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get('error'):
        raise ContractError('API error/unsupported response')
    if payload.get('utc_offset_seconds') != 0 or payload.get('hourly_units', {}).get('time') != 'unixtime':
        raise ContractError('Response time contract changed')
    hourly = payload.get('hourly', {})
    times = hourly.get('time')
    if not isinstance(times, list) or not times:
        raise ContractError('Empty/missing hourly time array')
    if any(type(t) is not int or t < start or t >= stop or (t - start) % 3600 for t in times):
        raise ContractError('Timestamps must be integral hourly epoch seconds within request')
    if times != sorted(set(times)):
        raise ContractError('Duplicate or unsorted timestamp')
    for variable in VARIABLES:
        if not isinstance(hourly.get(variable), list) or len(hourly[variable]) != len(times):
            raise ContractError(f'Array missing/length mismatch: {variable}')
        if payload['hourly_units'].get(variable) not in CONVERSIONS[variable]:
            raise ContractError(f'Unsupported source unit: {variable}')
    series = dict(provider='open-meteo', kind='reanalysis', model='era5', requested_latitude=latitude,
                  requested_longitude=longitude, grid_latitude=payload.get('latitude'), grid_longitude=payload.get('longitude'),
                  elevation_m=payload.get('elevation'))
    for key in ('grid_latitude', 'grid_longitude', 'elevation_m'):
        value = series[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError(f'Missing/invalid metadata: {key}')
    # Grid/elevation changes form a new series; raw coordinates are preserved.
    series_key = hashlib.sha256(json.dumps(series, sort_keys=True).encode()).hexdigest()
    by_time = dict(zip(times, range(len(times))))
    rows = []
    for timestamp in range(start, stop, 3600):
        for variable in VARIABLES:
            unit = payload['hourly_units'][variable]
            index = by_time.get(timestamp)
            value = None if index is None else hourly[variable][index]
            quality = 'absent_timestamp' if index is None else 'source_null' if value is None else 'valid'
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ContractError(f'Non-finite/non-numeric value: {variable}')
                factor, offset = CONVERSIONS[variable][unit]
                normalized = value * factor + offset
                if variable != 'temperature_2m' and normalized < 0:
                    raise ContractError(f'Negative physical quantity: {variable}; unknown sentinel is not silently accepted')
            else:
                normalized = None
            interval = 3600 if variable == 'precipitation' else 0
            rows.append((series_key, timestamp, variable, timestamp - interval, interval,
                         normalized, UNITS[variable], value, unit, quality))
    return series_key, series, rows


SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS imports (
 id INTEGER PRIMARY KEY, sha256 TEXT NOT NULL, url TEXT NOT NULL, fetched_at TEXT NOT NULL,
 raw_path TEXT NOT NULL, metadata_json TEXT NOT NULL, UNIQUE(sha256, url, fetched_at)
);
CREATE TABLE IF NOT EXISTS series (series_key TEXT PRIMARY KEY, metadata_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS measurements (
 series_key TEXT NOT NULL REFERENCES series(series_key), timestamp_utc INTEGER NOT NULL,
 variable TEXT NOT NULL, interval_start_utc INTEGER NOT NULL, interval_seconds INTEGER NOT NULL,
 value REAL, unit TEXT NOT NULL, source_value REAL, source_unit TEXT NOT NULL,
 quality TEXT NOT NULL CHECK(quality IN ('valid','source_null','absent_timestamp')),
 import_id INTEGER NOT NULL REFERENCES imports(id),
 PRIMARY KEY(series_key, timestamp_utc, variable),
 CHECK((quality='valid' AND value IS NOT NULL) OR (quality!='valid' AND value IS NULL))
);
'''


def ingest(raw_path, metadata_path, database):
    raw_path, metadata_path, database = map(Path, (raw_path, metadata_path, database))
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    key, series, rows = contract(raw_path.read_bytes(), metadata)
    fetched_at = metadata.get('completed_at', metadata.get('requested_at'))
    if not fetched_at or datetime.fromisoformat(fetched_at.replace('Z', '+00:00')).tzinfo is None:
        raise ContractError('Provenance fetch time must include a UTC offset')
    fetched_at = datetime.fromisoformat(fetched_at.replace('Z', '+00:00')).astimezone(UTC).isoformat(timespec='microseconds')
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        existing = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='imports'").fetchone()
        if existing and 'UNIQUE(sha256, url, fetched_at)' not in existing[0]:
            raise ContractError('Older research schema: use a new database and replay immutable fixtures')
        connection.executescript(SCHEMA)
        with connection:
            connection.execute('INSERT OR IGNORE INTO imports(sha256,url,fetched_at,raw_path,metadata_json) VALUES(?,?,?,?,?)',
                               (metadata['sha256'], metadata['url'], fetched_at, str(raw_path.resolve()), json.dumps(metadata)))
            import_id = connection.execute('SELECT id FROM imports WHERE sha256=? AND url=? AND fetched_at=?', (metadata['sha256'], metadata['url'], fetched_at)).fetchone()[0]
            connection.execute('INSERT OR IGNORE INTO series VALUES(?,?)', (key, json.dumps(series)))
            connection.executemany('''INSERT INTO measurements VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(series_key,timestamp_utc,variable) DO UPDATE SET
                interval_start_utc=excluded.interval_start_utc, interval_seconds=excluded.interval_seconds,
                value=excluded.value,unit=excluded.unit,source_value=excluded.source_value,
                source_unit=excluded.source_unit,quality=excluded.quality,import_id=excluded.import_id
                WHERE (SELECT fetched_at FROM imports WHERE id=excluded.import_id) >
                      (SELECT fetched_at FROM imports WHERE id=measurements.import_id)''',
                [(*row, import_id) for row in rows])
            count = connection.execute('SELECT COUNT(*) FROM measurements').fetchone()[0]
    return dict(import_id=import_id, processed=len(rows), rows_total=count, missing=sum(r[5] is None for r in rows), series_key=key)


def query(database, start=None, end=None, display_timezone='UTC'):
    tz = get_timezone(display_timezone)
    lower = epoch(start) if start else -(2 ** 62)
    upper = epoch(end) if end else 2 ** 62
    if lower >= upper:
        raise ContractError('Query start must precede exclusive end')
    # Read-only connection avoids accidentally creating a DB on a path typo.
    uri = Path(database).resolve().as_uri() + '?mode=ro'
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        records = [dict(row) for row in connection.execute('''SELECT series_key, timestamp_utc, variable,
                  interval_start_utc, interval_seconds, value, unit, source_value, source_unit, quality
                  FROM measurements WHERE timestamp_utc>=? AND timestamp_utc<? ORDER BY series_key,timestamp_utc,variable''', (lower, upper))]
    for row in records:
        row['time_utc'] = utc_iso(row['timestamp_utc'])
        row['time_local'] = datetime.fromtimestamp(row['timestamp_utc'], UTC).astimezone(tz).isoformat()
    # Do not mix locations or call incomplete precipitation a full-period total.
    grouped = {}
    for row in records:
        group = grouped.setdefault((row['series_key'], row['variable']), [])
        group.append(row['value'])
    summary = []
    for (series_key, variable), values in grouped.items():
        valid = [value for value in values if value is not None]
        summary.append(dict(series_key=series_key, variable=variable, unit=UNITS[variable],
                            rows=len(values), valid=len(valid), missing=len(values)-len(valid),
                            mean=(sum(valid) / len(valid)) if valid else None,
                            sum_available=sum(valid) if valid and variable == 'precipitation' else None))
    return dict(time_filter='start inclusive, end exclusive; precipitation keyed by end of preceding hour',
                display_timezone=display_timezone, summary=summary, rows=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    fetch_parser = sub.add_parser('fetch')
    fetch_parser.add_argument('--lat', type=float, default=37.57)
    fetch_parser.add_argument('--lon', type=float, default=126.98)
    fetch_parser.add_argument('--start', required=True)
    fetch_parser.add_argument('--end', required=True)
    fetch_parser.add_argument('--imperial', action='store_true')
    fetch_parser.add_argument('--out', type=Path, required=True)
    fetch_parser.add_argument('--db', type=Path)
    import_parser = sub.add_parser('ingest')
    import_parser.add_argument('raw', type=Path)
    import_parser.add_argument('--meta', type=Path, required=True)
    import_parser.add_argument('--db', type=Path, required=True)
    query_parser = sub.add_parser('query')
    query_parser.add_argument('--db', type=Path, required=True)
    query_parser.add_argument('--start')
    query_parser.add_argument('--end')
    query_parser.add_argument('--timezone', default='UTC')
    query_parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'fetch':
            raw, meta = fetch(request_url(args.lat, args.lon, args.start, args.end, args.imperial), args.out)
            result = dict(raw=str(raw), metadata=str(meta))
            if args.db:
                result['ingest'] = ingest(raw, meta, args.db)
        elif args.command == 'ingest':
            result = ingest(args.raw, args.meta, args.db)
        else:
            result = query(args.db, args.start, args.end, args.timezone)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                result = dict(summary=result['summary'], output=str(args.out), rows=len(result['rows']))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ContractError, ValueError, KeyError, TypeError, OSError, URLError, sqlite3.Error) as exc:
        print(json.dumps(dict(error=type(exc).__name__, message=str(exc)), ensure_ascii=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
