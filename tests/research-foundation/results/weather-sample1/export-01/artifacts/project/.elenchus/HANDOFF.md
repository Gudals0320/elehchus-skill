# 개발자 인계: 서울 기온·강수 → SQLite

세션 상태: **완료**. 2026-09-08 사용자가 결과와 남은 한계를 확인하고 현재 결론으로 종료했다. 미검증 기능과 제품 선택은 그대로 남긴다.

검증일: 2026-09-08. 사용자 지정 위치는 위도 **37.5665**, 경도 **126.9780**이며, **서울 현지 날짜 2026-09-01~09-02의 시간별 기온·강수**를 우선 검증했다. 실제 요청에 성공해 날짜 대체는 하지 않았다. Windows, Python 3.12.10, SQLite 3.49.1, tzdata 2026.3에서 실행했다. 시스템 설정과 기존 제품 파일은 변경하지 않았다.

자료는 Open-Meteo를 통해 받은 **ERA5 재분석**이다. 관측과 모델을 결합한 격자 추정치이며 관측소 실측이나 현재 발행 예보라고 표시하지 않는다. 반환 격자좌표는37.5/127.0으로 요청한 도심 좌표와 다르다. 최근 ERA5는 약5일 지연의 조기 자료가 2~3개월 후 최종판에서 바뀔 수 있고, 이 API 응답에는 최종판 확정 필드가 없다. 따라서 원격 데이터의 영구 불변은 보장하지 않으며 **수집 당시 원본·시간·해시를 고정해 재현**한다. [API 의미](https://open-meteo.com/en/docs/historical-weather-api), [원천 ERA5 설명](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview).

## 오프라인 재현

아래 경로는 이 파일이 있는 `.elenchus/`를 기준으로 한다. PowerShell에서 `project/.elenchus/lab/R002`로 이동한 후 실행한다. 최초 패키지 설치에는 공개 PyPI 접근이 필요하며, 그 뒤 테스트와 replay는 보존된 응답만 사용한다.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip --isolated install --index-url https://pypi.org/simple --cache-dir .pip-cache -r requirements.txt
.venv/Scripts/python.exe -B -m unittest -v test_weather_pipeline
.venv/Scripts/python.exe -B replay_requested.py
```

현재 회귀 **22개 통과**. replay는 수집 당시SI·실제재수집SI·imperial 세 snapshot을 `output/requested-weather.sqlite`에 넣고 조회한다. 각48행, 총144행이며 조회는 dataset_id 하나를 선택한다. 같은 원본을 다시 넣으면 `inserted:false`이고 행수는 늘지 않는다. 출력은 `output/requested-run-summary.json`과 `output/requested-seoul-query.json`이다. 첫 라벨은9/1 00:00+09, 마지막은9/2 23:00+09, 기온48/강수48개가 모두 유효했다. 평균기온24.25°C는 이 보존된 재분석 샘플의 결과다.

SQLite STRICT는3.37 이상이 필요하다. UTC 저장·조회에는 표준Python만으로 충분하며 Windows에서 IANA 현지 시간/DST 변환에는 tzdata를 설치한다. 대안 pandas3.0.3 실험은 별도 폴더의 선택 의존성이다.

## 새 공개 수집 → 저장 → 조회

```powershell
$download = .venv/Scripts/python.exe -B weather_pipeline.py fetch --latitude 37.5665 --longitude 126.9780 --start 2026-09-01 --end 2026-09-02 --timezone Asia/Seoul --out ../R001/new-samples | ConvertFrom-Json
$stored = .venv/Scripts/python.exe -B weather_pipeline.py ingest --raw $download.raw_file --db output/live.sqlite | ConvertFrom-Json
.venv/Scripts/python.exe -B weather_pipeline.py query --db output/live.sqlite --dataset $stored.dataset_id --start 2026-09-01T00:00+09:00 --end 2026-09-03T00:00+09:00 --timezone Asia/Seoul
```

기본 변수는 기온·강수다. `--imperial`은 화씨·인치로 받아 동일 정규화를 검증하며 `--include-wind`는 선택적인 풍속 비교를 추가한다. 날짜는 API의 inclusive start/end, 조회 경계는 offset/Z가 있는 `[start,end)` 라벨 범위다. `timezone=Asia/Seoul`로 날짜를 선택하더라도 반환 `unixtime`은 UTC epoch초이므로 offset을 더해서 저장하지 않는다.

보존 원본 하나만 입력·조회하려면 다음과 같다.

```powershell
.venv/Scripts/python.exe -B weather_pipeline.py ingest --raw ../R001/requested-samples/20260908T082652425301Z-3c0cfd0e9f00.json --db output/replay-single.sqlite
.venv/Scripts/python.exe -B weather_pipeline.py query --db output/replay-single.sqlite --dataset 2b36521026c2c6188494e56beac3cc86b52f3e618d0ce9c2839b30511a84b078 --start 2026-09-01T00:00+09:00 --end 2026-09-03T00:00+09:00 --timezone Asia/Seoul
```

## 반복·빈 응답·누락·단위의 처리

| 조건 | 실제 재료의 동작·검증 범위 |
|---|---|
| 같은 원본 재입력 | URL+원본SHA dataset 키로 중복 방지. 같은 파일을 실제로 재입력해 inserted:false 확인. |
| 실제 반복 수집 | 새 timestamp/raw/meta를 보존. 이번 두 SI 응답은 기상 배열이 같았지만 generationtime_ms가 달라 raw SHA와 dataset이 다름. 수집 snapshot은 별도로 유지하며 특정 dataset 조회는48행이다. 데이터셋 전체를 평탄화해 중복 관측으로 합치지 않는다. 의미상 동일한 기상값을 하나로 축약하는 정책은 구현하지 않았다. |
| 빈 정상 응답 | 빈 배열과 units가 유효하면0행 snapshot; 평균/합은NULL, completeness:false. 실제API에서 빈 자료를 유발한 것은 아니며 합성 회귀로 검증. 오류 객체는 빈 성공으로 바꾸지 않고 거절. |
| 값 null / 명시0 | null은SQL NULL,0은0. NULL을 보간하거나0으로 채우지 않음. 실제 새ERA5 응답에는null이 없어서 합성으로 검증했고 별도 NOAA 실자료에서 실제 결측도 검증. |
| 시간 행 누락 | 내부 구멍은NULL행+missing_timestamp. 요청범위 가장자리 부족은 expected_hours와 completeness로 드러남. |
| 요청하지 않은 풍속 | 기존 wide schema의 풍속은NULL이지만quality=not_requested:wind_speed_10m으로 표기, 누락행수에 포함하지 않음. 요청한 변수 자체가 응답에서 사라지면 전체 거절. |
| 단위 차이 | °C/mm/m/s로 정규화하며 원units 보존. 지정날짜의실제°C/mm와°F/inch 응답 비교에서 최대차이는0.066667°C/0.0116mm로 제공자반올림범위 안. |
| 잘못된 형식 | 배열길이·시간중복/역순·미지원단위·NaN·음수강수·요청/반환변수불일치 등을 DB쓰기 전에 거절. 기존 데이터 변하지 않음. |
| 시간대 차이 | UTC정수로 저장, 조회에IANA zone 적용하고 offset 포함. 서울자정과 DST반복시각을 회귀로 검증. offset없는 조회경계는 거절. |

강수는 **라벨 직전1시간의 합**이다. query에 `precipitation_period_start_utc`와 `precipitation_period_end_utc`를 함께 제공한다. `precipitation_observed_sum_mm`는 반환된 시각 라벨에 대응하는 유효 강수 합이며 **서울9/1~2의 달력일 강수 총량이라고 부르면 안 된다**. 일 강수 집계에는 해당 물리 구간을 덮는 종료시각을 선택하고 마지막 경계 자료를 추가로 가져오는 별도 계약이 필요하다. all-null은 합도NULL이며 유효 건수와 completeness를 함께 제공한다.

## 코드·응답·검증 근거

- `lab/R002/weather_pipeline.py`: request_url/fetch/normalize/ingest/query_data와 CLI. `replay_requested.py`는 이번 사용자 입력을 보존 샘플로 재현한다.
- `lab/R001/requested-samples/`: 지정날짜 세 실제 응답과meta/fetch-events. 첫SI는2026-09-08 08:26UTC 수집·1,321bytes·SHA256 `3c0cfd0e9f00ddea36b5ad53a940afd23c14ff8c0367e2be2f2640e5c1576f91`.
- `lab/R002/test_weather_pipeline.py`와 `output/test-results-requested.txt`:22개 회귀 및 결과. 내부 테스트 임시DB는 test-output/아래에 만든다.
- `lab/R001/samples/`, `adapter-samples/`: 사용자 날짜 확정 전2024년 비교 실험의 실제 원본. 삭제하지 않고 단위·오류·회귀 보조자료로 유지. 현재 우선 입력을 대체한 결과가 아니다.
- `lab/R002/alternative-research/README.md`: NOAA8,430행 역사관측/미량강수 처리, pandas 비교, GHCNh64KB 접근·형식검증 및 재실행 안내. 최신 GHCNh 전체 어댑터는 미구현.
- `lab/R001/source-research/reproduction/`: 초기17개 독립새환경 검증. `reproduction-september/`에는 이번22개와 지정날짜 복제 재현을 기록한다. 이전 검증을 새코드 전체의 성공으로 대신하지 않는다.
- `lab/R002/verification/summary.json`: 메인의 NOAA 별도 복제 재현과 원본제품SHA 불변 검사.

SQLite datasets는 요청 URL·수집시각·원본 SHA·원units·모델/격자 metadata를 저장하며 hourly는 dataset_id+epoch를 NOT NULL 기본키로 삼는다. 외래키/STRICT·바인딩·트랜잭션을 사용한다. SHA는 보존 후 변조 탐지용이며 제공기관의 디지털 서명이 아니다. 별도의 제품 schema/migration/동시writer 설계는 아니다.

## 접근·사용 조건·제약

fetch는1~31일·2MB·정규화100,000행 상한을 둔 연구 재료다. GET은최대3회, 요청당25초 socket timeout이며 HTTP400은즉시중단한다. 429/일부5xx와통신오류는제한적으로재시도하고 Retry-After가30초를넘으면조기재요청없이중단한다. 실제400과sandboxWinError10013을보존했고429/장애재시도는합성으로검증했다. 이환경의공개GET은사용자허용범위네트워크권한상승후성공했다. TLS검증/시스템설정/인증설정을변경하지않았다.

Open-Meteo 무료 **호스팅API는비상업용**이다. 데이터의CC BY4.0과다른계약이므로후속상업제품의무료연결권한을뜻하지않는다. 원본및변환자료재배포시Open-Meteo, Copernicus Climate Change Service/ECMWF ERA5 출처·링크·변경사실을표시한다. 이작업은원본JSON을보존하고단위/시간/누락표현을SQLite용으로변환했다. [API조건](https://open-meteo.com/en/terms), [CC BY4.0](https://creativecommons.org/licenses/by/4.0/).

확인한시행착오: sandboxGET차단→공개GET권한상승, Windows ZoneInfoNotFoundError→격리tzdata, 테스트SQLite연결미종료WinError32→명시closing, 실제변수오타400, 관측자료의missing/trace, pandas자동SQL의PK/transaction한계, NOAA서비스이전과GHCNh형식차이. 자세한판정은 research/R001-public-access.md 및 R002-local-normalization.md에있다.

환경/패키지캐시자체는필수인계물이아니며고정requirements로재구성한다. 대규모/동시쓰기·지속수집운영·정확도평가·최신관측어댑터·자동보간·일강수집계·제품화면/전체UX는미검증또는미구현으로명시한다. 이후개발자는함수·폴더·스키마를재구성할수있으며사용자지정입력과데이터의실제의미·접근조건은보존해야한다.
