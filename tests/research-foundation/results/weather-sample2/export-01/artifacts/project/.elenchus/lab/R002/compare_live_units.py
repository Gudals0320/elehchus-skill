"""Compare separately fetched, same-period metric and imperial responses.

This measures API output rounding plus conversion, not meteorological accuracy.
"""
import json
from pathlib import Path
import weather_path as w

ROOT = Path(__file__).resolve().parent
imperial_path = ROOT / 'fixtures/seoul-era5-imperial.json'
imperial_meta = ROOT / 'fixtures/seoul-era5-imperial.meta.json'
live_meta = next((ROOT / 'output/live').glob('*.meta.json'))
metadata = json.loads(live_meta.read_text(encoding='utf-8'))
metric_path = live_meta.parent / metadata['raw_file']
_, _, imperial = w.contract(imperial_path.read_bytes(), json.loads(imperial_meta.read_text(encoding='utf-8')))
_, _, metric = w.contract(metric_path.read_bytes(), metadata)
comparison = {}
for variable in w.VARIABLES:
    one = {r[1]: r[5] for r in imperial if r[2] == variable}
    two = {r[1]: r[5] for r in metric if r[2] == variable}
    assert one.keys() == two.keys(), 'Different time grids'
    differences = [abs(one[t] - two[t]) for t in one if one[t] is not None and two[t] is not None]
    comparison[variable] = dict(samples=len(differences), max_abs_difference=max(differences),
                                unit=w.UNITS[variable], sum_imperial_normalized=sum(one.values()), sum_metric=sum(two.values()))
result = dict(metric_url=metadata['url'], imperial_url=json.loads(imperial_meta.read_text(encoding='utf-8'))['url'],
              interpretation='Separate API requests round their output differently; conversion is not an accuracy benchmark.',
              variables=comparison)
(ROOT / 'output/unit-comparison.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
