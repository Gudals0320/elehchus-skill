# 서울 시간별 기온·강수량 → 로컬 SQLite 재료

사용자 확정 범위: **37.5665,126.9780**, 기온/강수량, 우선 **2026-09-01~02**. 날짜는 서울 시민 시간(Asia/Seoul)으로 해석했다. 실제 API가 이 범위를 제공해 다른 날짜로 대체하지 않았다. 기존 2025년 표본은 초기 단위 비교·회귀 테스트로 보존했다.

코드·requirements·fixtures를 복사하거나 `delivery/weather-materials.zip`을 풀어 실행한다. 압축의 시작점은 `.elenchus/lab/R002/README.md`다. 가상환경·패키지 캐시는 포함하지 않는다. 전체 제품 UI/UX와 기존 제품·시스템 설정은 변경하지 않았다.

## 실제 자료의 의미와 결과

[Open-Meteo Historical API](https://open-meteo.com/en/docs/historical-weather-api)의 `models=era5`를 명시했다. **관측을 동화한 모델 재분석 자료**이며 서울 관측소가 직접 측정한 값이나 운영 예보 응답이 아니다. ERA5 내부에는 분석과 단기 모델 예측에서 생산되는 변수가 모두 있다.

요청 좌표 37.5665,126.9780에 대해 반환 격자는 **37.5,127.0**, 고도 **34m**다. 한국시간 2026-09-01 00:00~09-02 23:00의 **48시간×2변수=96행**, 실제 null 0. UTC는 2026-08-31 15:00~09-02 14:00이다. 실제 반복 수집 DB는 **96행·수집 이벤트 2개**, 같은 고정 fixture 재생 DB는 **96행·이벤트 1개**다.

기온 범위 21.6~29.0℃, 평균 24.25℃. 강수의 이용 가능한 48구간 합은 94.7mm다. 강수는 timestamp **직전 한 시간 합**이므로 `[8/31 23:00,9/2 23:00]` KST 구간의 합이며, 9/1~2 달력일 전체 강수 합계라고 부르지 않는다.

최근 과거값은 영구 불변을 보장하지 않는다. [ECMWF ERA5 문서](https://confluence.ecmwf.int/spaces/CKB/pages/76414402/ERA5+data+documentation)의 Data update frequency에 따르면 ERA5T는 약 5일 지연된 초기 자료이며 해당 월 약 두 달 뒤 최종 ERA5로 대체될 수 있다. 9/8에 받은 9/1~2 자료를 잠정적인 최근 재분석으로 취급한다는 **추론**을 남긴다. Open-Meteo JSON에는 expver/revision 필드가 없어 정확한 ERA5T 버전을 직접 증명하지 못했다. 재현용 raw는 수집 시각·SHA256와 함께 byte 그대로 고정했다.

## 설치와 오프라인 재현

확인 환경: Windows, Python 3.12.10, SQLite 3.49.1. Python 3.12 이상/SQLite 3.24 이상. 명령은 이 README 폴더에서 실행한다. 서울 날짜를 해석하는 현재 preset은 IANA 자료 `tzdata`가 필요하다. 기본 Windows Python의 실제 ZoneInfoNotFoundError는 독립 venv로 해결했다.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip --disable-pip-version-check --cache-dir .pip-cache install -r requirements.txt
.venv/Scripts/python.exe reproduce.py --out output/reader-requested --timezone Asia/Seoul
.venv/Scripts/python.exe weather_path.py query --db output/reader-requested/weather.sqlite --start 2026-09-01T00:00:00+09:00 --end 2026-09-03T00:00:00+09:00 --timezone Asia/Seoul --out output/reader-requested/query-seoul.json
.venv/Scripts/python.exe -m unittest -v test_weather_path.py
python -m sqlite3 output/reader-requested/weather.sqlite "SELECT variable, COUNT(*), COUNT(value), AVG(value), MIN(value), MAX(value) FROM measurements GROUP BY variable;"
```

`reproduce.py`는 고정 응답을 적재하고 같은 fixture를 다시 넣어도 96행인지 확인한다. **28개 테스트 통과**. 독립 코드 복사본에서도 96행 재현. 이전 UTC 표본만 시험하는 `python reproduce.py --preset legacy --out output/reader-legacy`는 외부 패키지가 없는 기본 Python으로 432행을 재현한다. 두 preset은 별도 DB 폴더를 사용한다.

## 실제 수집

```powershell
.venv/Scripts/python.exe weather_path.py fetch --start 2026-09-01 --end 2026-09-02 --out output/new-seoul/responses --db output/new-seoul/weather.sqlite
.venv/Scripts/python.exe weather_path.py query --db output/new-seoul/weather.sqlite --timezone Asia/Seoul --out output/new-seoul/query.json
```

CLI 기본값은 좌표 37.5665,126.9780, `--variables temperature_2m,precipitation`, `--request-timezone Asia/Seoul`. `--request-timezone GMT`는 UTC 날짜를 요청한다. 표시 `--timezone`과 날짜 요청 `--request-timezone`은 역할이 다르다. 날짜 요청은 UTC/GMT/Asia/Seoul만 지원하고 조회 표시는 설치된 IANA zone을 지원한다. 변수·좌표·날짜·timezone은 URL과 metadata에 남는다.

`--imperial`은 Fahrenheit/인치를 요청해 degC/mm로 변환한다. 기존 풍속은 `--variables temperature_2m,precipitation,wind_speed_10m`으로 시험할 수 있다. 함수 `request_url` 기본 변수는 기존 3변수 호환성을 유지하고 CLI는 사용자 지정 2변수를 기본으로 삼는다.

일반 Codex sandbox의 네트워크는 WinError 10013으로 차단됐고 승인된 네트워크 실행으로 성공했다. API 장애가 아니며 TLS 검증을 끄지 않는다. 요청당 30초, 최대 4MB, 최대 3회 재시도, 1~31일 기간. 429/일시적 5xx의 Retry-After를 지키고 30초 초과 대기는 나중 재시도하도록 중단한다. 400·권한 오류는 무작정 재시도하지 않는다. 장기 자동화/계정 전체 호출량 제한기는 구현하지 않았다.

## 처리 계약

| 항목 | 처리 |
|---|---|
| 반복 수집 | 행 키는 series+UTC초+변수. 이벤트는 hash+URL+수집시각. 동일 파일 재생은 멱등, 최신 수집만 갱신. 과거와 같은 bytes를 새로 받으면 새 이벤트로 반영 |
| 빈 응답 | ContractError로 거절. 기존 DB 값·이벤트 유지. 성공한 0행으로 오인하지 않음 |
| 값 null | SQL NULL + source_null. 0 채움/보간 없음 |
| 시각 누락 | 요청 기간의 빠진 시각에 NULL + absent_timestamp 생성. 값 null과 구별 |
| 계약 오류 | 배열 길이/시간 정렬/중복·범위/단위/비유한 숫자를 쓰기 전에 검증. 미지원 sentinel은 임의 해석하지 않음 |
| 시간 | UNIX UTC 정수초 저장. 서울 날짜 경계는 tzdata로 계산, 응답 timezone/offset 검증. query는 start 포함/end 제외 |
| 단위 | 원값·원단위와 변환값·표준단위 보존. degC/mm/m/s. 강수 interval_start_utc=t-3600 및 interval_seconds=3600 |
| 수정 이력 | 최신 fetched_at 우선. 같은 시각 다른 내용은 기존 유지. 공급자 발행 버전과 수집시각은 다름. 원본으로 이전값 복원 |

`series.metadata_json`은 provider, reanalysis/ERA5, 요청·반환 좌표, 고도다. `imports`는 URL·raw SHA256·수집시각·응답 metadata·원본 경로, `measurements`는 시간·변수·단위·품질·수집 연결이다. 절대 원본 경로는 provenance 참고이며 복사본 재실행은 상대 fixture 경로를 쓴다.

강수 `sum_available`은 선택된 행 중 이용 가능한 합이다. 완전한 기간 합/미수집 기간 커버리지를 보장하지 않는다. 달력일 강수 총량은 구간 기준으로 조회 창과 추가 종료 timestamp를 맞춰야 한다. 빈 응답·실결측·HTTP 429/400·DST는 **주입 테스트**이며 API에서 그런 사례를 받았다고 주장하지 않는다.

## 재료와 조사

- `weather_path.py`, `reproduce.py`, `test_weather_path.py`: 핵심 경로·재현·테스트.
- `fixtures/seoul-requested-20260901.json` 및 `.meta.json`: 실제 고정 응답·출처. 최초 수집 2026-09-08T09:59:39Z, SHA256 `b416268fc89fd4feae86714a082ee1180bbf611712adb57704a5a3317ac3b3c1`.
- `output/requested-reproduction/`, `output/requested-live/`, `output/tests-requested.txt`: 최신 DB·조회·수집 원본·28개 테스트.
- `alternatives/`: 독립 처리 대안·실행·반증 기록. 특히 `requested-followup.md`와 `requested-reproduction/`가 현재 범위의 독립 확인. pandas 비교에는 `requirements-comparison.txt` 사용.
- `../R001/provider-discovery.md`: API/정적 관측파일/통합 라이브러리 비교. DWD·NOAA·NASA 전체 어댑터는 미구현.
- `README-initial.md`, 2025 fixture와 초기 output: 사용자 좌표/날짜 확정 전 실험 이력. 현재 기본 명령은 이 문서를 따른다. 구형 schema는 조용히 바꾸지 않고 새 DB에 fixture를 재생하도록 오류를 낸다.

출처: [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api), ERA5/Copernicus Climate Change Service. raw는 그대로이고 SQLite 값은 단위·시간·품질 구조를 변환했다. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 출처 표시를 유지한다. [무료 API 이용약관](https://open-meteo.com/en/terms)은 비상업용과 분/시/일 호출 제한을 별도로 둔다. 계정·키·결제를 사용하지 않았으며 미래 상업 제품의 무키 무료 운영을 허용한다는 결론은 아니다.

미검증: 실제 관측소 QC/trace, 대규모·장기 성능, 자동보간 정확성, 모든 공급자·변수, 영구 불변 공급자 revision. CLI·스키마는 연구 재료이며 이후 제작자가 재구성할 수 있다.
