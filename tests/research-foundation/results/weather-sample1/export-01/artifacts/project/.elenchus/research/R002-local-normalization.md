# Research R002: 시간·단위·누락을 보존해 로컬 저장·조회하는 방법은 무엇인가?
- 상태: 확정
- 기준: [Topology](../topology.md), [R001의 실제 응답](R001-public-access.md)
- 환경: Windows, Python 3.12.10, SQLite 3.49.1, tzdata 2026.3; 대안 pandas 3.0.3
- 현재 검증: 서울9/1~2 기온·강수48라벨, 실제3회 수집 snapshot, 22개 테스트 및 독립 복제 재현 통과. 초기2024년/17개 결과는 과거 근거로 보존한다.

## 질문·달성 조건
실제 공개 응답을 정규화해 SQLite에 넣고 재연결로 조회한다. UTC/현지 시간, 단위, NULL/0, 빠진 시각, 재입력, 오류 입력의 원자성을 확인하고 대화 없이 오프라인 재현할 코드·fixture·테스트·인계를 남긴다.

## 처리 비교와 재료
| 방식 | 실제 검증 | 판단과 한계 |
|---|---|---|
| urllib/json/datetime/zoneinfo/sqlite3와 명시 schema | [weather_pipeline.py](../lab/R002/weather_pipeline.py). 실제 지정날짜 SI/재수집SI/imperial 각각48행 저장, 서울9/1~2 48라벨 조회. [22개 테스트](../lab/R002/test_weather_pipeline.py) 통과. | 작은 자료의 검증·출처·시간·트랜잭션 계약을 드러내기 쉬워 기본 재료로 채택. 성능 우월성은 주장하지 않음. Windows 현지 시간에는 tzdata 필요. |
| gzip 고정폭 관측 parser와 명시 SQL | [archive_sqlite.py](../lab/R002/alternative-research/archive_sqlite.py). 실제 8,430행, 누락 354시간/강수 missing 7,824/trace 130, 반복 입력 행수 유지·48h 조회 성공. 메인도 복제 작업장에서 재실행. | sentinel은 배율 적용 전에 구분. trace를 -0.1mm/0과 합치지 않고 NULL+상태로 보존. 모델값과 같은 테이블에 자동으로 합치지 않음. 이 어댑터는 고정 2024 fixture 범위. |
| pandas read_csv/to_datetime/to_sql | [실험](../lab/R002/alternative-research/pandas_probe.py)과 [결과](../lab/R002/alternative-research/pandas-results.json). 같은 자료의 행/결측 일치, 자동 SQL 중복과 외부 rollback 한계, trace/epoch 단위/mixed-offset 착오를 실제 재현. | 많은 변수·집계·재색인에 유용하나 저장 계약을 대신하지 않음. dtype/NA/UTC/epoch 단위와 미리 정한 schema·키·트랜잭션 필요. 설치 시간·메모리/성능 차이는 측정하지 않음. |
| 공식 weather client / Parquet | R001에서 공식 코드/API/배포 상태 비교. 설치·사용 실험은 미수행. | 관측소 검색·공급자 결합·대량 열 분석에 후보. 작은 JSON 경로를 작동시키기 위한 필수 의존성으로 삼지 않음. |

## 데이터 계약·판정 근거
UTC epoch 정수로 시각의 정체성을 저장하고 조회에만 IANA 시간대를 적용한다. offset 없는 조회 경계는 거절한다. DST의 반복 1시는 -04/-05로 구분하는 합성 회귀를 통과했다. [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html)의 Windows DB 부재 설명을 실제 ZoneInfoNotFoundError로 확인하고 격리 venv에 tzdata를 고정 설치했다.

단위는 °C/mm/m/s로 변환하고 원본 units를 metadata에 유지한다. 실제 imperial 응답을 같은 기간 SI와 비교해 제공자 반올림 범위 내 일치를 확인했다. JSON null은 NULL, 0은 0, 누락 시간은 missing_timestamp 행으로 남긴다. unknown unit·잘못된 배열·중복 시간·NaN·음수 강수는 전체 검증 단계에서 거절하며 기존 DB는 변하지 않는다. HTTP200이라도 오류 객체를 데이터로 취급하지 않는다.

데이터셋은 URL+원본 SHA 키, 시간별 행은 dataset+epoch의 NOT NULL PK다. 같은 원본 재입력은 중복이 없고 다른 스냅샷은 보존한다. STRICT 테이블과 외래키/바인딩·트랜잭션을 사용한다. [SQLite STRICT](https://www.sqlite.org/stricttables.html), [Python sqlite3](https://docs.python.org/3.12/library/sqlite3.html). SQLite 기본 REAL은 문자 NA를 받고 AVG를 오염시킬 수 있으며 nullable 복합 PK는 중복 NULL을 허용하는 반증을 대안 실험에서 재현했다.

강수는 Open-Meteo의 직전 1시간 합이라 instant 온도와 물리 구간이 다르다. query에 precipitation_period_start/end_utc를 제공한다. 조회 [start,end)는 시각 라벨 범위이며 유효 강수 합을 일 강수라고 부르지 않는다. 모두 누락이면 sum도 NULL, 부분 누락/가장자리 부족은 건수와 completeness로 드러낸다. 실제 NOAA 자료의 trace/공백을 모의 API 테스트와 구분했다.

## 실제 시행착오
1. 기본 Python에는 pandas/requests/tzdata가 없었다. 기본 경로는 표준 라이브러리, 현지 시간만 tzdata 2026.3, 독립 대안은 pandas 3.0.3으로 실행해 의존성을 분리했다.
2. 초기 17개 테스트 중 15 통과/2 cleanup 오류: 테스트의 sqlite3 connection context가 연결을 닫지 않아 Windows WinError32가 발생했다. contextlib.closing으로 테스트 연결을 수정한 뒤 17/17 통과했다. 실제 수집/조회 함수는 처음부터 명시적으로 닫았다.
3. API 400과 sandbox 네트워크 오류는 실제 관찰이다. 재시도 429·null·빈 응답·DST·손상 단위는 주입 테스트다. 실시간 서비스 장애나 모든 날짜의 정확성을 검증한 것으로 확대하지 않는다.

## 재현·종료 범위
[HANDOFF.md](../HANDOFF.md)에 격리 환경 구성, 네트워크 없이 실행하는 테스트와 fixture import, 새 공개 GET→import→query 명령, 출처/라이선스, 해시, 실행 결과를 제공한다. 원본 README와 제품 sentinel은 전후 SHA로 보존 확인했다.

독립 탐색자 weather_sources는 필요한 코드와 샘플만 자기 작업장에 복제하고 새 venv+tzdata를 설치했다. 기존 가상환경 재사용 없이 17개 테스트, SI 첫 입력 48행·재입력 무중복, 현지 24행 조회, imperial 별도 48행 입력에 성공했다. 상세는 lab/R001/source-research/reproduction에 있다. 메인의 별도 NOAA 복제 재현은 [verification/summary.json](../lab/R002/verification/summary.json)에 기록했다.

판정: **결론 가능**. 요청된 기능 재료의 실제 경로·실패 처리·대표 회귀가 확보됐다. 최신 GHCNh용 완전 어댑터·관측 품질 검증·대규모/동시 쓰기·스케줄러·자동 보간·전체 UX는 이번 작은 연구의 성공 범위와 구분한다. 지금 추가 라이브러리를 형식적으로 실행하기보다 확보된 계약을 재사용할 수 있다.

## 사용자 지정 날짜·변수의 실행 갱신
사용자확정입력은서울37.5665/126.9780,기온/강수,서울달력일2026-09-01~09-02다. 현재CLI fetch기본값도이를따른다. 선택풍속은 --include-wind로추가하며요청하지않은풍속NULL은quality=not_requested로표시해실제누락과구분한다. 요청/반환변수집합불일치도DB쓰기전에거절한다.

새실제응답세개를정규화해각48행으로저장하고,서울9/1 00:00~9/3 00:00미포함범위를조회해48행을확인했다. UTC epoch에응답offset32400초를다시더하지않았고,반환시각라벨처음/끝을직접검증했다. 두SI재수집의기상배열은동일하나원본SHA가달라별도snapshot으로보존한다. 동일파일의재입력은중복없다. 현재DB는3개dataset/총144행이며조회는한dataset을선택해중복자료를합치지않는다.

회귀는현재 **22개 통과**다. 기존17개에실제서울지정날짜/2변수,동일GET재수집과동일파일재입력의차이,실제해당날짜단위차이,요청변수누락거절,잘못된hourly객체거절을추가했다. 최대단위차이는0.066667°C/0.0116mm였다. 새결과는 lab/R002/output/test-results-requested.txt와requested-run-summary.json,독립복제재현은lab/R001/source-research/reproduction-september에있다. 기존17개독립재현은이전코드의기록으로그대로보존한다.

지정날짜응답에는null이없었으므로빈배열·변수null·빠진시간은합성회귀이며NOAA관측의실제누락경험과구분한다. 최근ERA5의추후수정가능성때문에재현은원격데이터영구불변에의존하지않고보존fixture를사용한다. 새실행명령은갱신된 [인계문서](../HANDOFF.md)와 replay_requested.py에있다.
