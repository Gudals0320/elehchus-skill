# R001 공급 방식과 기존 구현 독립 탐색

- 상태: 이 위임 범위의 웹 비교 확정. 실제 수집·SQLite 기능 검증은 메인 연구의 별도 판정.
- 중립 질문: 계정·키·개인정보 입력·결제 없이 공개 기상 자료를 로컬에 가져올 때, 어떤 공급 구조와 구현을 재사용할 수 있으며 데이터 의미·계약·실패 조건은 무엇인가?
- 확인: 2026-09-08 UTC. 세부 확인시각·질문·URL·오류는 `records/provider-activity.jsonl`.
- 경계: input.md와 지정 skill의 SKILL/Research/Discovery/Web Evidence를 읽었다. 원본·기존 제품·다른 연구를 읽거나 수정하지 않았다. 이 파일과 지정 activity 파일만 작성했다. 추가 agent 생성·로그인·설치·실제 API 수집은 하지 않았다.

## 판단

**좌표를 입력하는 모델 JSON API와, 관측소 파일을 내려받는 관측 자료 수집은 모두 유력하지만 같은 데이터가 아니다.** 소량의 전 세계 좌표·과거 날씨에는 Open-Meteo 또는 NASA POWER가 구현 부담이 작다. 실제 관측·품질 플래그가 중요하면 DWD ZIP/CSV 또는 NOAA GHCNh PSV/Parquet를 택하고 관측소 메타데이터를 함께 보존해야 한다. 모든 공급자를 하나의 값으로 합치는 것은 권고하지 않는다. 데이터 의미와 공급자별 필드 변환을 분리하는 것은 에이전트 제안이며 최종 제품 선택은 아니다.

| 구조·후보 | 직접 확인한 의미·계약 | 적용 비용·제약 | 현재 판단 |
|---|---|---|---|
| **좌표·기간 HTTP GET → JSON: Open-Meteo archive** | 기상관측소 측정값이 아닌 재분석/모델. ERA5, ERA5-Land, IFS 등이며 Best Match가 혼합한다. 자유 API는 키 불필요·비상업 사용, 600회/분·5,000회/시·10,000회/일 한도. 데이터 CC BY 4.0과 API 이용 조건은 별개. [역사 API](https://open-meteo.com/en/docs/historical-weather-api), [이용약관](https://open-meteo.com/en/terms) | 표준 Python HTTP/JSON으로 충분. 요청 단위와 응답 units 확인, 반환 좌표/모델 기록. 장기 기후 비교에는 모델을 명시적으로 고정하는 편이 합리적. 무료 uptime 보장 없음. [요금 설명](https://open-meteo.com/en/pricing) | 작은 실제 경로 검증의 유력 후보. 관측 자료로 명명하면 안 됨. 미래 상업 서비스의 무키 무료 이용을 보장하지 않음. |
| **좌표·기간 HTTP GET → JSON/CSV: NASA POWER** | 기상자료는 MERRA-2·GEOS-IT 모델/동화, 0.5°×0.625° 격자. 태양자료는 위성 관측에서 모델로 추정. 시간 자료는 2001년 이후, LST 기본, UTC 선택. [원자료](https://power.larc.nasa.gov/docs/methodology/data/sources/), [시간 API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/) | 무료 공개 API 예제에 인증 단계가 없다. 1회 최대 15변수. 시평균이고 강수는 mm/hour. 시간값은 해당 시간의 시작. 최근 기상 자료는 2–3개월 후 더 안정된 자료로 교체되므로 다운로드 시점·버전을 저장. [공식 Python 예제](https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/), [시간 의미](https://power.larc.nasa.gov/docs/faqs/other/) | Open-Meteo와 독립 원천인 비교 후보. 단위·시간 구간 의미가 달라 숫자만 같은 열에 섞지 않음. 로컬 응답 미검증이며 장기 상업 재사용의 구체 조건은 이번 원문 확보 범위 밖. |
| **관측소별 ZIP → CSV: DWD CDC hourly** | 독일 2m 기온/습도 관측. ZIP에 자료와 관측소·장비·알고리즘 메타데이터, 세미콜론 구분 CSV, 기온 ℃/습도 %, YYYYMMDDHH24, QN 품질수준. 익명 OpenData 직접 다운로드, 데이터 CC BY 4.0. [익명 접근](https://www.dwd.de/EN/ourservices/cdc/cdc.html?lsbId=646268), [v24.03 명세](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/DESCRIPTION_obsgermany_climate_hourly_air_temperature_en.pdf) | `zipfile`+`csv` 가능. recent는 어제까지 500일 범위·매일 교체·QC 미완료. historical은 연간 갱신·해당 버전 QC 완료. 겹치는 기간 우선순위와 수정 이력 필요. 열 공백·품질·결측 처리 필요; UTC 적용과 측정값 결측 기호는 이 명세만으로 확정하지 않음. | 관측 자료의 소규모 정적 파일 실험에 유력. 독일 범위이므로 서울 관측 공급자로 쓰지 않음. |
| **관측소/연도 PSV 또는 Parquet: NOAA GHCNh** | ISD의 후속으로, 전 세계 고정 육상 관측소의 관측·다중 원천 통합·QC 정보 보존. 일별 갱신·연간/전체기간 관측소 파일. 메타데이터에서 CC0-1.0와 통상 무료 전자 다운로드 명시. [제품](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly), [공식 메타데이터](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C01688/html) | PSV는 기본 csv parser, Parquet는 PyArrow/Polars 등이 필요. 공식 PDF가 web 도구의 octet-stream 미지원으로 실패하고 파일 explorer는 JS shell만 읽혔다. 실제 헤더/단위/누락/QC 매핑·국내 관측소 가용성은 원자료 검증 전 확정 금지. | 장기적인 관측 경로의 유력 후보. 이 역할에서 실행 가능한 어댑터를 만들었다고 주장할 수 없음. |
| **구형 관측소/연도 gzip 고정폭: NOAA ISD-lite** | 8개 요소, 관측 시각을 정시에 맞춰 선택·축약하고 하위 시간 자료와 QC flags를 제거. 기온/풍속/강수 등 scale 10, 공통 결측 -9999, 강수 trace -1. [형식](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt), [선택과 한계](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-technical-document.txt) | gzip+기본 파싱은 가볍다. trace를 -0.1 mm 실측값으로 바꾸면 오류. 요소 사이 실제 관측 시각 차이가 최대 10분일 수 있다. 현재 [디렉터리](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/)는 2025까지만 표시; GHCNh 대체 전환을 고려해야 함. | 작은 역사 포맷 연습은 가능하나 최신 운영자료 기본값으로 추천하지 않음. |
| **통합 라이브러리·bulk: Meteostat** | 공식 hourly bulk는 연간 Parquet, 결측 관측을 모델로 대체, 값별 `_source` 열, 좌표는 별도 station DB join, beta로 schema 변경 가능. [bulk](https://dev.meteostat.net/data/bulk/hourly), [FAQ](https://dev.meteostat.net/faq.html) | 관측만 원하면 모델 대체를 끄거나 원천을 필터링해야 한다. [License](https://dev.meteostat.net/license)는 CC BY 4.0, FAQ는 CC BY-NC 4.0으로 공식 페이지끼리 불일치. Python 직접 원자료 provider 사용 시 개별 라이선스 확인 필요. | 편리한 대안이나 이 작업에서 순수 관측·재사용 계약을 단순화하는 근거로 채택하지 않음. |

## 실제 구현에서 가져올 요소

**Open-Meteo Python SDK**의 [Client.py](https://raw.githubusercontent.com/open-meteo/python-requests/main/openmeteo_requests/Client.py)를 직접 읽었다. 현재 main은 niquests를 사용하고 요청에 FlatBuffers 형식을 넣어 결과를 decode하며 400/429 응답을 별도 오류로 취급한다. [사용 예제](https://github.com/open-meteo/python-requests)는 변수 순서와 다중 위치 응답 배열, NumPy 선택을 보여 준다. 이점은 대량 배열 접근과 async; 작은 JSON→SQLite 검증에는 추가 SDK 의존성·순서 대응 비용이 이점보다 클 수 있다. 서버 AGPL과 클라이언트 코드 라이선스를 혼동하면 안 된다. SDK LICENSE raw 경로는 cache miss여서 코드 복사·설치는 하지 않았다.

**Wetterdienst**는 현재 [공식 저장소](https://github.com/earthobservations/wetterdienst)에서 Polars 기반 다중 국가 관측소 검색·단위 변환·QC 포함 결과 및 SQLite export를 설명하고 실제 Python 예제를 제공한다. 따라서 이 문제의 기존 통합 구현 사례다. README가 1.0 이전 breaking change 가능성과 버전 고정을 권고한다. [pyproject](https://raw.githubusercontent.com/earthobservations/wetterdienst/main/pyproject.toml)의 읽힌 snapshot은 0.119.0, Python >=3.10, Polars/PyArrow/aiohttp/pydantic/tzdata 등 다수 의존성이다. 최신 배포판 버전을 설치해 확인한 것은 아니다. noaa parser 추측 경로와 저장소 트리는 web 실패로 구현 본문을 얻지 못했으므로 GHCNh 세부 파싱이 검증되었다고 볼 수 없다.

**NASA 공식 예제**는 requests + pandas 또는 xarray로 구조화 응답을 읽는 실제 예를 제공한다. 30초 timeout, 응답 상태 확인, 여러 위치 반복을 가져올 수 있다. 문서 안의 오래된 multiprocessing 예제는 verify=False를 사용하므로 그대로 재사용하지 말고 TLS 검증을 유지해야 한다. 동시 요청은 5개를 넘기지 말라는 예제 주석과 과도한 요청 차단 안내가 있다. 본 작업 규모에는 직렬 소량 요청이 충분하다는 판단이다.

**제외한 경로:** NOAA CDO v2는 [공식 시작 문서](https://www.ncei.noaa.gov/cdo-web/webservices/getstarted)에 토큰 필수가 명시되어 이 제약에서 제외했다. 동일 NOAA라고 [NCEI Access Data Service](https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation) 및 bulk를 함께 제외하지 않았다. 제공 라이브러리의 AEMET/DMI/KNMI/Frost 등의 키 요구 공급자도 무키 후보와 구분했다.

## Windows/Python 적용 시 필요한 검증

다음은 문서와 코드에서 도출한 설계 제안이며 이 역할의 로컬 실행 결과가 아니다.

1. HTTP JSON 또는 ZIP/PSV는 Python 표준 라이브러리와 sqlite3로 시작 가능하다. Parquet·Wetterdienst는 바이너리 wheel와 패키지 설치, 캐시 위치를 추가 확인해야 한다. Windows가 이유라는 것만으로 미지원으로 판정하지 않는다.
2. UTC 값을 저장하는 기본 경로와 표시용 시간대 변환을 분리한다. Open-Meteo에 GMT/UTC와 원하는 단위를 명시하고 응답 units·UTC offset을 확인한다. NASA는 `time-standard=UTC`를 명시한다. Windows IANA 시간대 자료는 환경마다 다르므로 zoneinfo의 Asia/Seoul 사용은 실제로 확인하고, 없다면 tzdata 의존성 또는 UTC 전용 경로를 검토한다.
3. NULL은 원문 결측을 유지하고 자동 보간은 하지 않는다. trace, 품질 거절, 필드 미제공, 시각 자체 누락을 같은 숫자 0으로 만들지 않는다. 원시 토큰·정규화 값·quality/source/model을 보존한다.
4. temperature의 순간/평균, 강수의 직전/이후 시간 구간·누적/율, 모델 격자/관측소를 metadata에 담는다. timestamp만 같은 두 행을 동일 관측으로 간주하지 않는다.
5. raw 원본·요청 URL·수집 UTC·해시·응답 units·데이터 의미를 보존하고 공급자별 어댑터에서 검증 후 transaction으로 적재한다. 중복 키에는 provider, dataset/model, 위치 또는 station, timestamp, variable을 고려한다.
6. 최신 NOAA 전환, DWD historical/recent 중복, NASA 최근자료 교체, Meteostat beta처럼 자료는 변할 수 있다. 고정 날짜의 작은 fixture와 live 요청을 나누고 새 다운로드의 변경을 기록해야 한다.

## 근거 공백과 종료 범위

실제 웹 검색은 직접 API, 정적 관측 파일, 통합 라이브러리, 데이터 의미·라이선스·운영상 실패를 비교했다. 원문을 얻지 못한 GHCNh PDF/파일 목록은 공개 metadata·제품 문서·구형 포맷을 대조했지만 단위/누락값 계약까지 복원하지 않았다. 이 부분은 직접 raw 다운로드를 수행하는 Lab 과제로 남긴다. NASA endpoint와 DWD ZIP도 이 역할에서는 내려받지 않았다.

메인이 Open-Meteo 실제 수집을 수행 중이라고 전달받았지만 독립 관찰로 계산하지 않았다. 현재 공급 방식 선택을 바꿀 핵심 차이는 충분히 드러나므로 같은 소개 자료를 더 찾는 효용은 낮다. 다음 효용은 작은 실제 응답·한 관측소 파일의 수집과 파싱/SQLite 검증에서 나오며, 그것은 메인 연구 범위다. 이 문서는 API/정적파일 비교 완료이며 전체 사용자 기능의 실행 완료 선언이 아니다.

