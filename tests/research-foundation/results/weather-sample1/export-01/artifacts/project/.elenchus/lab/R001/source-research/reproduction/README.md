# Independent offline reproduction

Question: Can the developer handoff run from only its copied code, requirements and preserved public samples?
Expectation: fresh environment; unittest 17/17; SI ingest 48 rows; same input inserted false; Asia/Seoul one-day query 24 rows and mean temperature 3.345833333333333 C.
Original code and data are read-only. Seven required files are copied with byte-identical SHA-256 values and preserved relative lab/R001,R002 layout. Tests put temporary writes below copied R002/test-output. Commands use -B; no source imports from the main work area. Only setup accesses public PyPI; data reproduction uses preserved samples offline.
Test pass is offline functionality evidence; it does not repeat or prove a new live weather API call. No original code changes will be made if failures appear.

## 결과

- 독립 venv: Python 3.12.10, SQLite 3.49.1, tzdata 2026.3. 메인 venv 재사용 없음.
- 새 venv 생성 후 일반 sandbox pip 설치는 `No matching distribution found`로 실패했다. 같은 고정 요구사항을 승인된 네트워크 접근으로 설치하자 성공했다. 상세 `setup.log`, `setup-escalated.log`.
- `test.log`: 17 tests / OK.
- `ingest-si.json`: 첫 SI 48행. `reingest-si.json`: inserted false, 48행.
- `ingest-imperial.json`: 별도 snapshot 48행. DB 합계 96행/2개 dataset, 자료종류 reanalysis.
- `query-seoul.json`: 한국시간 2024-01-02 00시부터 23시까지 24행, 평균기온 3.345833333333333 C. 강수 유효값 합 0.1 mm는 반환 시각 라벨의 직전 구간 합으로서 인계의 의미를 따른다.
- SQLite integrity_check=ok, foreign_key_check 문제 없음.
- `input-manifest.json`과 `input-after-manifest.json`: 원본 7개와 복제본의 사전/사후 SHA-256 일치. 메인 코드 수정이나 재현용 코드 패치 불필요.
- `summary.json`: 환경 경로·버전·입출력 핵심·해시의 기계 판독 결과.
- `verify_reproduction.py`: 저장된 출력/DB/복제본 해시를 오프라인으로 교차 확인한다.

## 실제 실행 명령

이 reproduction의 `lab/R002`에서 PowerShell 실행:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip --isolated install --index-url https://pypi.org/simple --cache-dir .pip-cache --timeout 10 --retries 0 -r requirements.txt
.venv/Scripts/python.exe -B -m unittest -v test_weather_pipeline
.venv/Scripts/python.exe -B weather_pipeline.py ingest --raw ../R001/samples/seoul-era5-si.json --db output/replay.sqlite
.venv/Scripts/python.exe -B weather_pipeline.py query --db output/replay.sqlite --dataset 7ec4d012ac07418d6d97db828de9754899b5fe638b69cc14854475bc713c1c50 --start 2024-01-02T00:00+09:00 --end 2024-01-03T00:00+09:00 --timezone Asia/Seoul
.venv/Scripts/python.exe -B weather_pipeline.py ingest --raw ../R001/samples/seoul-era5-si.json --db output/replay.sqlite
.venv/Scripts/python.exe -B weather_pipeline.py ingest --raw ../R001/adapter-samples/20260908T081157522643Z-cd887096aaff.json --db output/replay.sqlite
.venv/Scripts/python.exe -B ../../verify_reproduction.py
```

실행 로그 및 JSON 결과는 상위 reproduction 루트에 각각 보존했다. 마지막 검증 스크립트는 이미 저장된 해당 결과 파일을 읽는다. 네트워크 권한 상승은 dependency setup 한 번에 사용했고, 데이터 테스트·ingest·query는 일반 sandbox에서 복제 fixture만 읽었다. 배포할 때 `.venv`와 `.pip-cache`를 포함할 필요 없이 requirements로 재생성한다.
