# R001 공개 제공 해법 조사

- 역할: 기존 공개 제공 해법·공식 구현 라이브러리 비교.
- 범위: 공식 공개 웹 근거 조사. 실제 데이터·SQLite 실행 성공은 메인 검증 대상.
- 질문: 비밀키·계정·개인정보·유료서비스 없이 가져올 수 있는 기상 데이터는 어떤 방식으로 제공되며, 관측/모델 의미·시간·단위·누락 처리에 어떤 차이가 있는가?
- 열린 선택: 지역, 기간, 시간 간격, 관측과 모델, 제공기관·라이브러리 모두 미리 고정하지 않는다.
- 필요한 근거: 공식 API/파일 사양과 코드·정책, 계정·비용·라이선스·호출 제한, 과거 또는 예측의 시간 의미, Python 재사용 경로.
- 탐색 방향: 좌표 기반 모델 API, 관측소 자료 API/라이브러리, 정부 원자료 파일 서비스. 인증 요구와 결측/시간 착오를 반증 관점으로 확인.
- 최초 release check: 메인이 이미 up_to_date 확인. 반복하지 않음.
- 제한: 다른 작업·결과·평가 자료를 읽지 않음. 추가 agent 없음.

## 비교 결론 (2026-09-08 KST 확인)

아래는 공식 본문·코드를 읽은 결과다. 실제 데이터 다운로드, 설치, SQLite 저장·조회 성공을 이 문서에서 주장하지 않는다. 선택은 메인의 Lab 결과 및 사용자 데이터 의미에 따른다.

| 접근 | 접근 조건·비용·라이선스·호출 제한 | 데이터 의미·지역·시간 | Python 재사용 경로와 판단 |
|---|---|---|---|
| Open-Meteo 좌표 기반 HTTP API | 무료 엔드포인트는 키 불필요. 비상업 용도로만 사용; 600/min, 5,000/hour, 10,000/day, 300,000/month 한도. CC BY 4.0 데이터와 서버의 AGPLv3는 별개. 데이터 라이선스의 상업 허용을 무료 호스팅 API의 상업 허용으로 해석하면 안 됨. [약관](https://open-meteo.com/en/terms), [가격·호출 계산](https://open-meteo.com/en/pricing) | archive는 관측을 결합한 **재분석/모델 자료**. ERA5는 전세계 1940년부터 시간별·5일 지연, ERA5-Land는 1950년부터·5일 지연, IFS는 2017년부터. 반환 좌표는 선택된 격자점이며 관측소 식별자가 아님. [Historical API, Data Sources/API Documentation](https://open-meteo.com/en/docs/historical-weather-api) | HTTP JSON을 표준 라이브러리로 파싱하거나 공식 openmeteo-requests 사용. 작고 재현 가능한 좌표·기간 질의에 적합. 관측이라고 저장할 수 없음. 호출량은 변수 10개 초과·2주 초과 등에 HTTP 요청 수보다 커질 수 있음. [공식 클라이언트](https://github.com/open-meteo/python-requests), [계산 설명](https://open-meteo.com/en/pricing) |
| Meteostat 관측소별 CSV.gz / Python | bulk는 무계정·무키. 캐시 권고, 악성 호출 금지; 읽은 bulk/terms 본문에는 수치 rate limit 없음. 데이터 무료, 재배포 자료 CC BY 4.0, 원 제공기관 직접 취득시 해당 기관 라이선스 적용. [Bulk Access](https://dev.meteostat.net/data/), [Terms](https://dev.meteostat.net/terms), [License](https://dev.meteostat.net/license) | 전세계 관측소 기반, 기간·완전성은 관측소별 다름. 연간 시간별 CSV는 역사 DB/METAR/SYNOP를 취합하며 **관측 결측을 모델로 보완**함. 변수별 `_source` 열 제공. [시간별 파일 사양](https://dev.meteostat.net/data/timeseries/hourly) | 공식 meteostat 2.1.4와 Pandas 경로 또는 gzip+csv. 관측소 검색·공급자 선택·보간 기능을 재사용할 수 있음. 기본 자료를 순수 관측으로 취급하면 부적합. `_source`를 보존하고 의도에 맞게 공급자 제한. [현재 Python 문서](https://dev.meteostat.net/python), [공급자](https://dev.meteostat.net/python/providers) |
| NOAA NCEI ISD / ISD-Lite HTTPS 파일 | 공개 디렉터리에서 station/year 단위 직접 취득. CDO의 이메일 토큰 API와 구분. CDO 데이터 자체는 무료. 검토한 파일/제품 사양에는 수치 요청 제한 없음. NCEI 일반 저작권 안내는 별도 표시가 없는 정부 자료의 미국 내 public domain과 외국 권리 가능성을 명시하므로 모든 국제 원천에 CC0를 단정하지 않음. [파일 디렉터리](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/), [CDO FAQ](https://www.ncei.noaa.gov/cdo-web/faq), [NCEI copyright](https://data.ngdc.noaa.gov/ngdcinfo/privacy.html) | ISD는 전세계 시간별·종관 **관측**; 구 제품 페이지의 1901~현재 표기는 최신 갱신 보장이 아님. 2026-06-23 공식 이전 공지에 따르면 2025-08-24 이후 갱신 중단(아래 정정 메모 참조). 지점별 공백·분포 편차 존재. Lite는 8변수·시간당 정리된 관측, 정시 직전 10분 창에서 선택한 값으로 변수간 실제 관측시각이 다를 수 있음. [제품 설명](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database), [Lite 기술문서](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-technical-document.txt) | gzip+고정폭 parser로 의존성을 줄이거나 Meteostat의 ISD_LITE 공급자 활용. 정확한 개별 관측시각·QC flag가 필요하면 full ISD를 선택. 관측 원자료를 정규화하는 재료에 적합하나 station metadata·형식·연도별 가용성 검증 필요. [형식](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt), [공급자 목록](https://dev.meteostat.net/providers) |
| MET Norway Locationforecast HTTP GeoJSON | 공개 무료 서비스, 별도 유료 상위 플랜 없음. 실제 앱/프로젝트와 연락 가능한 경로를 식별하는 User-Agent 요구; 허위·일반 UA는 차단 가능. 개인 이메일 대신 실제 프로젝트 URL도 가능하지만 현재 사용할 식별자가 합의돼 있지 않아 자동 실행 후보 보류. CC BY 4.0, 앱 전체 20 req/sec 초과는 별도 합의. Expires/Last-Modified 캐시 계약 준수. [Terms](https://api.met.no/doc/TermsOfService), [FAQ](https://api.met.no/doc/FAQ) | 전세계 최대 9일 **예보**. UTC이지만 시계열 간격이 1h에서 6h로 변할 수 있음. 다음 1/6/12시간 집계가 있는 경우만 제공되며 마지막 시점에는 instant만 존재. [HOWTO](https://api.met.no/doc/locationforecast/HowTO), [Forecast JSON](https://api.met.no/doc/ForecastJSON) | 공식 HOWTO가 Python requests+json을 제시. 전용 공식 Python SDK보다 일반 HTTP+JSON+캐시 구조를 재사용. 이번 historical/관측 목적의 단독 자료원으로는 맞지 않지만 예보 갱신 시각·집계구간 저장의 비교 사례로 유용. [HOWTO](https://api.met.no/doc/locationforecast/HowTO) |

## 시간·단위·누락에서 가져올 계약

- **Open-Meteo:** `timezone=GMT`와 시간별 `timeformat=unixtime`이면 UTC epoch seconds로 정규화하기 쉽다. 섭씨·mm를 명시하고 바람은 `wind_speed_unit=ms`로 통일 가능하다. 기온은 해당 시점, 강수는 **직전 1시간 합계**다. 반환 `hourly_units`, 요청 좌표와 반환 좌표, 모델 이름·조회시각을 저장해야 의미를 보존한다. [API parameter/Hourly Parameter Definition](https://open-meteo.com/en/docs/historical-weather-api)
- **Meteostat:** 기본 UTC·섭씨·mm·km/h·hPa다. 모델 보완 여부와 공급자 출처를 값과 함께 유지한다. `fetch(sources=True, fill=False)`가 출처와 원래 공백을 관찰하기 좋은 시작점이다. `fill=True`의 뜻은 **빠진 행 생성**이며 모델 값을 제외한다는 뜻이 아니다. 기본 `clean=True`는 부정확한 값을 제거하므로 원자료와 정제 후 자료를 구분해야 한다. [단위](https://dev.meteostat.net/formats), [fetch 사양](https://dev.meteostat.net/python/api/meteostat.TimeSeries.fetch), [실제 fetch 코드](https://github.com/meteostat/meteostat/blob/main/meteostat/api/timeseries.py)
- **ISD-Lite:** `-9999`는 NULL로 변환하되 먼저 판별한다. 온도·압력·풍속·강수의 스케일은 10이므로 유효값을 10으로 나눈다. 풍속은 m/s, 강수는 mm. 강수 `-1`은 trace이므로 음의 강수량으로 나누거나 단순 0으로 합치지 않는다. 1시간·6시간 강수 필드를 별도 보존해야 중복 합산을 막는다. [공식 format](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt)
- **MET Norway:** `updated_at`, 유효 UTC 시점, 집계구간과 `meta.units`를 저장한다. `next_1_hours` 강수는 **해당 시점부터 다음 1시간**으로 Open-Meteo와 방향이 반대다. 뒤쪽 자료에 없는 1시간 강수를 0으로 채우면 안 된다. [Forecast JSON, Forecast timeseries/Aggregation periods](https://api.met.no/doc/ForecastJSON)

위 저장 제안은 에이전트의 구현 판단이다. SQLite 테이블 모양·결측 정책은 메인이 실데이터 실험으로 검증하며 제품 UX 선택과 무관하다.

## 공식 라이브러리·코드 재사용의 현재 상태

| 재료 | 직접 확인 | 적용 비용·주의 |
|---|---|---|
| openmeteo-requests | PyPI 현재 1.7.5, 2026-01-19 공개, Python >=3.9, MIT. 저장소 README는 Client/AsyncClient와 FlatBuffers·Numpy/Pandas/Polars 사용례 제공. [PyPI](https://pypi.org/project/openmeteo-requests/), [README](https://github.com/open-meteo/python-requests) | 현재 main pyproject는 niquests>=3.15.2와 openmeteo-sdk>=1.22.0 의존성을 명시. `version=0.1.0`이라 배포 버전과 main 값이 다름; main 파일값을 설치 버전이라고 기록하지 않는다. [pyproject](https://github.com/open-meteo/python-requests/blob/main/pyproject.toml). 작은 JSON→SQLite 샘플에는 wrapper 없이 표준 HTTP도 충분하다는 판단. |
| meteostat | PyPI 2.1.4, 2026-03-21 공개; Python >=3.11,<4.0. 현재 main pyproject도 2.1.4·requests·Pandas>=2.3,<4·pytz를 명시. [PyPI](https://pypi.org/project/meteostat/), [pyproject](https://github.com/meteostat/meteostat/blob/main/pyproject.toml) | 현재 함수는 `ms.hourly(...)`이며 `providers`를 명시할 수 있음. 과거 `from meteostat import Hourly` 예제를 그대로 가져오지 않음. 공식 코드의 `fetch`는 데이터가 없으면 None 반환 가능하고 기본적으로 출처를 합치므로 빈자료·원천 유지 처리가 필요. [hourly](https://dev.meteostat.net/python/api/meteostat.hourly), [fetch 코드](https://github.com/meteostat/meteostat/blob/main/meteostat/api/timeseries.py) |
| 표준 HTTP+gzip+csv/고정폭+sqlite3 | 공급기관은 NOAA HTTPS 원자료를 권장하고 MET는 범용 HTTP+JSON 경로를 설명. [NOAA access](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database), [MET HOWTO](https://api.met.no/doc/locationforecast/HowTO) | 제3자 wrapper 버전 의존성을 줄이는 대신 스케일·sentinel·캐시·retry·metadata와 provenance 처리를 직접 구현. 성능 우월성이나 실제 실행 성공은 아직 주장하지 않음. |

## 실패·충돌·제외 기록

1. `dev.meteostat.net/python/` open은 Web 도구 Internal Error. trailing slash 없는 `/python` 공개 경로로 본문 확보; 서비스 전체 실패로 보지 않음.
2. 최초 검색에 나온 `fcic/meteostat-python`은 공식 소유자의 현재 저장소가 아니며 오래된 CC BY-NC 설명을 포함했다. 현재 `meteostat/meteostat` 저장소, 공식 license, PyPI로 출처를 교정했다. 과거 fork를 독립 공식 근거로 합산하지 않았다.
3. `ncei.noaa.gov/access-data`는 Web 도구 Internal Error. 제품 본문과 연결된 공개 WAF·Access Data Service 문서를 확보했다. WAF와 토큰 기반 CDO API를 구분한다. [무토큰 파라미터 예시가 있는 Access API 문서](https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation)는 별도 대안이지만 실제 API 호출은 이 역할에서 하지 않았다.
4. 추정한 Meteostat raw `meteostat/providers/isd_lite/hourly.py`는 Web 도구 Internal Error. 그 경로의 존재를 주장하지 않는다. 공식 API 문서의 Source Code 링크를 따라 실제 `meteostat/api/timeseries.py`를 확보했다.
5. NOAA의 일반 제품 본문은 현재까지 자료를 설명하지만 읽은 ISD-Lite 디렉터리에는 2025까지만 링크가 보였다. 최신일 필요하면 해당 station/year의 실다운로드로 판정해야 하며 2026 Lite 가용성을 단정하지 않는다.
6. ISD-Lite format/technical 문서만으로 시간대 UTC 표기를 직접 확보하지 못했다. 정시 반올림과 선택 창은 확인. NOAA를 채택할 경우 full ISD 시간 사양 또는 데이터 제공자 코드를 추가 확인해야 한다. 시간대 변환의 실검증은 메인의 실험 범위다.
7. NOAA 전체 국제 원천자료의 단일 글로벌 라이선스 및 WAF 수치 rate limit은 미확인이다. 현재 확보한 일반 저작권 안내보다 넓게 단정하지 않았다.
8. MET User-Agent에 가짜 주소·타인의 연락처를 넣어 호출하지 않았다. 공개 실제 프로젝트 식별자를 정하면 비개인 이메일 없이 사용할 가능성은 문서상 있지만 이번 연구를 위해 계정·연락처를 새로 만들 필요는 없다.

## 판단과 종료 근거

- **유지:** 관측 중심이면 NOAA ISD/ISD-Lite, 빠른 좌표·시간 모델 자료면 Open-Meteo, 관측소 탐색/공급자 결합을 재사용하려면 Meteostat.
- **보류:** MET Norway는 현재 범위에서 과거자료가 아닌 예보이며 식별자 부담이 있어 비교 사례로 남김. Meteostat JSON/RapidAPI 및 CDO 토큰 API는 무키·무계정 경로의 대체물이 아님.
- **비교 질문은 결론 가능:** 모델 HTTP, 혼합 관측소 라이브러리/CSV, 관측 원자료 파일, 예보 GeoJSON의 서로 다른 조건을 비교했고 공식 구현·정책·의미를 확인했다. 한 기관 소개글의 재인용을 여러 독립 원천으로 세지 않았다. 추가 서비스 목록 확대보다 선택된 경로의 실다운로드·형식·SQLite 검증이 다음 판단에 유용하다.
- **실행 판정은 별도:** 지역·기간 가용성, 결측 수, 실제 네트워크 응답·라이브러리 설치·SQLite 결과는 이 역할에서 미검증. NOAA 시간대 근거와 라이선스 세부는 채택시 후속 확인 필요.

기준 문서 후속 확인: 메인이 생성한 topology.md와 research/index.md의 R001/R002 역할·달성 조건은 위 비교 범위와 일치했다. 연결된 R001-public-access.md는 확인 시점에 아직 생성되지 않았으므로 부모 brief·Topology·index에 근거했다. 다른 연구 결과를 읽지 않았다.


## NOAA 최신성 정정 — 2026-09-08 후속 원문 확인

[2026-06-23 NESDIS/NCEI 공식 서비스 이전 공지](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly)의 본문을 직접 확인했다. ISD/ISD-Lite/ISD CSV는 **2025-08-24 이후 갱신이 없는 대체된 제품**이다. NCEI 자체 FTP/HTTPS 서비스의 계획 종료일은 **2026-07-31**이며, 기존 형식은 공지가 연결하는 NODD 경로로 접근하도록 안내한다. 최신 자료와 더 넓은 과거 범위에는 **GHCNh**를 권고한다.

따라서 앞에서 읽은 일반 ISD 제품 페이지의 “1901~현재”와 active station 갱신 설명을 현재 데이터 갱신 보장으로 채택하지 않는다. 새로운 구체적 이전 공지를 최신성 판단의 우선 근거로 삼는다. 과거 데이터 정규화 실험에 ISD-Lite를 유지할 수는 있지만, 최신 관측을 수집하는 재사용 재료의 기본 제공 경로로 권장하려면 GHCNh 사양·접근 실험이 필요하다. NCEI 디렉터리가 읽혔다는 사실은 서비스 종료 계획이 철회됐거나 최신 데이터가 추가됐다는 증거가 아니다. 직접 확인하지 않은 실제 종료 완료 여부는 단정하지 않는다.

이 정정은 대안 탐색자가 발견한 단서를 메인에게 전달받아 공식 원문을 독립 재확인한 것이다. 동일 공지는 독립 원천 하나이며 agent 수로 중복 합산하지 않는다.
