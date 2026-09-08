# Research R001: 무계정 공개 기상 데이터를 어떤 방식으로 실제 확보할 수 있는가?
- 상태: 확정
- 기준: [Topology](../topology.md)의 실제 수집·출처·접근 조건
- 확인: 2026-09-08, Windows/Python3.12.10
- 현재 우선 입력: 사용자 지정 서울37.5665/126.9780, 현지 날짜2026-09-01~02, 시간별 기온·강수. 실제48행 수집 성공·fallback 없음. 아래 초기 비교와 마지막 후속 검증을 함께 보존한다.

## 질문·달성 조건
계정·키·개인정보·유료 서비스를 쓰지 않고 공개 기상 데이터의 제공 방식과 적용 조건을 비교한다. 모델/관측의 의미, 시간·지역, 라이선스와 최신성을 구분하고 실제 한 경로 이상의 응답과 출처·수집시각·해시를 확보한다. 관측 또는 모델 중 하나를 사용자의 필수 요구로 새로 정하지 않는다.

## 비교·판정
| 접근 | 직접 근거와 실제 실행 | 적용 판단 |
|---|---|---|
| Open-Meteo archive JSON + 일반 HTTP 또는 공식 client | [공식 사양](https://open-meteo.com/en/docs/historical-weather-api), [API 조건](https://open-meteo.com/en/terms). 초기2024년 서울 예시 ERA5 SI48행 및 imperial48행 실제HTTP200, 잘못된 변수는 실제400. | 작은 좌표·기간 재분석 실험으로 채택. 관측소 실측이 아니고 반환은 격자좌표다. 비상업 무료API 조건을 데이터 CC BY4.0과 분리. 모델과 요청·반환좌표 모두 저장. |
| NOAA ISD-Lite 역사 관측 gzip + 표준 파서 | [형식](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt), [UTC 근거 ISD문서 p5](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf). 실제471080-99999/2024 파일94,995bytes·8,430행 수집/저장/조회. | 역사 관측의 독립 대안으로 채택. 누락354시간·미량강수130건 발견. 지점ID는 확인했으나 별도 좌표 메타데이터는 미검증이므로 서울 좌표API와 같은 지점/동일기상이라고 수치 비교하지 않는다. |
| NOAA GHCNh station/year PSV 또는 Parquet | [공식 제품](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly), [v1.1.0 문서](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf). 실제PSV prefix206·65,536bytes·완전63행 확인. | 현재 권장 후속 관측자료. UTC이지만 분단위 시각·소수값·QC/출처 필드라 ISD정시/정수배율 어댑터를 재사용할 수 없음. 전용 저장 어댑터는 미구현; 접근·형식 판정만 성공. |
| Meteostat station/year CSV.gz, bulk Parquet, Python | [현재 접근개요](https://dev.meteostat.net/data), [CSV계약](https://dev.meteostat.net/data/timeseries/hourly), [Python](https://dev.meteostat.net/python). 공식 본문·현재API/소스 확인, 자체 다운로드/클라이언트 실행은 하지 않음. | 두 파일 경로는 공존한다. 관측 누락의 모델 보완·변수별_source를 보존해야 함. 관측소 검색·다수 공급자·보간용 재사용 후보; 이번 최소 경로의 필수 의존성으로 채택하지 않음. |
| MET Norway GeoJSON / NWS API | [MET 계약](https://api.met.no/doc/TermsOfService), [집계기간](https://api.met.no/doc/ForecastJSON), [NWS 공식](https://www.weather.gov/documentation/services-web-api). 본문만 확인. | 다른 예보·관측API의 계약 비교. MET 실제 프로젝트식별자 필요, 다음1/6시간 강수와 가변간격; NWS User-Agent필요·미국 중심. 실행 성공으로 세지 않으며 과거자료 대안보다 추가 호출 효용 낮음. |

독립 탐색자 weather_sources는 제공해법/공식클라이언트를, weather_alternatives는 아카이브·인접처리·실패를 맡았다. 무이력 생성은 실제 fork_turns=none으로 지원됐다. 각자 lab 하위 파일만 소유했고 메인은 결정적인 공식 본문·반환 코드·결과를 재확인했다. 같은 NOAA를 재사용하는 Meteostat 설명을 별도 관측원으로 합산하지 않았다. 상세 비교·공식클라이언트 버전/유지/라이선스는 [source comparison](../lab/R001/source-research/comparison.md), 대체 접근·실행은 [alternative README](../lab/R002/alternative-research/README.md) 참조.

## 실패와 판단 갱신
- 일반 sandbox GET은 WinError10013. 범위 내 공개GET 권한 상승 뒤 실제 성공. 계정/키/인증 우회 없음. 원본 JSON/압축바이트를 보존했으며 웹 설명을 실행 성공으로 대신하지 않았다.
- NOAA 일반제품 소개의 ‘현재까지’는 [2026-06-23 이전공지](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly)와 충돌. 메인도 공지 본문을 확인: ISD는2025-08-24 이후 갱신없음, 기존FTP/HTTPS 종료계획2026-07-31, NODD 이전과 GHCNh 권고. 오늘 기존2024파일 GET성공은 장래유지/최신자료 보장이 아니다. 추정 NODD 파일경로404는 대체 URL로 배포하지 않는다.
- Meteostat의CSV/Parquet 설명 차이는 제품폐기 증거가 아니라 서로 다른 time-series/bulk 경로였음을 현재 개요와 각 원문으로 해소했다. 현재2.x Python과 과거 Hourly 예제를 구분했다.
- GHCNh PDF Web도구 형식실패→공개다운로드/본문추출, ISD공지 일시timeout→공개GET 대체. 핵심근거는 확보했으나 지점목록·최신갱신지연은 미검증.
- 실제 API400 JSON을 보존했다. 429·장애재시도는 합성 테스트이며 실제서비스에 부하를 주어 유발하지 않았다.

## 재료·결론
[인계/실행방법](../HANDOFF.md), lab/R001/samples 및 adapter-samples, lab/R002/alternative-research의 raw/meta/log. 메인 활동은 작업 records/activity.jsonl, 탐색자 각 하위 activity.jsonl에 있다.

판정: **결론 가능**. 실제 제공자 두 계열의 전체 입력을 확보하고 세 번째후속포맷의 접근을 확인했다. 직접API·파일·클라이언트·처리실패 비교가 확보됐고 중요한 최신성 충돌도 해결했다. 추가 서비스 목록은 현재기능의 선택을 바꾸기 어렵다. GHCNh 최신전체수집, Meteostat 실행, 특정상업사용 허용, 대규모운영은 이번 달성조건 밖의 열린 선택이다. 전체제품 화면·UX는 결정하지 않았다.

## 사용자 지정 날짜·변수 후속 검증 (2026-09-08)
사용자가 서울37.5665/126.9780, 시간별 기온·강수, 2026-09-01~09-02를 우선 입력으로 확정했다. 날짜는 서울 현지 달력일로 해석하고 timezone=Asia/Seoul + timeformat=unixtime으로 요청했다. 기존2024년 자료는 초기 비교/회귀 자료로 보존하며 새우선입력으로 대체한 것이 아니다.

실제 GET은 성공했다. 첫SI·실제SI재수집·imperial변형 세응답 각각48행이며 날짜 fallback은 사용하지 않았다. 첫UTC epoch1788188400=8/31 15:00Z=서울9/1 00:00, 마지막1788357600=서울9/2 23:00이다. 요청한변수는기온/강수뿐이며 반환units도°C/mm이다. 원본과meta는 lab/R001/requested-samples, 통합결과는 lab/R002/output/requested-run-summary.json에있다.

원천 [CDS ERA5 본문](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)과 [API](https://open-meteo.com/en/docs/historical-weather-api)를 후속탐색자와메인이재확인했다. ERA5는관측과모델을결합한재분석이며약5일지연의조기자료ERA5T가2~3개월후최종판에서달라질수있다. 이번API응답에는최종판상태를입증할필드가없다. 고정과거시각의접근에는성공했으나영구불변인최종자료라고보장하지않고수집시각/원본바이트/해시로실험snapshot을고정한다. 추가원천계약은 [seoul-september-contract.md](../lab/R001/source-research/seoul-september-contract.md)에있다.

기존R001의결론가능판정은유지한다. 현재결론의우선입력은이후속요구이며,2024년자료및NOAA는기능비교·실제결측·실패경험의보조재료다.
