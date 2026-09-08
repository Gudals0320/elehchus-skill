"""Compare API contracts on one owned synthetic file; never touches inputs."""
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

lab = Path(__file__).resolve().parent
run = lab / ("ctime_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
run.mkdir()
path = run / "fixed_old_mtime.bin"
path.write_bytes(b"local synthetic data")
time.sleep(0.05)  # Separate creation from change time for this deliberate fixture.
os.utime(path, ns=(946684800000000000, 946684800000000000))
fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_birthtime_ns")
def values(stat):
    return {k: getattr(stat, k, None) for k in fields}
with path.open("rb") as f:
    p1, f1 = values(path.stat()), values(os.fstat(f.fileno()))
    f.read()
    p2, f2 = values(path.stat()), values(os.fstat(f.fileno()))
result = {"python": sys.version, "path_before": p1, "handle_before": f1,
          "path_after": p2, "handle_after": f2,
          "same_api_path_fields_stable": p1 == p2,
          "same_api_handle_fields_stable": f1 == f2,
          "cross_api_fields_equal": {k: p1[k] == f1[k] for k in fields}}
out = run / "results.json"
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
record = lab.parents[3].parent / "records" / "agent_alternatives.jsonl"
with record.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                        "question": "Windows Python 3.12.10 stat/fstat ctime는 같은 계약인가?",
                        "url": ["https://docs.python.org/3.12/library/os.html#os.stat_result.st_ctime"],
                        "command": "local .venv/Scripts/python.exe -I -B ctime_probe.py",
                        "result": result, "path": str(out)}, ensure_ascii=False) + "\n")
print(json.dumps({"path": str(out), "result": result}, indent=2))
