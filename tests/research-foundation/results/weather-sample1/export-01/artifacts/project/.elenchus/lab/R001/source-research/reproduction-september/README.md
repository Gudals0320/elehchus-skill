# Independent reproduction — September Seoul scope

- Inputs: byte-identical copies of 4 R002 source/requirements files and 10 required historical/September fixture JSON/meta files. No output DB or cache copied.
- Environment: reuses this agent's earlier independent venv at ../reproduction/lab/R002/.venv; does not use main R002/.venv. Pinned tzdata requirement remains 2026.3. No new dependency or weather-data network calls.
- Expected: 22 offline tests pass; replay_requested.py produces 3 snapshots of 48 rows, 48 Seoul hourly labels on September 1-2, unrequested wind stays NULL with not_requested quality, exact file replay creates no duplicate.
- Review: timestamp bounds, requested variable contract and snapshot policy; original code remains read-only, with hashes before/after. All outputs and imports are in this copied R002 except the explicitly reused dependency runtime.

## 결과와 검토 판정

재현 성공. 22개 테스트가 통과했고, replay_requested.py도 assertion 오류 없이 완료했다. 시각·요청 변수·반복 정책 검토 범위에서 수정이 필요한 결함은 발견하지 않았다. 원본 및 복제본 14개 파일은 전후 SHA-256이 모두 일치했다.

- 요청 날짜 서울 2026-09-01 00:00~2026-09-02 23:00: 48개 시간별 라벨. UTC epoch 1788188400~1788357600, 3,600초 간격. offset을 중복 적용하지 않았다.
- 요청은 기온·강수 두 변수. 선택된 snapshot에서 모두 48개 유효값이다. 풍속은 요청하지 않았으므로 DB의 세 snapshot 전체144행에서 NULL과 `not_requested:wind_speed_10m`으로 보존했고 missing_rows는0이다. 실제 요청된 풍속이 응답에서 빠지면 ingest가 metadata의 변수 집합과 대조해 거절하는 코드·회귀도 확인했다.
- 같은 요청의 두 SI 응답은 기상 배열이 같고 `generationtime_ms`만 다르다. raw bytes/SHA가 다르므로 별도 snapshot이라는 문서화된 정책대로 각48행이 생긴다. 같은 파일의 재입력은 inserted:false다. 새 imperial 응답까지 합해3개 dataset·144행이며 기존 snapshot을 덮어쓰지 않는다.
- 기온 평균24.25°C. 강수94.7mm는 선택된 시간 라벨의 **직전1시간 값 합**이다. 현지 날짜의 물리적 일 강수 총량으로 재명명하지 않는다.
- SI↔imperial 최대 변환 차이: 기온0.06666666666666288°C, 강수0.01159999999999961mm. 제공자별 반올림을 고려한 기존 허용오차 안이다.
- SQLite integrity_check=ok, foreign_key_check=[]이며 metadata의 날짜·timezone·요청변수와 보존 raw SHA도 재대조했다.
- 보존된 공개 응답으로 오프라인 기능을 검증했다. 이 agent는 새 weather GET이나 설치를 하지 않았으며 과거 독립venv를 재사용했다. 일반 네트워크 가용성이나 최신 서버의 지속 갱신을 이번 실행으로 추가 입증하지 않는다.

## 재실행

`reproduction-september/lab/R002`에서 PowerShell:

```powershell
$reproPython = '../../../reproduction/lab/R002/.venv/Scripts/python.exe'
& $reproPython -B -m unittest -v test_weather_pipeline
& $reproPython -B replay_requested.py
```

현재 결과를 보존한 파일:

- `test.log`: 22 tests/OK.
- `replay.log`: 요청 재현의 첫 실행 출력.
- `lab/R002/output/requested-run-summary.json`: 세 입력, 단위오차, DB 조회 결과.
- `lab/R002/output/requested-seoul-query.json`: 48행 조회 결과.
- `lab/R002/output/requested-weather.sqlite`: 세 snapshot.
- `review-summary.json`, `review.log`, `review_outputs.py`: 복제 코드 import 위치와 출력·DB·요청 metadata 교차검증.
- `input-manifest.json`, `input-after-manifest.json`: 원본/복제본14개 사전·사후 해시.
- `output-manifest.json`: 로그·summary·DB 해시.

이미 이 DB가 있는 상태에서 replay_requested.py를 다시 실행하면 세 ingestions도 inserted:false가 되는 것이 정상이다. 첫실행을 전제로 작성한 review_outputs.py는 이미 보존된 첫실행 summary를 교차검증하는 역할이므로 이를 일반 반복 실행 테스트로 해석하지 않는다. 처음부터 재현하려면 새 작업장으로 코드·JSON/meta와 requirements만 복제하여 빈 output으로 실행한다. 기존 DB를 지우는 명령은 제공하거나 실행하지 않았다.
