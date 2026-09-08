"""Read-only independent parsing of the user's Seoul two-variable actual response."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
RESPONSES = HERE.parent.parent / "R001" / "responses"
stem = "seoul-requested-20260901"
raw_path = RESPONSES / f"{stem}.json"
raw = raw_path.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
metadata = next(m for p in RESPONSES.glob(f"{stem}.meta.*.json")
                if (m := json.loads(p.read_text(encoding="utf-8"))).get("sha256") == digest)
request = {key: value[0] for key, value in parse_qs(urlparse(metadata["url"]).query).items()}
payload = json.loads(raw)
times = payload["hourly"]["time"]
seoul = ZoneInfo("Asia/Seoul")
utc = timezone.utc
assert request["start_date"] == "2026-09-01" and request["end_date"] == "2026-09-02"
assert float(request["latitude"]) == 37.5665 and float(request["longitude"]) == 126.9780
assert request["hourly"] == "temperature_2m,precipitation"
assert request["timezone"] == "Asia/Seoul" and request["models"] == "era5"
assert request["timeformat"] == payload["hourly_units"]["time"] == "unixtime"
assert payload["timezone"] == "Asia/Seoul" and payload["utc_offset_seconds"] == 32400
assert len(times) == 48 and len(set(times)) == 48
assert all(type(t) is int for t in times)
assert all(b - a == 3600 for a, b in zip(times, times[1:]))
local_times = [datetime.fromtimestamp(t, utc).astimezone(seoul) for t in times]
assert local_times[0].isoformat() == "2026-09-01T00:00:00+09:00"
assert local_times[-1].isoformat() == "2026-09-02T23:00:00+09:00"
values = {}
for variable in ("temperature_2m", "precipitation"):
    sample = payload["hourly"][variable]
    assert len(sample) == len(times)
    valid = [v for v in sample if isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)]
    values[variable] = {"count": len(sample), "source_null": sample.count(None),
                        "nonfinite_or_nonnumeric": len(sample) - sample.count(None) - len(valid),
                        "unit": payload["hourly_units"][variable], "minimum": min(valid), "maximum": max(valid)}
values["precipitation"]["sum_of_available_end_labeled_hours"] = math.fsum(payload["hourly"]["precipitation"])
result = {"verified_at": datetime.now(utc).isoformat(), "actual_source": str(raw_path), "sha256": digest,
          "fetch_completed_at": metadata["completed_at"], "request": request,
          "returned_grid": {key: payload[key] for key in ("latitude", "longitude", "elevation")},
          "time": {"count": len(times), "utc_start": datetime.fromtimestamp(times[0], utc).isoformat(),
                   "utc_last": datetime.fromtimestamp(times[-1], utc).isoformat(),
                   "utc_exclusive_stop": datetime.fromtimestamp(times[-1] + 3600, utc).isoformat(),
                   "local_start": local_times[0].isoformat(), "local_last": local_times[-1].isoformat(),
                   "local_exclusive_stop": (local_times[-1] + timedelta(hours=1)).isoformat(),
                   "cadence_seconds": 3600, "absent_timestamps": 0,
                   "precipitation_interval_start_local": (local_times[0] - timedelta(hours=1)).isoformat(),
                   "precipitation_interval_end_local": local_times[-1].isoformat()},
          "values": values,
          "caution": "The precipitation sum is over 48 preceding-hour intervals ending at the returned timestamps; it is not the complete Sep 1-2 local-calendar total.",
          "response_revision_fields": {key: payload[key] for key in ("expver", "revision", "era5t", "model") if key in payload},
          "raw_preserved": digest == hashlib.sha256(raw_path.read_bytes()).hexdigest()}
output = HERE / "requested-sample-verification.json"
output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=True, indent=2))
