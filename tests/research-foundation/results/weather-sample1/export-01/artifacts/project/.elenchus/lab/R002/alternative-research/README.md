# 공개 관측 아카이브 대안 연구

소유 범위: 이 디렉터리만. 다른 agent 파일·원본 skill 수정 없음. 최초 release 확인은 메인 결과(up_to_date)를 재사용했다. Research, Discovery, Web Evidence Loop, Lab 지침을 읽었다. 시작 시 topology/index는 아직 존재하지 않아 메인이 전달한 중립 brief로 진행한다.

질문: 인증 없는 공개 파일 다운로드가 공개 기상 데이터→시간·단위·결측 정리→SQLite 저장·조회에 실용적인 대안인가? 표준 라이브러리와 dataframe/전용 클라이언트의 선택 조건은 무엇인가?

실험 계획: NOAA ISD-Lite의 한 관측소·2024년 압축 파일을 작은 독립 입력으로 다운로드하고 원본 해시/출처를 보존한다. UTC 시각, 정수 배율, -9999 결측 및 -1 미량강수를 구분하여 SQLite로 넣고 같은 입력 재실행, 범위 조회, 실제 결측과 시간 구멍을 확인한다. 보조 실험으로 SQLite의 유연한 타입/NULL 키/비교, UTC 오프셋 보존 실패를 재현한다. 실패를 주입한 경우 실제 자료 오류와 구분한다.

기본 수집·SQLite 실험은 Python 3.12 표준 라이브러리만 사용하며 `-B`로 bytecode 쓰기를 막는다. 추가 dataframe 비교와 PDF 본문 추출에만 소유 폴더의 `.venv`에 pandas/pypdf를 설치했다. 모든 다운로드·DB·로그·패키지 캐시는 이 디렉터리에 둔다. 네트워크 읽기만 하고 키·계정·개인정보·유료서비스를 쓰지 않는다. 아직 측정하지 않은 처리량·정확성은 주장하지 않는다.

## 확보한 재료와 재현

기본 관측 수집·저장 재료는 표준 라이브러리만 필요하다. 이 폴더에서 다음을 실행한다.

```powershell
python -B archive_sqlite.py
python -B failure_probes.py
```

원본 `471080-99999-2024.gz`를 함께 제공하므로 위 실행은 네트워크가 필요 없다. `archive_sqlite.py`는 고정 fixture 해시를 검사하고 `observations.sqlite3`에 넣은 뒤 읽기 전용으로 다시 열어 조회한다. 출력은 `archive-results.json`, `query-48h.json`, `failure-results.json`이며 세부 실행 기록은 `activity.jsonl`이다. 실제 다운로드 재현 명령은 아래와 같으며 원본 파일이 이미 있으면 덮어쓰기를 거부한다. 새 다운로드는 다른 파일명을 쓰고 달라진 해시를 먼저 검토한다.

```powershell
python -B fetch_probe.py 'https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/2024/471080-99999-2024.gz' 'new-471080-2024.gz'
```

dataframe 비교는 선택적인 별도 가상환경이다. 현재 실험 버전은 `requirements-experiment.txt`와 `pip-install.log`에 고정되었다. 가상환경/패키지 캐시는 코드 재사용의 필수 인계 파일이 아니다.

```powershell
python -B -m venv .venv
New-Item -ItemType Directory -Force -Path 'tmp','pip-cache' | Out-Null
$env:TEMP = (Join-Path (Get-Location) 'tmp')
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = (Join-Path (Get-Location) 'pip-cache')
.venv/Scripts/python.exe -B -m pip install --disable-pip-version-check --no-compile -r requirements-experiment.txt
.venv/Scripts/python.exe -B pandas_probe.py
```

`ghcnh_probe.py`는 공식 문서의 예시 PSV에서 64KB만 다운로드한다. 완전한 관측 파일이 아니라 일부 관측행/헤더 확인용이다. 기존 prefix가 있으면 덮어쓰기를 거부한다. 보존한 입력의 파싱은 `python -B ghcnh_probe.py --offline`으로 재현한다. `ghcnh-probe-results.json`에 요청 Range, 응답 Content-Range, 해시, 필드와 관측값을 보존했다. PDF 원문 `ghcnh_DOCUMENTATION.pdf`와 추출 본문 `ghcnh-documentation-extracted.txt`는 신규 포맷 검증 근거다.

## 실제 결과

- Python 3.12.10, SQLite 3.49.1. ISD-Lite 94,995 bytes를 실제 공개 GET으로 받았다. 원본 SHA256: `2619321a2fbaf7a472757b9de2b4d777d3c0b2a89d5ee4886a4dd2b5f886c220`.
- 관측소 ID 471080-99999의 2024년 파일은 8,430행이다. UTC 윤년 기대 8,784시간 중 행 자체 누락은 354시간이다. 이 파일만으로 관측소의 위치 메타데이터는 검증하지 않았다.
- 온도 8,430개 유효, 풍속 36개 결측. 1시간 강수는 missing 7,824개, trace 130개, measured 476개다. 누락은 0으로 대체하지 않았다. 미량강수는 정확한 수치 미보고로 NULL+trace, 실제 0mm는 0+measured로 나눈다.
- /10 후 첫 온도 0.6°C, 풍속 1.5m/s. UTC epoch 초로 저장했다. 재입력 전후 모두 8,430행, 읽기 전용 재연결에서 최초48시간 범위조회48행, 원본 해시 불변을 확인했다.
- 합성 실패 실험: 일반 SQLite REAL 컬럼에 `'NA'`가 들어가 AVG 결과가 0.0으로 오염됨; nullable 복합 PK에 같은 NULL 키가 2행 들어감; mixed-offset 문자열 정렬과 시간순서가 다름; Python 기본 timestamp converter가 UTC tzinfo를 없앰. STRICT+NOT NULL은 앞 두 입력을 거부했다. malformed 숫자와 hour24는 파서가 거부했다.
- pandas 3.0.3에서 같은 파일 행/결측/trace 개수는 표준 라이브러리와 일치했다. `na_values=[-9999]`만 지정하고 모든 강수를 /10하면 미량강수가 -0.1mm가 됐다. `to_sql` 자동 스키마에는 PK가 없어 동일 입력 append 두 번으로2행이 되었고, sqlite3.Connection을 넘긴 `to_sql` 뒤 외부 rollback을 해도1행이 남았다. mixed-offset 파싱은 기본값에서 오류, `utc=True`로 서로 다른 두 UTC시각이 보존됐다. epoch 밀리초에 `unit='ms'`를 생략하면1970년으로 오해했다.
- GHCNh 공식 v1.1.0(2026-03-10) 문서의 예시 USW00003812/2023 공개 PSV에 Range GET206 성공. 전체12,346,435 bytes 중65,536 bytes만 보존, 완전63행/329필드 중60행이 분00이 아니다. 첫 온도는 이미 `10.0`°C, 결측강수는 빈칸이었다. 첫 ID 헤더는 문서의 개념 이름 Station_ID가 아니라 실제 `STATION`이다. 이전 ISD /10·정시 가정을 이 포맷에 복사하면 오류가 난다.

## 접근 비교와 공식 본문

| 접근 | 확인한 직접 근거 | 적용 판단·실패 조건 |
|---|---|---|
| 관측소·연도 ISD-Lite gzip 고정폭 파일 | [형식](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt)의 배율·결측·trace, [기술문서](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-technical-document.txt)의 시간창·정시 반올림·QC 제거, [ISD 원문](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf) p5 UTC. 실제 파일 전체 실험 성공 | 작은 역사 관측 파일은 stdlib gzip/int/datetime/sqlite로 충분. QC 플래그/정확한 관측분은 Lite에 없고 요소별 최대10분 차이가 가능하여 정밀 동시 비교나 관측밀도 연구의 대체가 아니다. |
| GHCNh PSV/Parquet 관측 아카이브 | [공식 개요](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly), [v1.1.0 문서](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf) I·III·IV·V·VI·IX, [메타데이터](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC01688). 실제 PSV prefix GET 및 헤더/행 확인 | 현재 NOAA가 권장하는 ISD 후속 자료. station/year PSV는 csv delimiter='|'로도 읽을 수 있다. UTC지만 분 단위 행, 소수 단위, 변수별 measurement/QC/source 필드, 다중 강수 누적시간을 보존할 별도 어댑터가 필요. 실제 prefix에는 missing1개 온도, missing51개 강수가 있었다. 전 지역·전체 파일·최신 관측 지연은 미검증. |
| Meteostat time-series/bulk/전용 Python client | [Data Access](https://dev.meteostat.net/data), [현재 hourly bulk](https://dev.meteostat.net/data/bulk/hourly), [형식/단위](https://dev.meteostat.net/formats), [Python](https://dev.meteostat.net/python), [데이터 라이선스](https://dev.meteostat.net/license) 실제 본문 | 관측소/연도 단위 time-series CSV.gz와 연도별 전체 bulk Parquet는 현재 공존하는 별도 경로다. Parquet가 station CSV를 대체했다는 뜻이 아니다. bulk는 beta이고 모델로 관측 누락을 대체한 자료를 포함한다. 변수별 `_source`가 있고 좌표는 관측소DB join이 필요하다. 재배포 데이터 CC BY4.0·Meteostat 및 공급자 attribution 필요. Python 직접 공급자 접근은 공급자 조건도 확인해야 한다. 풍속 km/h이므로 ISD/GHCNh m/s와 그대로 합치면 오류. 클라이언트/CSV/Parquet 실제 다운로드는 수행하지 않아 동작 성공으로 계산하지 않는다. NOAA 등 재사용이므로 별도 독립 관측원으로 세지 않는다. |
| stdlib 변환 + 명시 SQL | [Python sqlite](https://docs.python.org/3.12/library/sqlite3.html#default-adapters-and-converters-deprecated), [SQLite 타입](https://www.sqlite.org/datatype3.html), [SQLite quirks](https://www.sqlite.org/quirks.html) 본문과 본 실험 | 의존성 없는 작은 수집·검증 경로에 적합. UTC epoch와 단위가 이름에 있는 컬럼, NULL+별도 상태, 명시적 트랜잭션·PK·STRICT·바인딩이 필요. 많은 컬럼/집계·보간·Parquet는 직접 코드 비용이 커짐. |
| pandas 변환 + 별도 저장 계약 | [read_csv](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html), [to_datetime](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.to_datetime.html), [to_sql](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html) 본문과3.0.3 실험 | 읽기·필터·시간별 재색인·집계에는 유용. 의존성과 명시 dtype/NA/UTC/unit 결정은 여전히 필요. 저장은 미리 만든 스키마·중복키·트랜잭션 정책을 적용해야 하며 to_sql을 멱등·원자 수집 계약으로 오해하면 안 된다. 성능 우열은 측정하지 않았다. |

## 실제 실패와 접근 갱신

1. 일반 sandbox Python 공개 GET은 WinError10013으로 실패했다. 같은 공개 읽기를 권한 상승하여 NOAA 원본/공지/PDF/PSV prefix 다운로드에 성공했다. 인증이나 유료서비스를 사용하지 않았다.
2. NOAA 서비스 이전 공지는 web 도구에서 timeout으로 본문 확보 실패했지만 공개 urllib GET으로 본문을 받았다(`noaa-service-change.html`:2210). [2026-06-23 공지](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly)는 ISD가2025-08-24 이후 갱신되지 않으며 기존 HTTPS/FTP 예정 종료일2026-07-31, NODD 이전 및 GHCNh 사용 권장을 명시한다. 오늘 기존 파일 GET 성공을 향후 유지 보장으로 해석하지 않는다.
3. 공지의 NODD ISD-Lite 디렉터리를 바탕으로 구성한 `https://noaa-isd-pds.s3.amazonaws.com/isd-lite/2024/471080-99999-2024.gz`는404였다. 이 구성 경로는 재현 가능한 대체 다운로드로 채택하지 않았다. 기존 과거 fixture는 보존했고 최신 후속 GHCNh의 공식 예시를 직접 검증했다. 모든 NODD 파일이 없다고 일반화하지 않는다.
4. GHCNh PDF와 관측소목록은 web 도구에서 application/octet-stream 미지원이었다. PDF는 urllib로 받아 pypdf6.8.0으로 추출했다. Windows cp949 stdout에서 UnicodeEncodeError가 났지만 추출 파일 저장은 완료되었으며 UTF-8/PowerShell 읽기로 본문을 확인했다. station list는 다운로드하지 않아 station mapping을 검증했다고 하지 않는다.
5. Meteostat `/python/`는404였으며 현재 `/python`에서 본문을 확보했다. bulk Parquet만 보고 station CSV가 대체되었다고 추론했던 중간 판단은 메인의 반증과 `/data` 공식 본문으로 수정했다. station/year time-series CSV.gz와 bulk Parquet가 현재 공존한다. 전용 클라이언트의 과거 `Hourly` 예제를 현재 계약으로 단정하지 않았다.

## 판정·남은 범위

대안 탐색과 이 실험 범위는 결론 가능하다. 과거 관측 gzip과 현재 GHCNh PSV, 집계·보간을 제공하는 전용 클라이언트 및 dataframe 처리를 비교했다. 핵심 차이는 요청 문법보다 데이터 의미(관측/모델, 정시/관측분, missing/trace, 단위/QC)다. 기능은 stdlib ISD-Lite 전체 입력의 저장·조회만 검증 완료했고 GHCNh는64KB 접근·형식 검증까지다. GHCNh 전용 생산 어댑터, Meteostat 실제 수집, 대규모 성능 및 최신 갱신 지연은 남아 있다. 메인의 현재 end-to-end 목표를 바꾸기 위한 필수 사용자 질문은 없다.

다음 탐색은 이번 작은 수집·저장 재료의 선택을 크게 바꾸기 어렵다. 이후 제작자가 최신 지점 관측·많은 관측소·보간·Parquet를 요구할 때 해당 어댑터/데이터프레임으로 확장하면 된다. 본 함수/스키마는 재사용 예시이며 종합 UX나 최종 제품 구조를 고정하지 않는다.
