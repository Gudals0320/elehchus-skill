**독립 재현 기록 — 공개 기상 데이터 → SQLite**

2026-09-08 09:22~09:27 UTC에 제공된 기능 재료를 새 실행 사본과 가상환경에서 재현했다. 주 회귀 **22개 모두 통과**, 보존 fixture 재생 **3개 dataset·144행**, 새 공개 Open-Meteo 수집→저장→조회 **48행 성공**이다. NOAA fixture 처리, 합성 실패 실험, pandas 비교, GHCNh prefix의 오프라인 파싱도 성공했다. 제품 코드를 수정할 필요는 없었다. 이 문서는 독립 검토자의 명령·관찰·한계 기록이며 전체 host trace가 아니다.

**읽은 시작 문서와 범위**

최초 지시는 이 작업 폴더의 `input.md`였다. 이어 `project/README.md`, `project/.elenchus/HANDOFF.md`, `project/.elenchus/topology.md`, `project/.elenchus/research/index.md`, Research R001·R002를 읽었다. 주 실행 코드·테스트·requirements·replay와 `alternative-research/README.md` 및 해당 실행 코드를 확인했다. `material-manifest.json`은 이 패키지에 실제 있는 파일의 해시를 대조하는 데 사용했다. 다른 대화, 원래 actor 작업장, 상위 평가 자료, 외부 실행 기록을 읽거나 참조 경로를 따라가지는 않았다.

`README.md`에는 연구 목적만 있고 실행 안내 링크가 없다. 숨김 파일을 포함한 파일 목록에서 `.elenchus/HANDOFF.md`를 찾아 실행 진입점을 확보했다. HANDOFF를 찾은 뒤에는 서울 좌표, 날짜, 변수, 시간대, 원본/metadata의 짝, 설치 및 주 실행 순서를 추가 사용자 답변 없이 알 수 있었다.

**환경과 원본 보존**

작업 루트는 `C:/Codex/Elenchus/tests/research-foundation/.work/weather-sample1-reproduction-clean`이다. 아래 경로는 이 루트를 기준으로 한다.

| 구분 | 실제 환경·처리 |
|---|---|
| OS / shell | Windows 11, `Windows-11-10.0.26200-SP0` / PowerShell |
| 기본 Python | `C:/Program Files/Python312/python.exe`, Python 3.12.10, AMD64 |
| SQLite | 3.49.1; STRICT를 요구하는 코드 실행 가능 |
| 주 실행 사본 M | `run/project/.elenchus/lab/R002` |
| 주 가상환경 | `M/.venv`, Python 3.12.10, pip 25.0.1, tzdata 2026.3. `sys.prefix != sys.base_prefix` 확인 |
| 선택 실험 폴더 A | `M/alternative-research` |
| 별도 선택 가상환경 | `A/.venv`, numpy 2.5.3, pandas 3.0.3, pypdf 6.8.0, python-dateutil 2.9.0.post0, six 1.17.0, tzdata 2026.3 |
| 설치 방법 | 제공된 두 requirements의 버전을 공개 PyPI에서 설치. 패키지 캐시는 각 실행 사본 아래에 지정. 기존 가상환경 재사용·시스템 패키지 설치 없음 |
| 원본 보존 | `project/` 52개 파일의 크기·SHA256 전후 일치. 추가·삭제·변경 모두 0개 |

원본 전체를 `run/project/`로 복사한 후, **사본의 기존 산출물만** `provided-output/`로 옮겼다. 주 `output/`와 NOAA DB를 새로 생성해 제공된 DB의 기존 행을 재현 성공으로 오해하지 않도록 했다. GHCNh의 `ghcnh-probe-results.json`은 결과 파일인 동시에 `--offline`의 입력 metadata이므로 실행 전에 보존 사본에서 원위치로 복사했다. 원본 `project/`와 제품 코드·입력 바이트에는 손대지 않았다. 실행 사본의 `.py`/`.txt` 15개도 원본과 해시가 같다.

주요 제품 파일의 보존 해시는 다음과 같다.

| 원본 파일 | bytes | SHA256 |
|---|---:|---|
| `project/README.md` | 125 | `41d7512f7506b4b0191b7ba61d94fa488cee97d66c2def128f40f644d7a71122` |
| `project/existing-product.txt` | 50 | `53f0c7f7a926d9252540a73f22338b37ab5d4323fdc4c68041a7ac7ad795fb71` |

**실제 명령과 종료 코드**

표의 M/A는 위 작업 디렉터리이며, 명령은 해당 디렉터리에서 실행한 자식 프로세스의 argv이다. `reproduction_runner.py`는 독립 검토용 보조 파일로, 실제 cwd·argv·UTC 시각·종료 코드·stdout/stderr를 `evidence/commands.jsonl` 및 `evidence/<label>.*.txt`에 저장했다. 아래 네트워크 권한 상승은 자동 승인으로 허용되었다.

| cwd | 실행 명령 | 종료 코드 / 관찰 |
|---|---|---|
| 작업 루트 | `python -B reproduction_runner.py prepare` | 0, 해시 목록과 새 실행 사본 생성 |
| M | `python -m venv .venv` | 0 |
| M | `.venv/Scripts/python.exe -m pip --isolated install --index-url https://pypi.org/simple --cache-dir .pip-cache -r requirements.txt` | 기본 sandbox 1: WinError 10013. 같은 명령의 네트워크 권한 상승 실행 0: tzdata 2026.3 설치 |
| M | `.venv/Scripts/python.exe -B -m unittest -v test_weather_pipeline` | 0, 22 tests / 0.199s / OK |
| M | `.venv/Scripts/python.exe -B replay_requested.py` | 0, 새 DB의 세 입력 모두 `inserted:true`; 같은 파일 재입력 `false` |
| M | `.venv/Scripts/python.exe -B weather_pipeline.py fetch --latitude 37.5665 --longitude 126.9780 --start 2026-09-01 --end 2026-09-02 --timezone Asia/Seoul --out ../R001/new-samples` | 기본 sandbox 1: 3회 WinError 10013. 같은 명령의 네트워크 권한 상승 실행 0: HTTP 200 |
| M | `.venv/Scripts/python.exe -B weather_pipeline.py ingest --raw ../R001/new-samples/20260908T092429641359Z-9ed6bff1463c.json --db output/live.sqlite` | 첫 실행 0, 48행·`inserted:true`; 마지막 동일 명령 재입력도 0, `inserted:false` |
| M | `.venv/Scripts/python.exe -B weather_pipeline.py query --db output/live.sqlite --dataset 8d2a00f39784559437e67c63c60b48fafc831d57d7fdd075acdf5a1373f12c43 --start 2026-09-01T00:00+09:00 --end 2026-09-03T00:00+09:00 --timezone Asia/Seoul` | 1, 검토자가 잘못 전달한 dataset ID를 `Unknown dataset id`로 거절 |
| M | `.venv/Scripts/python.exe -B weather_pipeline.py query --db output/live.sqlite --dataset 26f3e14a2e18fc0d853e51be6b44705eb7c0146d24e69f0874262a1aa59abeb7 --start 2026-09-01T00:00+09:00 --end 2026-09-03T00:00+09:00 --timezone Asia/Seoul` | 0, ingest가 반환한 실제 ID로 48행 조회 |
| A | `../.venv/Scripts/python.exe -B archive_sqlite.py` | 0, 빈 DB에서 NOAA 8,430행 저장·재입력·재연결 조회 |
| A | `../.venv/Scripts/python.exe -B failure_probes.py` | 0, 합성 반례 및 거절 확인 |
| A | `python -B -m venv .venv` | 0, 선택 실험용 새 환경 |
| A | `../.venv/Scripts/python.exe -B -c "from pathlib import Path; import shutil; shutil.copy2(Path('provided-output/ghcnh-probe-results.json'),Path('ghcnh-probe-results.json'))"` | 0, 사본에서 offline 입력 metadata 복원 |
| A | `../.venv/Scripts/python.exe -B ghcnh_probe.py --offline` | 0, 보존 prefix SHA 검사·완전한 63행 파싱 |
| A | `.venv/Scripts/python.exe -B -m pip --isolated install --disable-pip-version-check --no-compile --index-url https://pypi.org/simple --cache-dir pip-cache -r requirements-experiment.txt` | 네트워크 권한 상승 0, 고정 버전 6종 설치 |
| A | `.venv/Scripts/python.exe -B pandas_probe.py` | 0, NOAA 처리 결과 일치·잘못된 처리의 반례 재현 |
| 작업 루트 | `run/project/.elenchus/lab/R002/.venv/Scripts/python.exe -B review_reproduction.py` | 0, 환경·새 DB 무결성·실제 응답·fixture·사본 코드 해시 독립 확인 |
| 작업 루트 | `python -B reproduction_runner.py finish` | 0, 원본 52개 전후 완전 일치 |

검토 도구 자체의 시행착오도 있었다. 첫 `python -B reproduction_runner.py run main-pip-default run/project/.elenchus/lab/R002 .venv/Scripts/python.exe -m pip --isolated install --index-url https://pypi.org/simple --cache-dir .pip-cache -r requirements.txt` 호출은 종료 1 / WinError 2였다. Windows `subprocess`가 상대 실행파일 경로를 새 cwd 기준으로 찾지 못하여 **pip가 시작되기 전** 실패한 것이다. 독립 보조 runner에서 실행파일 경로를 절대경로로 해석하도록 고쳤으며 제품 파일은 바꾸지 않았다. 이 시작 실패는 runner의 명령 journal 생성 전이어서 여기 별도로 기록한다. 위 잘못된 dataset ID 입력도 검토자 실수이며, 자료나 제품의 결함으로 계산하지 않았다.

**저장 fixture로 재현한 결과 — 신규 네트워크 수집과 구분**

주 unittest와 `replay_requested.py`는 설치가 끝난 뒤 보존된 R001 JSON 및 `.meta.json`만 읽었다. 네트워크를 호출한 것으로 세지 않는다. 2026-09-01~02 서울 날짜의 SI·반복 SI·imperial fixture는 각각 48행이며 새 `requested-weather.sqlite`는 3개 dataset, 총 144행이다. 한 dataset을 지정한 조회는 48행이다. SQLite `integrity_check=ok`, `foreign_key_check=[]`였다.

| 관찰 항목 | 재현 결과 |
|---|---|
| 첫/마지막 서울 시각 라벨 | `2026-09-01T00:00:00+09:00` / `2026-09-02T23:00:00+09:00` |
| 유효 기온 / 강수 개수 | 각각 48개 |
| 평균 기온 | 24.25 °C |
| 선택 라벨의 직전 1시간 강수 유효 합 | 94.7 mm. 서울 두 달력일의 물리 구간 총강수량으로 해석하지 않음 |
| 같은 원본 재입력 | `inserted:false`, 행 증가 없음 |
| 보존된 SI 두 snapshot | 정규화 기상값은 같으나 raw hash/dataset은 다름 |
| SI / imperial 최대 변환 차이 | 기온 0.06666666666666288 °C, 강수 0.01159999999999961 mm |
| 요청하지 않은 풍속 | SQL NULL + `not_requested:wind_speed_10m`; 주 입력의 missing row 0 |

22개 회귀는 원본 왕복·재입력, NULL/0, 전체 강수 결측, 내부 시각 누락, 빈 배열, 단위·배열·숫자·음수 오류의 DB 불변성, 중복 시각, 비표준 JSON 숫자, 원본 hash 손상, 서울 날짜, DST 반복 시각, 명시 offset, STRICT, 가장자리 부족, HTTP 재시도, 두 변수 요청/반환 계약 등을 확인했다. 빈 응답·NULL·DST·429/400 재시도는 **합성 테스트**이다. 이번 공개 API에 이 상태들을 실제 유발한 것은 아니다.

NOAA는 보존된 94,995-byte gzip을 새 DB에 넣었다. 입력 SHA256은 `2619321a2fbaf7a472757b9de2b4d777d3c0b2a89d5ee4886a4dd2b5f886c220`. `db_rows_before=0`, 첫 입력/재입력 모두 8,430행, 첫 48시간 조회 48행, 연간 시각행 누락 354, 풍속 결측 36, 강수 missing 7,824 / trace 130 / measured 476이었다. NULL·trace·실제 0을 분리하는 결과가 재현되었다.

NOAA 합성 실패 실험에서는 nullable 복합 PK 중복 2행, 일반 REAL의 문자열 `NA`와 오염된 평균 0.0, STRICT 및 NOT NULL의 입력 거절, mixed-offset 문자열 정렬 오류, 기본 timestamp converter의 tzinfo 소실을 확인했다. pandas 3.0.3은 동일 원본의 8,430행 및 결측/trace 수와 일치했다. 단순 강수 /10의 trace=-0.1 오류, 자동 `to_sql` 중복 2행과 외부 rollback 뒤 잔존 1행, mixed-offset 및 epoch 단위 착오도 문서대로 재현되었다.

GHCNh는 보존한 65,536-byte prefix만 파싱했다. SHA256 `0ac539ecb8180585ea6c107b5d468f3e64bf5f7b32d13949da3fcfd1b895b0b4`, 완전한 63행 중 분 값이 00이 아닌 행 60개, 온도 결측 1개, 강수 결측 51개였다. 출력의 HTTP 206/Content-Range는 **입력 metadata에서 이어받은 과거 정보**이며 이번 검토의 신규 GET 결과가 아니다. NOAA/GHCNh의 신규 네트워크 수집과 전체 GHCNh 어댑터는 실행하지 않았다.

**이번에 실행한 공개 네트워크 경로**

PyPI 설치와 Open-Meteo GET을 실제 실행했다. 기본 sandbox에서는 WinError 10013으로 차단되었다. pip의 최종 메시지에 `No matching distribution`이 포함되지만 그 앞의 원인은 접속 실패였다. 권한 상승 후 같은 고정 버전 설치가 성공했으므로 버전 부재로 판단하지 않았다. API 기본 sandbox 호출 역시 세 번 실패 기록이 있고, 권한 상승 후 HTTP 200을 새 원본·metadata·fetch-events로 보존했다. 인증·비밀키·TLS 검증·시스템 설정을 변경하지 않았다.

- 요청: 위도 37.5665, 경도 126.9780, ERA5, 시간별 기온·강수, 서울 현지 날짜 2026-09-01~02, `timeformat=unixtime`.
- 수집 metadata 시각: `2026-09-08T09:24:28.457413+00:00`; 파일 생성 완료 약 09:24:29 UTC.
- 새 원본: `run/project/.elenchus/lab/R001/new-samples/20260908T092429641359Z-9ed6bff1463c.json`, **1,322 bytes**.
- 새 원본 SHA256: `9ed6bff1463caa178287706287077391b4b23130d2118e099f0325917baa2eb1`.
- 실제 반환 격자: 37.5 / 127.0. 요청 좌표와 구분된다.
- 신규 live dataset: `26f3e14a2e18fc0d853e51be6b44705eb7c0146d24e69f0874262a1aa59abeb7`.
- 새 `output/live.sqlite`: 1개 dataset·48행, 재입력 뒤에도 그대로. 무결성 `ok`, 외래키 오류 없음.
- 서울 조회: fixture와 같은 처음/마지막 라벨, 48개 유효 기온/강수, 평균 24.25 °C, 선택 강수 라벨 합 94.7 mm.
- 새 raw byte/hash는 보존 SI fixture와 다르지만 정규화 기상 배열은 같다. 날짜 대체를 사용하지 않았다. 이번 원격 응답의 성공을 장래 값 불변이나 ERA5 최종판 확정으로 확대하지 않는다.

**설명만으로 해결되지 않는 부분과 재사용 범위**

주 실행은 충분히 자립적이다. 다만 다음 사항은 파일 목록·코드 확인이나 실제 실행에서 드러났다.

1. 패키지의 manifest는 118개 항목을 열거하지만 실제 일치 파일은 49개, 없는 참조는 69개였다. 존재하는 manifest 대상의 hash/size 불일치는 0개다. 제공된 전체 52개 중 README·제품 sentinel·manifest 자체가 나머지다. 누락 항목에는 과거 독립 재현 폴더, verification 결과, 실행 로그, 일부 참고 PDF/HTML이 있다. 이들을 읽거나 확보하려고 제공 범위를 벗어나지 않았고 주 기능 재현에도 필요하지 않았다. 상세 목록은 `evidence/preparation.json`에 있다.
2. `verify_materials.py`는 코드상 `project/` 바깥 `records/original-hashes.json`과 그 안의 기록된 원래 절대경로에 의존하며 외부 activity 기록도 쓴다. 제공된 재료만으로 실행하는 범용 검증 진입점이 아니다. **실행하지 않았으며** 성공했다고 보고하지 않는다. 대신 제공된 NOAA 실행 코드 자체를 사본에서 실행하고 이번 원본 52개를 독립적으로 해시 검사했다.
3. replay의 출력 DB 경로는 고정이다. 패키지의 기존 DB를 그대로 두면 첫 재생부터 `inserted:false`가 될 수 있다. 새 삽입 검증을 위해 사본의 기존 출력만 보관 위치로 옮겼다. GHCNh 결과 JSON의 입력 metadata 역할도 코드에서 확인해 함께 유지했다.
4. Windows에서는 가상환경 tzdata 설치 및 공개 네트워크 권한이 필요했다. 두 사실은 문서의 환경 주의와 부합한다. 검토용 runner의 상대경로 해석과 잘못 전달한 ID는 별개의 검토자 시행착오로 위에 기록했다.

재사용 가능한 것은 문서에 정한 작은 ERA5 좌표/기간의 공개 수집·원본 보존·정규화·SQLite 저장/조회 경로와 회귀 fixture, 고정 NOAA 2024 입력의 처리 예시, pandas/SQL의 구체적 실패 실험이다. 시간은 UTC epoch로 저장하고 조회의 명시 offset/IANA zone, NULL/0/미요청 변수, dataset 단위 snapshot 정책, 직전 1시간 강수 구간 의미를 유지해야 한다. 모델 재분석을 관측소 실측으로 바꾸어 표기할 근거는 없다.

GHCNh 최신 전체 어댑터, Meteostat 실제 연결, 별도 관측소 좌표 확인, 대규모 성능·동시 쓰기·지속 수집, 물리적 달력일 강수 집계, 자동 보간, 제품 UX, 데이터 정확도는 이번 실행으로 검증하지 않았다. API/데이터 사용 조건은 제공된 HANDOFF와 Research에 기술된 구분을 인계받았으며 이번 재현에서 법적 조건을 새로 조사·확정하지 않았다. 필수 사용자 질문은 없다.

검토자가 추가한 파일은 `reproduction_runner.py`, `review_reproduction.py`, 이 문서, `evidence/` 및 `run/`이다. 제품 구현 보완은 0개이며 성공을 위해 원래 자료를 고친 부분도 없다. 핵심 증거는 `evidence/commands.jsonl`, `evidence/main-tests.stderr.txt`, `evidence/review-summary.json`, `evidence/preservation.json`과 새 실행 사본의 raw/meta/SQLite 산출물이다.
