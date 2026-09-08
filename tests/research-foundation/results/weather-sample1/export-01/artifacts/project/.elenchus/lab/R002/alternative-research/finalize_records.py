"""Record tool-only activities and hash local research materials, excluding environments."""
from pathlib import Path
import hashlib
import json
from fetch_probe import log

ROOT = Path(__file__).resolve().parent
log('tool_activity_summary', retrospective=True,
    initial_reads=['skill/SKILL.md','skill/stages/research.md','skill/stages/discovery.md','skill/stages/web-evidence-loop.md','skill/stages/lab.md'],
    project_read_status='Initial topology/index paths missing; both read after main created them.',
    search_queries=[
        'site.ncei.noaa.gov ISD lite data format missing -9999 UTC temperature tenths',
        'site.dev.meteostat.net bulk hourly csv units UTC license',
        'site.ncei.noaa.gov 471080 Seoul ISD history',
        'site.sqlite.org datatype3 date time NULL primary key strict',
        'site.pandas.pydata.org to_datetime mixed offsets utc read_csv na_values to_sql sqlite rollback',
        'site.ncei.noaa.gov GHCNh hourly CSV format UTC quality flag'],
    web_access_failures=[
        'NOAA service-change and ISD-Lite 2024 index: web timeout',
        'Meteostat /python/: 404; /python success',
        'GHCNh PDF and station list: web unsupported application/octet-stream',
        'NODD S3 list-type query: web could not open URL; no result claimed'],
    shell_stdout_failure='pypdf extraction wrote UTF-8 file but printing full text hit cp949 UnicodeEncodeError; inspected saved text via PowerShell and PYTHONIOENCODING=utf-8',
    commands=[
        'python -B -m venv .venv',
        ".venv/Scripts/python.exe -B -m pip install --disable-pip-version-check --no-compile pandas==3.0.3 pypdf==6.8.0 --log pip-install.log",
        'python -B archive_sqlite.py',
        'python -B failure_probes.py',
        '.venv/Scripts/python.exe -B pandas_probe.py',
        'python -B ghcnh_probe.py',
        'python -B ghcnh_probe.py --offline',
        '.venv/Scripts/python.exe -B -m pip freeze'],
    isolation='Owned alternative-research directory only; reads of skill and current topology/index; no other task results or outside evaluation files read; no extra agent spawned',
    downloads='All raw successful GETs and errors are separately recorded in this activity log.',
    outcome='See README, archive-results, failure-results, pandas-results, ghcnh-probe-results. No benchmarks or complete GHCNh ingestion claimed.')

hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
          for p in ROOT.iterdir() if p.is_file() and p.name not in {'activity.jsonl','material-hashes.json'}}
(ROOT/'material-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print(json.dumps({'hashed_files':len(hashes),'raw_hash':hashes['471080-99999-2024.gz']},indent=2))
