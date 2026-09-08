# R001: 무인증 공개 기상 데이터를 어떤 경로로 확보하는가?

- 상태: 확정
- 기준/영향: [Topology](../topology.md)의 실제 데이터·출처·접근 제약 목표
- 확인 환경: 2026-09-08 UTC, Windows/Python 3.12.10. 원문 확인과 실제 HTTP 수집을 구분.

## 후속 사용자 확정 범위와 현재 결과

서울 좌표 **37.5665,126.9780**, 시간별 기온/강수, 우선 **2026-09-01~02**로 범위를 갱신했다. 날짜를 Asia/Seoul 시민 날짜로 해석해 실제 ERA5 endpoint에 요청했고 **HTTP 200, 1,322 bytes, 48시간/96값, NULL 0**을 받았다. 다른 날짜로 fallback할 필요가 없었다. 요청 좌표와 반환 **37.5,127.0, 고도34m**를 구분했다. [원본](../lab/R002/fixtures/seoul-requested-20260901.json)과 metadata, [현재 실행 안내](../lab/R002/README.md)를 기준으로 재현한다. 아래 2025년 표본은 초기 조사·단위 비교 기록이다.

현재 자료는 관측을 동화한 **재분석**이다. 최근 날짜를 영구 고정된 최종 데이터라고 부를 수는 없다. 메인과 독립 조사자가 [ECMWF ERA5 문서의 Data update frequency](https://confluence.ecmwf.int/spaces/CKB/pages/76414402/ERA5+data+documentation)를 읽어 ERA5T 약5일 지연과 약두달 후 최종본 대체·실제 수정사례를 확인했다. JSON에 upstream expver/revision 표지가 없으므로 정확한 ERA5T 버전은 미확인. 이번 최근 응답을 잠정 자료로 취급하고 저장한 bytes를 고정 재현하는 것이 타당하다는 추론이다. 이는 요청 기간 접근 실패나 날짜 대체가 아니다. 관측소 직접 측정값/운영 예보 제품으로 해석하지 않는다. [독립 후속 확인](../lab/R002/alternatives/requested-followup.md).

## 질문과 판정 기준

계정·키·결제 없이 쓸 수 있는 제공 방식의 차이를 발견하고, 작은 실제 응답을 확보한다. 단순 무료 API 목록이 아니라 모델/관측, 시간 구간·단위·품질 의미, 재사용 계약과 운영 실패를 비교한다. 공개 API와 정적 파일, 통합 라이브러리의 차이가 선택을 설명하고 실제 bytes+요청+시각+hash를 남기면 대표 수집 목표를 달성한다. 모든 공급자의 어댑터를 구현하는 연구는 아니다.

## 접근 비교와 직접 근거

| 접근 | 확인된 차이·비용 | 현재 판단 |
|---|---|---|
| Open-Meteo JSON archive | [공식 API](https://open-meteo.com/en/docs/historical-weather-api)의 ERA5 재분석 격자 자료. 요청·반환 좌표 차이와 단위 메타데이터를 보존해야 한다. 작은 JSON은 표준 Python으로 충분 | 이번 대표 경로 채택. Best Match 혼합 대신 ERA5를 명시한 것은 재현을 위한 임시 연구 선택 |
| DWD 관측소 ZIP→세미콜론 CSV | [v24.03 명세](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/DESCRIPTION_obsgermany_climate_hourly_air_temperature_en.pdf): 독일 관측, QC 정보, recent/historical 기간 중복·수정 정책 | 실제 관측용 유력 대안. 원문 재확인했으며 ZIP 수집·어댑터는 미실행 |
| NOAA GHCNh PSV/Parquet | [공식 제품](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly): ISD 후속, 육상 관측소, QC 유지, bulk 권장 | 과거 ISD endpoint를 최신 수집 기본값으로 쓰지 않음. 파일 header/국내 관측소/파싱은 미검증 |
| NASA POWER JSON/CSV/NetCDF | [Hourly API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/): 기본 LST는 시민 시간대와 다름, UTC 옵션 필요, 시평균과 강수 mm/hour, 최대 15변수 | 모델 API의 다른 접근. Open-Meteo의 직전시간 강수 합과 섞을 때 별도 의미 변환 필요. 실제 호출 미실행 |
| Meteostat, Wetterdienst, 전용 SDK | 데이터 공급자 통합, 품질·단위/배열·대량 처리 재사용 가능. 단 의존성·버전과 모델 보충 조건이 추가됨 | [독립 공급 조사](../lab/R001/provider-discovery.md)에 코드·계약·실패 비교. 작은 경로에서는 직접 JSON 처리 채택 |

Open-Meteo [무료 이용약관](https://open-meteo.com/en/terms)은 비상업용이고 분/시/일 호출량을 제한한다. 데이터 CC BY 4.0과 무료 endpoint의 이용 허용 범위는 별개다. 이 연구는 몇 회의 공개 연구 조회만 수행했고 미래 상업용 운영의 무키 무료 접근을 확정하지 않았다. Meteostat의 [license](https://dev.meteostat.net/license)와 [FAQ](https://dev.meteostat.net/faq.html)의 다른 라이선스 문구도 메인이 다시 열어 확인했으며 선택 근거로 단순화하지 않았다.

## 실제 수집·실패·후속 실험

1. 일반 sandbox에서 Release 조회 및 첫 데이터 요청 모두 WinError 10013. Release 지침의 1회 재시도와 사용자 승인 범위인 데이터 수집을 네트워크 허용 실행으로 재시도하여 성공했다. HTTP 서비스 오류와 host 권한 오류를 구분한다.
2. `lab/R001/probe_access.py`로 서울 요청 좌표 37.57,126.98, ERA5, UTC unix seconds, 2025-01-01~03 기온/강수/풍속을 수집: **HTTP 200, 2,134 bytes, 72시간**, SHA256 `a8cc853f5c2ef64618cf2eaf05e61a6135dd023efe89fa8717585c1c95e1031f`. 반환 격자 37.5,127.0, 고도 37m. 기록은 [원본 및 시도 metadata](../lab/R001/responses/).
3. 같은 공급자로 2025-07-16~18 Fahrenheit/mph/inch 응답 수집: **HTTP 200, 2,221 bytes, 72시간**, SHA256 `a2763cedd57330897589aeee15725f2da2bf63c690436797193b055bc7825517`. 여름 강수 값이 있어 0만으로 변환을 검증하는 한계를 보완했다.
4. R002의 최종 기능 진입점 `weather_path.py fetch ... --db ...`로 같은 여름 날짜 metric 데이터를 다시 수집하여 실제 수집→정규화→SQLite까지 연결했다. [live 원본/metadata](../lab/R002/output/live/)와 [단위 비교](../lab/R002/output/unit-comparison.json)에서 metric 합 190.3mm와 imperial 환산 190.2968mm의 차이를 확인했다. API 출력 반올림/독립 요청 차이지 기상 정확도 검증이 아니다.

## 역할·탐색 종료

무이력 provider_discovery는 제공 방식·기존 구현을, processing_discovery는 처리 대안·실패를 독립 조사했다. 슬롯에 맞춰 순차 실행했고 역할별 파일 소유권을 나눴다. 이는 작업 규칙이며 기술적 파일 격리가 아니다. 메인은 후보 원문과 결정적 결과를 재확인하고 통합했다. 1차 공급 조사 후 API 구현을 임시 시작했으며 최종 선택은 처리 대안/실행 반증까지 반영했다.

직접 API·정적 관측 파일·통합 라이브러리, 시간 의미·사용조건·최신 서비스 전환의 차이를 살폈다. GHCNh PDF 도구 미지원과 JS shell 접근 실패는 agent의 공개 metadata/제품 대안으로 범위를 확인했으나 파싱 가능성까지 확정하지 않았다. 현재 목표에서 공급자 소개 링크를 더 늘리는 것보다 확보한 대표 경로의 처리 정확성 검증이 판단에 더 중요하므로 그 검증을 R002에서 수행했다. 전체 대안 실구현을 완료로 세지 않았다.

## 재료와 결론

[R002 실행 안내](../lab/R002/README.md)가 실제 코드·fixture·테스트·재실행 명령을 제공한다. 출처/단위 원본을 보존했으며 사용자 원본 project 파일을 수정하지 않았다. 장기 운영 SLA, 실제 관측 어댑터 및 전체 제품은 후속 제작자의 선택이다.

**판정: 결론 가능.** 무인증 공급 방식 비교와 실제 대표 수집 목표 달성. 외부 공급자 전체 수집 성공이나 관측소 정확성으로 확대하지 않는다.
