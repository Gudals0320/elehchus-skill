"""Bounded, keyless public API probe. Saves exact bytes plus non-secret provenance."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    metadata = {'requested_at': datetime.now(timezone.utc).isoformat(), 'url': args.url}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = Request(args.url, headers={'User-Agent': 'ElenchusPublicWeatherResearch/1.0', 'Accept': 'application/json'})
        with urlopen(request, timeout=30) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ValueError('Response exceeds research sample size limit')
            metadata.update(status=response.status, content_type=response.headers.get('Content-Type'), final_url=response.url)
        payload = json.loads(raw)
        args.output.write_bytes(raw)
        metadata.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), json_type=type(payload).__name__, keys=list(payload)[:20])
    except HTTPError as exc:
        metadata.update(error=type(exc).__name__, status=exc.code, reason=str(exc.reason), body=exc.read(2048).decode('utf-8', errors='replace'))
    except (URLError, OSError, ValueError) as exc:
        metadata.update(error=type(exc).__name__, reason=str(exc))
    metadata['completed_at'] = datetime.now(timezone.utc).isoformat()
    metadata_path = args.output.with_suffix('.meta.json')
    # Retain attempts: the metadata filename includes time to avoid overwriting a failure.
    attempt = metadata_path.with_name(metadata_path.stem + '.' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    attempt.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(metadata, ensure_ascii=True))
    return 1 if 'error' in metadata else 0


if __name__ == '__main__':
    raise SystemExit(main())
