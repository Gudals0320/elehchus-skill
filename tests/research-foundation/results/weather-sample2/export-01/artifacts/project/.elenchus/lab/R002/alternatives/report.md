# R002 처리 대안·반증 조사 반환

작성자: processing_discovery 독립 하위작업. 확인일: 2026-09-08 UTC. 제품 화면/UX를 정하지 않았으며, 추가 패키지 설치·공급자 수집은 수행하지 않았다. 공식 웹 문서와 기존 R001 실제 응답, R002 기본 Python/연구 venv만 사용했다.

## 판단

현재처럼 세 변수·짧은 기간의 의미 보존과 SQLite 조회를 검증하는 재료는 Python 표준 라이브러리로 충분히 실행됐다. pandas도 같은 값을 계산했으며 분석 단계의 편의가 있다. 두 방식 모두 공급자 계약 검증·단위 매핑·강수 구간·수집 이력을 별도 구현해야 한다. Polars/Arrow와 기상 client는 다른 사용 조건을 가진 후보이며, 이번 실행으로 속도나 운영 적합성을 순위 매기지 않았다.

## 대안과 선택 조건

| 접근 | 직접 확인한 근거 | 가져올 기능 / 주의할 의미 | 이번 범위의 판단 |
|---|---|---|---|
| 표준 `datetime`/`zoneinfo`/`sqlite3` | [Python 3.12 sqlite3](https://docs.python.org/3.12/library/sqlite3.html#default-adapters-and-converters-deprecated), [zoneinfo](https://docs.python.org/3.12/library/zoneinfo.html#data-sources), 실제 실행 | UTC epoch 정수와 명시적 NULL/단위/품질 열은 driver 자동 datetime 변환에 의존하지 않는다. 기본 timestamp converter는 offset을 버리며 3.12부터 deprecated다. Windows에서 IANA 표시에는 tzdata가 필요할 수 있다. | UTC 경로는 가상환경 밖 Python 3.12.10에서도 재현. IANA 변환은 기존 tzdata 환경에서 검증. |
| pandas 3.0.5 | [tz_localize](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.dt.tz_localize.html), [sum](https://pandas.pydata.org/docs/reference/api/pandas.Series.sum.html), [to_sql](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html), 실제 실행 | 벡터 단위 변환·UTC 생성·reindex·집계가 편하다. `tz_localize`는 naive 벽시계를 해석하는 연산이며 모호/존재하지 않는 시각을 기본적으로 거절한다. all-null `sum()` 기본값 0은 강수 없음으로 오해할 수 있어 `min_count=1`과 유효/예상 개수를 함께 둬야 한다. `to_sql`의 replace는 테이블을 바꾸고 append 자체는 upsert 정책이 아니다. sqlite3.Connection 삽입 rollback 제한도 문서에 있다. | 실제 432개 값 일치. 분석용 대안으로 남김. pandas 도입이 의미 검증과 provenance를 대체하지 않는다. |
| Polars | [null/NaN](https://docs.pola.rs/user-guide/expressions/missing-data/), [timezones](https://docs.pola.rs/user-guide/transformations/time-series/timezones/), [write_database](https://docs.pola.rs/api/python/stable/reference/api/polars.DataFrame.write_database.html) 본문 | null과 NaN은 다르다. null_count/fill_null은 NaN을 처리하지 않고, NaN은 집계에 전파될 수 있다. 한 Datetime 열은 한 timezone을 가지므로 UTC 공통화가 필요하다. DB 쓰기는 SQLAlchemy/ADBC 경로이며 SQLAlchemy 엔진은 현재 pandas.to_sql을 사용한다. | 미설치·미실행. 열 기반 처리가 필요한 후속 규모에서 실험할 후보. 성능 우월성은 주장하지 않음. |
| Arrow 형식/교환 | [timestamp](https://arrow.apache.org/docs/python/timestamps.html), [columnar validity](https://arrow.apache.org/docs/format/Columnar.html) 본문 | timestamp의 정수 값과 시간 해상도·선택적 timezone 메타데이터, 값과 별도의 null validity를 제공한다. 이 형식의 null이 공급자 sentinel의 뜻이나 강수 집계 구간을 정해 주지는 않는다(추론). | 미설치·미실행. 여러 분석 엔진으로 자료를 전달할 때의 후보이며 이번 SQLite 요구를 대체하지 않음. |
| Open-Meteo 공식 Python client | [공식 README](https://github.com/open-meteo/python-requests/blob/main/README.md) 본문 | 변수 enum/고도 선택, 시작/종료/간격과 NumPy 배열, pandas/Polars 예제, session cache/retry 구성이 있다. 읽은 pandas 예제는 `pd.to_datetime(...,unit='s')`에 UTC 표시가 없으므로 그대로 복사하면 naive index가 된다. 적용 시 `utc=True`를 명시해야 한다(문서 코드로부터의 추론). SQLite cache는 원본 수집 이력과 목적이 다르다. | 미설치·미실행. 요청량/배열 처리 편의를 얻을 수 있으나 원본·수집시각·null 의미는 어댑터가 보존해야 함. |
| Meteostat 인접 해법 | [normalize](https://dev.meteostat.net/python/api/timeseries/normalize.html), [interpolate](https://dev.meteostat.net/python/api/timeseries/interpolate.html) 본문 | 시간축에 빠진 자리를 만드는 작업과 값을 추정해 채우는 작업을 분리한다. 문서의 interpolate는 normalize 후 적용하며 기본 limit=3이다. 이번 재료에서는 전자의 구분을 가져오고 실제 값을 채우는 보간은 별도 연구 대상으로 남긴다. | 페이지의 예제는 과거 API 문서이며 현재 client 버전의 실행 계약으로 확대하지 않음. 설치·실제 호출 미검증. |

강수는 [Open-Meteo Historical API의 hourly parameter definition](https://open-meteo.com/en/docs/historical-weather-api)에서 이전 한 시간의 합계이고, temperature/wind는 해당 시각 값이다. 따라서 동일 timestamp라도 같은 집계 종류가 아니다. 현재 메인의 `interval_start_utc=t-3600`, `interval_seconds=3600`은 이 정의와 맞는다. 전체 기간 합계를 해석할 때 `[start,end)`의 시각 필터가 강수 구간 종료시각을 고른다는 조건을 유지해야 한다.

## 실제 실험과 실패 경험

대표 최신 결과: [runs/20260908T095203744861Z/results.json](runs/20260908T095203744861Z/results.json). Python 3.12.10 / SQLite 3.49.1 / pandas 3.0.5. 시험한 메인 사본 SHA256은 `eb3ec468efab7470f273384c2a4dc0ac8453945d2a06c5cad95443368c073ab6`이며 같은 run에 코드 사본이 있다.

1. **실제 입력 대조:** 겨울 metric 72시간/216값, 여름 imperial 72시간/216값의 독립 pandas 변환과 메인 결과를 대조했다. 최대 절대 오차는 각각 `4.44e-16`, `3.55e-15`이다. 이 둘은 기간이 달라 동일 기간의 metric/imperial API 반올림 차이 검증은 아니다. 원본 응답과 metadata의 실행 전후 해시가 보존됐다.
2. **DST 경계 주입:** New York 2025-11-02 01:30이 `-04:00`/fold 0와 `-05:00`/fold 1로 각각 보존됐다. naive 01:30 가을 시각과 2025-03-09 02:30 봄 시각은 pandas 기본 설정에서 ValueError. 표준 `replace(tzinfo=...)`는 이 검증을 수행하지 않으며, 봄 02:30을 UTC 왕복하면 03:30으로 바뀌었다. 메인의 UTC 입력 정책은 이 모호성을 피한다.
3. **결측 주입:** pandas float 열의 None/NaN은 모두 NA로 취급되고 SQLite에 NULL로 쓰였다. 숫자 0과 -999는 숫자로 남았다. SQLite 직접 바인딩에서는 NaN이 NULL, infinity가 REAL inf가 됐다. all-null 합계는 pandas 기본 0, pandas `min_count=1`은 NA, SQLite `sum`은 NULL이었다. 이에 따라 쓰기 전 `isfinite` 확인과 별도 source_null/absent_timestamp 품질이 필요하다.
4. **실험 순서의 부수효과 발견:** 첫 실험은 pandas.to_sql 뒤에 timestamp converter를 시험해 offset이 보존됐다. 이를 기본 sqlite3 동작으로 해석하지 않고 순서를 바꿔 재실험했다. to_sql **이전**에는 `2025-01-01T00:00:00.123456+09:00`이 offset 없는 datetime으로 돌아왔고 deprecation 경고 2개, **이후**에는 offset 보존·경고 없음이었다. [pandas v3.0.5 소스](https://github.com/pandas-dev/pandas/blob/v3.0.5/pandas/io/sql.py)의 `_register_date_adapters`와 로컬 설치 소스 2553–2580행에서 전역 sqlite3 adapter/converter 등록을 확인했다. 메인의 integer epoch 경로는 이 변화에 의존하지 않는다.
5. **입력 검증 주입:** NaN 온도·음수 강수 sentinel·미지원 K 단위는 ContractError였다. 첫 timestamp 전체 제거는 세 변수의 absent_timestamp 3개, 한 source null은 source_null 1개로 구별됐다. 이는 실제 제공자 결측 관측이 아니라 복사본에 만든 시나리오이다.
6. **재수집 정책 결함과 수정 검증:** 최초 정적 검토에서 무조건 UPSERT의 과거 파일 회귀 위험을 전달했다. 실행 전에 메인에서 시간 guard를 추가했으므로 미수정 production 경로를 실행했다고 주장하지 않는다. 이후 [두 번째 실행](runs/20260908T094949960532Z/results.json)은 A(t1)→B(t2)→과거 A(t1)는 B 유지하지만, 새 수집 A(t3)가 A(t1)과 같은 bytes이면 `UNIQUE(sha256,url)` 때문에 무시됨을 실제 재현했다. 메인은 수집 이벤트 키에 fetched_at을 추가했다. 최신 재실험은 과거 A(t1)는 B를 유지하고 새로운 A(t3)는 import3으로 반영했으며 모든 단계 216행을 유지했다. [SQLite UPSERT 공식 예제](https://sqlite.org/lang_upsert.html)의 조건부 갱신은 시간 guard를 지원하지만, 이벤트 식별은 별도 설계가 필요하다는 사례다.

## 독립 재현과 인계

[clean-reproduction-v2/output/reproduction.json](clean-reproduction-v2/output/reproduction.json)은 최신 코드·reproduce.py·실제 fixture 두 쌍만 다른 폴더에 복사한 결과다. 기본 `C:/Program Files/Python312/python.exe`는 `sys.prefix==sys.base_prefix`, pandas/tzdata 미설치 상태였으며 UTC 경로에서 **432행**, fixture 재입력 후 **432행**, 강수 `sum_available=190.2968 mm`를 얻었다. 이 수치는 서로 떨어진 두 표본 기간의 사용 가능한 구간 합계다. 첫 복사본 결과는 clean-reproduction/에 시행착오 기록으로 보존했다.

R002에서:

```powershell
.\.venv\Scripts\python.exe -B .\alternatives\probe_processing.py
python -B .\alternatives\clean-reproduction-v2\reproduce.py --out .\alternatives\clean-reproduction-v2\output-replay
```

실험 결과는 주장별 관찰 기록이며 메인 test suite의 테스트 개수에 더하지 않는다. 재수집 최신/이력 정책, UTC epoch, 원값/원단위/품질 보존은 인계할 의미이고, 파일명·테이블명·분석 라이브러리는 후속 제작자의 재량이다. 대량 성능, Polars/Arrow/client 실행, 모든 공급자의 sentinel, 자동 보간 정확성은 검증하지 않았다. 대표 처리 경로에 영향을 바꿀 미해결 반증은 이번 범위에서 남지 않았고, 추가 동일 문서 검색의 효용은 낮다고 판단한다.
