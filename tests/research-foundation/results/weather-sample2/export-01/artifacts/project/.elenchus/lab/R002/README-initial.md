# 공개 기상 데이터 → 로컬 SQLite 연구 재료

코드·requirements·fixtures를 복사하거나 `delivery/weather-materials.zip`을 풀어 대표 경로를 다시 실행할 수 있다. 가상환경과 패키지 캐시는 인계 압축에 포함하지 않았다. 표본은 서울 요청 좌표 37.57,126.98에 대해 Open-Meteo가 반환한 ERA5 격자 37.5,127.0의 **재분석 자료**다. 실제 관측소 기록이나 날씨 예측 정확성 검증 자료가 아니다. 제품 화면·전체 UX는 정하지 않았다.

## 빠른 오프라인 재현

Python 3.12 이상과 SQLite 3.24 이상. 아래 명령은 이 README가 있는 폴더를 현재 디렉터리로 사용한다. UTC 경로는 외부 패키지가 전혀 필요 없다.

```powershell
python reproduce.py --out output/readme-replay
python weather_path.py query --db output/readme-replay/weather.sqlite --start 2025-01-01T00:00:00Z --end 2025-01-01T03:00:00Z
python -m sqlite3 output/readme-replay/weather.sqlite "SELECT variable, COUNT(*), COUNT(value), AVG(value), MIN(value), MAX(value) FROM measurements GROUP BY variable;"
```

대표 결과: 2개 실제 fixture × 72시간 × 3변수 = **432행**. 첫 fixture 재적재 후에도 432행, imports 2개. 재현 도구는 입력 fixture를 변경하지 않는다. `output/readme-replay/query.json`에서 결과를 읽는다.

Windows IANA 시간대 표시·DST 테스트에는 공개 tzdata 패키지가 필요하다. 전역 환경 대신 연구 폴더 가상환경을 사용한다.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip --disable-pip-version-check --cache-dir .pip-cache install -r requirements.txt
.venv/Scripts/python.exe reproduce.py --out output/reproduction-seoul --timezone Asia/Seoul
.venv/Scripts/python.exe -m unittest -v test_weather_path.py
```

이번 확인 환경: Windows, Python 3.12.10, SQLite 3.49.1, tzdata 2026.3. 기본 Python에는 pandas/requests/tzdata가 없었으며 `ZoneInfo('Asia/Seoul')`가 실제 실패했다. UTC 경로는 tzdata 없이 동작한다. 모의 DST 자료의 반복 01시를 -04:00/-05:00으로 구분하는 테스트를 포함한다.

## 실제 API 수집과 연결 실행

```powershell
python weather_path.py fetch --lat 37.57 --lon 126.98 --start 2025-07-16 --end 2025-07-18 --out output/new-live --db output/new-live.sqlite
python weather_path.py query --db output/new-live.sqlite --out output/new-live-query.json
```

`--imperial`은 API에 Fahrenheit, mph, inch를 요청한다. 기본은 Celsius, km/h, mm. 함수는 UTC 초·ERA5·3변수를 명시하며 1~31일의 작은 요청만 허용한다. 날짜 범위는 UTC 날짜의 시작부터 마지막 날짜 23:00까지다. 원본 JSON과 수집 메타데이터를 별도 파일로 남긴다. 수동 적재:

```powershell
python weather_path.py ingest fixtures/seoul-era5.json --meta fixtures/seoul-era5.meta.json --db output/manual.sqlite
```

현재 Codex sandbox의 일반 Python 네트워크에서 WinError 10013을 실제 관찰했다. 승인된 네트워크 실행으로 같은 endpoint가 성공했다. 이것은 API 장애가 아니다. 다른 호스트에서는 방화벽/프록시/TLS를 정상 설정해야 하며 TLS 검증을 끄지 않는다. 네트워크 없는 환경에서도 fixture 재현이 가능하다. 수집은 요청당 30초, 최대 4MB, 최대 3회로 제한한다. 429/일시적 5xx 재시도와 Retry-After를 처리하고 30초를 넘는 대기는 재시도 안내와 함께 중단한다. 400·권한 오류는 무작정 재시도하지 않는다. 전역 호출량 제한기나 장기 자동 수집 기능은 아니다.

## 필드와 데이터 의미

| 저장 필드 | 의미 |
|---|---|
| series.metadata_json | 공급자, ERA5, reanalysis, 요청/반환 격자 좌표, 고도. 좌표나 격자가 다르면 분리 |
| timestamp_utc | UNIX epoch 정수 초. SQLite datetime 기본 converter에 의존하지 않음 |
| variable / value / unit | temperature_2m→degC, precipitation→mm, wind_speed_10m→m/s |
| source_value / source_unit | 실제 응답 숫자와 단위. 변환 후에도 보존 |
| interval_start_utc / interval_seconds | 기온·풍속은 순간값(0초), 강수는 표시 시각 직전 3600초 합 |
| quality | valid, source_null, absent_timestamp. 결측은 SQL NULL이며 0 채움/보간하지 않음 |
| imports | raw SHA256, URL, UTC 수집 시각, 원본 위치, 응답 메타데이터. 수집 이벤트 유일성은 hash+URL+fetched_at |
| measurements.import_id | 현재 행을 제공한 수집 snapshot과 연결 |

검증은 DB 쓰기 전에 완료한다. 빈 응답·배열 길이 불일치·잘못된 시간/단위·중복 시각·비유한 값은 실패한다. 시각 자체가 빠진 경우에는 요청 기간의 해당 시간에 NULL+absent_timestamp를 만든다. 공급자 null은 source_null로 보존한다. 임의의 -999 같은 다른 포맷의 sentinel을 이 어댑터에 그대로 넣지 않는다. DWD/NOAA/NASA에는 별도의 계약·어댑터가 필요하다.

행 키는 series+UTC초+변수. 동일 snapshot 재적재는 멱등적이다. 수정 응답은 **더 최신 수집 시각일 때만** 현재 행을 갱신한다. 같은 수집시각의 서로 다른 내용은 기존 값을 유지한다. 예전과 같은 byte를 새 시각에 수집하면 새 이벤트로 취급하므로 값의 정당한 복귀도 반영된다. 이 시각은 공급자 발행 버전이 아니므로 정식 revision/version 정책은 후속 제작자가 보강할 수 있다. imports와 원본은 남으며 측정값의 모든 이력은 원본 재파싱으로 복원한다. 원본 경로의 절대 경로는 출처 참고이고 재실행은 이 폴더의 상대 fixture 경로로 한다. 개발 중 구형 schema DB는 덮어쓰지 않고 새 DB에 fixture를 재생하도록 명시적 오류를 낸다.

조회 시작은 포함, 끝은 제외다. 지역 시간 필터는 `+09:00` 같은 오프셋을 요구한다. 강수는 종료 시각으로 필터링하므로 UTC 달력 하루 `[00,24)` 조회의 첫 행은 전날 23~24시 강수를 포함한다. 완전한 지역 날짜 강수 합을 얻으려면 원하는 **구간**에 맞춰 창을 이동하고 커버리지를 확인해야 한다. `sum_available`은 현재 선택된 행 중 이용 가능한 강수 합이며 결측 포함 완전한 기간 합을 보장하지 않는다. 미수집 기간 사이의 전체 커버리지를 자동 평가하지 않는다.

## 재료·테스트·독립 비교

- `weather_path.py`: 재사용 함수 request_url/fetch/contract/ingest/query와 CLI.
- `fixtures/*.json`: 2026-09-08에 받은 겨울 metric/여름 imperial 원본 각각 72시간. `.meta.json`은 URL·실제 수집시각·SHA256.
- `test_weather_path.py`: 실제 fixture·단위·NULL/시각 누락·UTC/DST·재적재/수정/과거 replay·잘못된 계약·transport 실패 테스트. 변조 사례와 HTTP 429/400은 **모의 테스트**다. 실제 2개 fixture에는 결측이 없었다.
- `reproduce.py`: 오프라인 end-to-end와 재적재를 자동 확인.
- `compare_live_units.py`, `output/unit-comparison.json`: 같은 여름 기간 실제 metric/imperial API 응답의 반올림 차이. 원래 응답/metadata는 `output/live/`에 있다.
- `alternatives/`: 독립 조사자의 처리 방법 비교·실행·반증 기록. 비교를 재실행할 때 `requirements-comparison.txt` 사용.
- `output/tests.txt`, `output/final-reproduction/weather.sqlite`, `output/final-reproduction/query.json`: 최종 코드 실행 결과. output 최상위와 live.sqlite의 초기 DB는 수정 전 실험 기록으로 보존되며 최종 ingest는 새 DB 경로를 사용한다.

데이터 출처는 [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api), ERA5/Copernicus Climate Change Service. 원본 fixture는 응답 byte 그대로, 저장값은 단위 변환/시간 누락 표기/SQLite 구조 변환을 했다. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 출처 표기를 유지한다. API의 [무료 이용약관](https://open-meteo.com/en/terms)은 비상업용과 호출량 제한을 별도로 둔다. 이 연구에서 계정·키·결제는 사용하지 않았으며 미래 상업 제품에 무료 endpoint 사용이 허용된다는 결론은 아니다.

미검증: 장기간·다중 사용자 성능, 공급자 모든 변수/데이터 변경, forecast issue time, 관측소 QC·trace, 외부 공급자 어댑터. 현재 스키마/CLI/폴더는 연구 구현으로 후속 제작자가 재구성할 수 있다.
