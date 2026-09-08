# R002: 시간·단위·누락을 보존하여 로컬 저장·조회하는가?

- 상태: 확정
- 기준/영향: [Topology](../topology.md), R001에서 확보한 실제 응답의 정규화·SQLite·개발자 재현
- 확인 환경: Windows/Python 3.12.10, SQLite 3.49.1, 별도 venv의 tzdata 2026.3/pandas 3.0.5

## 후속 범위·현재 기준

사용자가 지정한 서울 **37.5665,126.9780 / 2026-09-01~02 / 기온·강수량**을 우선 경로로 반영했다. CLI 기본값을 이 좌표·두 변수·Asia/Seoul 날짜로 변경하고 함수는 기존 표본 호환성을 유지했다. 날짜 요청은 UTC/GMT/Asia/Seoul, 조회 표시는 설치된 IANA zone을 지원한다. 서울 날짜 경계는 UTC epoch로 변환하고 응답 timezone/offset도 검증한다. 실제 시간범위는 KST09/0100:00~09/0223:00이며 UTC08/3115:00~09/0214:00이다.

현재 **28개 테스트 통과**. 새 두변수 실응답·서울 날짜 경계·빈응답 시 기존DB 불변·요청 변수/응답 timezone 계약을 추가했다. 고정 fixture 재생은 **96행·imports1개**, 두 번 실제 수집은 **96행·imports2개**를 확인했다. 같은 목적의 좁은 후속 실험이므로 별도 Research 번호나 새 탐색자 두 명을 다시 만들지 않고 기존 처리 조사자에게 검증을 맡겼다. 독립 사본에서도 venv/tzdata로 96행·동일재생96행·요청/격자좌표 보존을 확인했고 새 결함은 없었다. [후속 독립 결과](../lab/R002/alternatives/requested-followup.md).

최신 산출물은 [requested-reproduction](../lab/R002/output/requested-reproduction/), [실제 반복수집 DB와 원본](../lab/R002/output/requested-live/), [28개 테스트](../lab/R002/output/tests-requested.txt)다. 현재 재실행은 [README](../lab/R002/README.md)의 요청 preset을 따른다. 아래 432행·25개 테스트는 초기 표본 단계 기록이며 legacy preset으로 남았다.

최근 응답의 upstream revision은 미확인·수정 가능하다. 원본 bytes/수집시각을 고정해 재현한다. 강수94.7mm는 반환된48개 **직전시간 구간**의 사용가능 합이므로9/1~2 달력일 완전합으로 표시하지 않는다. 빈응답/null/DST/HTTP 오류는 주입 테스트이며 실제 새 표본에는 결측이 없다.

## 질문·달성 조건

시간·단위·결측값을 숫자로만 섞지 않고 처리할 방법을 비교한다. 실제 수집→정규화→SQLite 저장/조회, 오프라인 fixture 재현, DST·단위·NULL/시간 누락·잘못된 응답·재수집의 의미 있는 테스트가 실행돼야 한다. 실제 원본에는 없는 오류는 주입 테스트라고 표시한다. 제품 UX를 결정하지 않는다.

## 처리 접근 비교

| 방법 | 직접 근거와 적용 비용 | 판단 |
|---|---|---|
| 표준 urllib/json/datetime/sqlite3 | [Python 3.12 sqlite3](https://docs.python.org/3.12/library/sqlite3.html): 기본 timestamp converter는 offset을 버릴 수 있다. UTC 정수 seconds와 parameter binding으로 명시적 SQL 구현 | 핵심 경로 채택. 요청/변환/검증을 짧게 추적하고 UTC 재현은 무의존성 |
| pandas DataFrame→SQL | [to_sql](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html), [결측 의미](https://pandas.pydata.org/docs/user_guide/missing_data.html): nullable dtype/NaT를 알아야 하며 저장 DB와 datetime 동작을 확인해야 한다 | 실제 독립 변환으로 432값 대조. 재표본화/집계가 많으면 유력하나 nullable/시각 dtype와 SQLite adapter 부수효과를 명시해야 함 |
| Polars/Arrow와 전용 SDK FlatBuffers | [Open-Meteo client](https://github.com/open-meteo/python-requests): 배열 접근, 변수 순서, cache/retry 예제. Polars/Arrow는 넓은 columnar 자료에 유력 | 이번 작은 JSON에는 패키지/매핑 비용이 더 큼. 성능 우열을 benchmark하지 않았고 설치/실행하지 않은 후보는 문서 비교로만 처리 |
| 기상 통합 라이브러리 | [Wetterdienst](https://github.com/earthobservations/wetterdienst) 등의 다중 공급자 QC/단위 처리 | 실제 관측 자료가 다음 요구가 되면 재사용 후보. 이번 공급자 어댑터와 동일 검증을 했다고 주장하지 않음 |

상세 원문·실험·한계는 [독립 처리 조사](../lab/R002/alternatives/)에 있다. 외부 client 코드를 복사하지 않고 본 연구의 작은 코드를 작성했다.

## 시간·단위·누락·수집 계약

API에 ERA5·GMT·unixtime를 명시해 UTC 초를 받는다. [Open-Meteo 시간/단위 정의](https://open-meteo.com/en/docs/historical-weather-api)에 따라 기온·풍속은 순간값, 강수는 표시 시각 직전 1시간 합이다. 원래 값/단위와 정규화 값(degC/mm/m/s), 구간 시작/길이, 요청/반환 격자와 모델·해시·수집시각을 저장한다. 조회는 시작 포함/끝 제외이고 지역 시간은 IANA 표시로만 변환한다.

SQLite NULL과 quality(source_null/absent_timestamp)를 구분해 0 채움·보간하지 않는다. 정규화 이전에 전체 계약을 검증하며 빈 응답/배열 불일치/비정상 시각·단위/비유한 숫자를 거절한다. 수집 기간 안 빠진 시각은 의도적으로 확장한 NULL 행이다. 미수집 기간 전체를 자동 커버리지 계산하지 않으며 강수 `sum_available`은 관측 가능한 선택 행의 합이다.

시계열 키는 공급자·모델·요청 및 반환 격자·고도에 기반한다. 수집 이벤트는 hash+URL+수집시각이다. 더 최신 수집 이벤트만 현재 값을 갱신하고 과거 fixture의 재생으로 회귀하지 않는다. 같은 byte를 새로 받은 수집 이벤트는 새 시각을 인정한다. 수집시각은 공급자 발행 버전이 아니므로 별도의 model revision 보장은 미검증이다.

## 시행착오·실행 결과

| 관찰 | 후속 행동·결과 | 증거 수준 |
|---|---|---|
| 기본 Python에 tzdata가 없어 Asia/Seoul ZoneInfoNotFoundError | 별도 venv와 고정 tzdata 의존성. UTC 경로는 표준 Python으로 유지 | 실제 오류와 복구. [공식 Windows 주의](https://docs.python.org/3/library/zoneinfo.html#data-sources)와 일치 |
| 최초 SDK 없이 winter/summer raw fixture 적재 | 72×3×2=432행, NULL 0. 재적재 후 432행 | 실제 응답·SQLite 조회 |
| 동일 여름 날짜 metric/imperial 출력 환산 차이 | 최대 차이 기온 0.05556℃, 강수 0.0126mm, 풍속 0.034681m/s. 응답 반올림에 따라 같은 시계열도 달라질 수 있음 | [실제 비교 JSON](../lab/R002/output/unit-comparison.json). 기상 정확도 비교 아님 |
| 입력 순서 UPSERT가 오래된 fixture로 회귀할 위험 | 독립 정적 검토 후 최신시각 guard 추가; old→new→old 독립 실행으로 수정 확인 | 초기 문제는 정적 발견, 수정 결과는 실제 주입 실행 |
| hash+URL만으로 dedup하면 이전 bytes를 다시 새로 수집한 사건을 누락 | 독립 A(t1)→B(t2)→A(t3) 실험에서 실패, fetched_at 포함 이벤트 키로 수정 및 회귀 테스트 | 주입 실험으로 실제 코드 오류 재현·복구. 라이브 API 오류 아님 |
| pandas.to_sql이 sqlite3 datetime converter를 등록하는 차이 | 메인 경로는 epoch int로 그 의존을 없앰. 독립 조사자가 clean/after 실험 기록 | 해당 설치 버전의 실제 부수효과, 전 pandas 버전으로 일반화하지 않음 |

현재 **25개 테스트 통과**: 실제 fixture, 출처 hash, 단위, 0/NULL/시각 부재, 배열·시각·unit 실패, DST 반복시간 구분, SQL 재적재/신규수집/구형재생, HTTP 429/400 transport 주입. HTTP 재시도 사례와 결측은 모의다. 실제 응답에 NULL이 없었으므로 공급자 실결측 성공을 주장하지 않는다.

메인 `python reproduce.py --out output/final-reproduction`은 패키지 없는 기본 Python으로 432행과 재적재를 확인했다. 독립 조사자도 코드와 fixture만 별도 복사한 작업장에서 기본 Python(pandas/tzdata 미설치)로 432행 재현했다. 전체 테스트와 IANA 표시는 venv에서 확인했다. 실제 fetch와 DB 연결은 `weather_path.py fetch ... --db ...`로 수행하고 원본을 보존했다.

## 전달·판정

[README 및 정확한 실행 명령](../lab/R002/README.md), [핵심 코드](../lab/R002/weather_path.py), [테스트](../lab/R002/test_weather_path.py), [fixture](../lab/R002/fixtures/), [최종 DB/조회](../lab/R002/output/final-reproduction/)를 사용한다. 초기 DB는 수정 전 실험 기록으로 보존하고 최종 ingest에 구형 schema를 사용하면 새 DB 재생 안내를 낸다.

접근법/근거/적용 비용/선택/종료 근거를 대조했다. 더 많은 라이브러리 설치로 작은 대표 경로 판단을 바꿀 가능성은 낮고, 실제 발견된 재수집 결함과 시간·NULL 문제를 회귀 테스트로 닫았다. 대규모 성능/모든 기상변수/실제 관측소 QC·trace/다중 공급자 통합·장기 운영은 미검증이며 전체 제품의 채택 조건이 아니다. 이후 제작자는 스키마·CLI·제품 구조를 재구성할 수 있다.

**판정: 결론 가능.** 이번 기능 재료 목표 달성. 실제 자료 범위 밖의 테스트는 주입 검증으로만 보고한다.
