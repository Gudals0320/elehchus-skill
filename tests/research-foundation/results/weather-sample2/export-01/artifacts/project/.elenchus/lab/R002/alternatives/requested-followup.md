# 사용자 확정 서울 표본: 독립 후속 검증

확인일 2026-09-08 UTC. 사용자 지정은 서울 37.5665,126.9780, Asia/Seoul 기준 2026-09-01~02, 시간별 기온·강수 두 변수다. 원본 수집은 메인이 수행했으며 이 후속 작업은 읽기 전용 파싱, 공식 문서 확인, 별도 코드 사본 재현을 수행했다.

## 최근 자료의 의미와 수정 가능성

이 요청의 `models=era5`는 관측과 모델을 결합한 재분석 계열이다. 관측소의 원 측정값과 같다고 볼 수 없다. ERA5 시스템에는 분석과 짧은 모델 예측이 함께 있으며, 강수 같은 누적 변수는 모델 계산에서 나온다. 자료의 역사적 유효시각을 조회했다는 뜻으로 재분석으로 분류하고, 운영 시점에 발표된 예보와 구별한다. [ECMWF ERA5 data documentation, Introduction / The IFS and data assimilation](https://confluence.ecmwf.int/spaces/CKB/pages/76414402/ERA5+data+documentation).

최근 ERA5T는 약 5일 지연된 초기 자료이고 최종 ERA5는 약 2~3개월 뒤 제공된다. CDS는 해당 월 초기 자료를 약 2개월 뒤 최종 자료로 대체한다. 실제 보정으로 초기·최종 값이 달랐던 사례도 문서화돼 있으므로 이번 최근 과거 응답을 영구 불변의 최종 자료라고 설명하면 안 된다. [ECMWF의 제품 지연 표](https://confluence.ecmwf.int/spaces/GCR/pages/473842427/ECMWF+ERA5), [ERA5의 Data update frequency](https://confluence.ecmwf.int/spaces/CKB/pages/76414402/ERA5+data+documentation).

Open-Meteo도 ERA5를 0.25° 격자, 시간별, 약 5일 지연으로 명시한다. **추론:** 2026-09-08에 가져온 9월 1~2일 값은 후속 갱신 가능성이 있는 최근 재분석으로 취급하는 것이 타당하다. 실제 JSON에는 `expver`, revision, ERA5T 표지가 없으므로 정확한 upstream 버전은 이 응답만으로 직접 증명하지 못한다. 원본 bytes와 수집시각의 보존은 수집 당시의 결과를 재현하는 장치다. [Open-Meteo Historical API](https://open-meteo.com/en/docs/historical-weather-api).

검색 결과는 ECMWF 옛 페이지 버전으로 연결됐다. 그 페이지의 current-version 링크는 웹 도구 Internal Error가 났고, 공식 canonical display URL로 재접근해 2026-06-19 수정된 현재 본문을 확인했다. 옛 페이지를 최신 문서로 오인하지 않았다.

## 실제 응답 파싱

[독립 결과 JSON](requested-sample-verification.json), [파싱 코드](verify_requested_sample.py). 실제 원본 SHA256: `b416268fc89fd4feae86714a082ee1180bbf611712adb57704a5a3317ac3b3c1`.

| 항목 | 결과 |
|---|---|
| 요청 좌표 | 37.5665,126.9780 |
| 반환 격자 좌표 / elevation | 37.5,127.0 / 34 m |
| 현지 시각 | 2026-09-01 00:00 ~ 2026-09-02 23:00 (+09:00) |
| UTC 시각 | 2026-08-31 15:00 ~ 2026-09-02 14:00 (+00:00) |
| 시각 수·간격 | 고유 48개, 전 구간 3600초, 누락 시각 0 |
| 기온 | 48값, °C, NULL·비정상 0, 21.6~29.0 |
| 강수 | 48값, mm, NULL·비정상 0, 0~22.5 |
| 원본 보존 | 전후 SHA256 동일 |

강수는 각 시각 **직전 한 시간**의 양이다. 반환된 48시각의 합 `94.7 mm`는 8월 31일 23:00부터 9월 2일 23:00 KST까지 이어지는 구간들의 합이며, 9월 1~2일의 완전한 달력일 합계라고 이름 붙이지 않는다. 현지 날짜 전체 구간 합이 나중에 필요하면 마지막 9월 3일 00:00 종료시각 자료까지 포함하는 별도 선택이 필요하다. 이번 사용자는 시간별 값을 요청했으므로 현재 48시각 표본은 그 요청 범위를 충족한다. [Open-Meteo hourly parameter definition](https://open-meteo.com/en/docs/historical-weather-api).

## 수정 코드의 독립 사본 재현

`requested-reproduction/`에 최신 weather_path.py, reproduce.py, 새 fixture 한 쌍만 복사했다. 기존 R002 `.venv` Python 3.12.10과 tzdata를 사용해 별도 SQLite에 실행했다. [출력](requested-reproduction/output/reproduction.json)과 [검증 receipt](requested-reproduction/receipt.json)에 코드/자료 해시가 있다.

- 96 measurements = 48시각 × 2변수. 바람 변수 없음.
- 재입력 후 96행 및 imports 1개 유지.
- 모든 quality=valid, NULL=0.
- query 현지 첫/마지막 시각이 독립 원본 파싱과 일치.
- 요청 좌표와 반환 격자 좌표를 구별해 series metadata에 보존.
- 기온 mean=24.25 °C, 강수 `sum_available=94.7 mm`.

R002에서 재현:

```powershell
.\.venv\Scripts\python.exe -B .\alternatives\verify_requested_sample.py
.\.venv\Scripts\python.exe -B .\alternatives\requested-reproduction\reproduce.py --timezone Asia/Seoul --out .\alternatives\requested-reproduction\output-replay
```

코드 검토에서 request timezone은 UTC/GMT 또는 Asia/Seoul로 제한되고, epoch는 현지 날짜의 시작·다음날 시작을 UTC 순간으로 바꿔 범위를 잡는다. 응답 timezone/offset/unixtime, 요청된 변수만 처리하는 경로와 실제 서울 표본은 일치했다. 이번 후속 범위에서 추가 실행 결함은 발견하지 않았다.
