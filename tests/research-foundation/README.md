# Research Foundation 평가

beta.2의 Topology와 실전적 Research를 실제 웹·독립 agent·코드 실행이 있는 새 컨텍스트에서 네 번 평가하기 위한 입력과 기록 도구다. **이 폴더를 준비하거나 Python 테스트를 실행한 것만으로 실제 평가가 완료되지는 않는다.** 실제 결과는 실행 후 별도 `results/`에 추가한다. 과거 `tests/research-discovery/`의 자료를 수정하거나 다시 채점하지 않는다.

## 이번 실행의 마무리

사용자의 요청으로 잔여 실제 평가·독립 검토를 중단했다. [결과와 수정 사항](RESULTS.md), [범위 변경](scope-change.json)을 확인한다. 아래는 평가 재현/준비 절차이며 미실행을 완료로 간주하지 않는다.

최초 소스는 baseline/primary/runtime.zip에 원래 Git blob bytes로 보존했다. runtime/ 디렉터리는 설치 payload에 중첩 SKILL 사본이 들어가지 않도록 Git에서 제외한다. 필요하면 해당 ZIP을 runtime/에 풀어 살펴볼 수 있다. 당시 평가 방법은 freeze에 기록한 커밋/해시를 기준으로 확인하며, 현재 보완된 도구로 재평가할 때는 새 freeze label을 사용한다.

## 구성과 경계

- `actor/`: 두 원요구, 고정 사용자 답변과 종료/계속 응답. 수행 모델에게 개선 이유·rubric·기대 정답·사전 후보 목록을 주지 않는다.
- `evaluator/`: 실행 감독·판정·빈 컨텍스트 재현 지침. 수행 모델에게 전달하지 않는다.
- `fixtures.py`: 개인 사진 없는 작은 합성 JPEG·PNG·TIFF, 중복/손상 입력. 제공 프로젝트에는 입력 이미지와 해시만 복사하며 정답은 evaluator 측 freeze에 둔다. fixture는 사진 라이브러리 설치 없이 생성된다.
- `harness.py`: freeze, 준비, 공개 이벤트 기록, 명시적 파일 export, 무결성 확인과 재현 작업장 준비. 모델 API/CLI를 호출하거나 agent를 생성하지 않는다.

사용 모델은 `gpt-6-astra`/`xhigh`이고 세션 시간·응답 수 상한은 없다. 실제 host가 이 조건을 제공했는지 별도로 확인한다. 웹·위임·코드 실행을 못 했으면 통과가 아니다. actor가 쓴 활동 로그와 operator가 본 도구 이벤트를 구분하고, 전체 host trace나 토큰이 제공되지 않으면 미관찰/미측정으로 남긴다.

## 준비와 실행

1. runtime과 평가 준비 파일을 검토하고 커밋한 뒤 정확한 source revision을 freeze한다. 아래 `REVISION`은 해당 40자리 커밋으로 바꾼다. 각 출력 폴더는 새로 생성하며 기존 기록은 덮어쓰지 않는다.

```powershell
python tests/research-foundation/harness.py freeze --revision REVISION --out tests/research-foundation/baseline/primary
python tests/research-foundation/harness.py prepare --freeze tests/research-foundation/baseline/primary --run weather-sample1 --workspace tests/research-foundation/.work/weather-sample1 --out tests/research-foundation/results/weather-sample1
```

2. `weather-sample1`, `photos-sample1`, `weather-sample2`, `photos-sample2`를 각각 따로 prepare한다. 한 actor와 그 독립 조사자 두 명이 사용할 수 있는 여유를 확보하고 표본은 하나씩 수행한다. `fork_turns="none"`, 합의 모델/effort로 native actor를 시작하는 것은 operator의 별도 작업이다. 실제 모델과 설정이 확인되지 않으면 요구값을 관찰값으로 옮겨 적지 않는다.

3. 각 actor에게 해당 `.work/<run>/input.md`와 절대 작업 디렉터리만 준다. 추가로 읽을 수 있는 것은 복사된 `skill/`과 `project/`이고 기록은 `records/`에 쓴다. 작업 디렉터리 밖의 이 평가 폴더·루브릭·다른 실행 결과를 보게 하지 않는다. 이 프롬프트 경계는 기술적 격리가 아니므로 host가 제공하는 실제 제한은 별도로 기록한다. `.git` 파일, 별도 설정 복사, 설치된 스킬 갱신을 하지 않는다.

4. 첫 응답/질문 뒤 results의 `answers.md`를 한 번 제공한다. 이후 필요할 때 `continuation.md`, 실제 결과 전달 후 완료 확인에만 `close.md`를 쓴다. 세부 규칙은 [평가자 프로토콜](evaluator/protocol.md)을 따른다. 모델의 질문을 보고 새로운 취향이나 예상 정답을 만들어 답하지 않는다.

5. 실행 중/종료 시 공개 답변을 저장하고 관찰 이벤트를 따로 추가한다. `observer-template.json`의 미확인 값은 `null`로 유지한다. 각 raw 응답은 받은 바이트와 native 도구 원문 노출 범위를 명시하고, 사용자가 볼 공개 사본은 별도로 검토한다.

```powershell
python tests/research-foundation/harness.py event --out tests/research-foundation/results/weather-sample1 --source observer_event --kind actor_started --detail "Native fresh-context actor dispatched; observed model recorded separately."
```

## 수집과 재현

작업 폴더에서 **직접 검토한 파일 상대경로의 JSON 배열**을 results의 `allowlist.json`으로 만든다. 예: `["records/final.md", "project/.elenchus/topology.md", "project/.elenchus/research/index.md", "project/.elenchus/lab/R001/README.md"]`. 실제 코드·테스트·fixture·의존성 잠금·Research·공개 활동 기록도 필요한 범위로 모두 포함한다. 예제 목록만 복사하면 재현 자료가 충분하다는 뜻은 아니다. 실행 환경·캐시·`.git`·호스트 설정·비밀은 포함하지 않는다.

```powershell
python tests/research-foundation/harness.py export --workspace tests/research-foundation/.work/weather-sample1 --run tests/research-foundation/results/weather-sample1 --allowlist tests/research-foundation/results/weather-sample1/allowlist.json --out tests/research-foundation/results/weather-sample1/export-01
python tests/research-foundation/harness.py verify --export tests/research-foundation/results/weather-sample1/export-01
python tests/research-foundation/harness.py reproduce-prepare --export tests/research-foundation/results/weather-sample1/export-01 --workspace tests/research-foundation/.work/weather-sample1-reproduction --materials tests/research-foundation/results/weather-sample1/reproduction-materials.json
```

export는 개별 누락·읽기 실패·금지 경로를 기록하고 성공 파일도 보존한다. 부분 수집이면 exit code 1이며 미완료 사실을 보고한다. 파일당 32 MiB 초과는 공개 크기 경계로만 적용되며 연구 세션 시간 제한이 아니다. 필요한 큰 자료는 별도 검토한 방법으로 보존하고 provenance를 기록한다. 작업 폴더 자동 삭제는 없다. snapshot의 input/runtime/원본 프로젝트·사진 해시 변화를 확인한다. 저장소 원본의 변경 여부는 root operator가 해당 파일 해시와 Git diff로 별도 확인한다.

[재료 선택 보완](reproduction-selection.md)에 따라 actor 활동·과거 replay 폴더와 이를 포함한 ZIP은 재현 입력에서 제외한다. 현재 reproduce-prepare도 같은 선택 경로를 사용한다.

재현 검토자는 `reproduction` 작업장의 `input.md`와 `project/`만 받는다. 재현 요청은 freeze 해시로 확인한 바이트를 prepare 시 operator 결과 폴더의 `reproduction-input.md`로 고정하고, export에서 같은 바이트와 해시를 보존한다. `reproduce-prepare`는 검증한 export 사본만 사용한다. 현재 지침 파일이 바뀌어도 과거 실행의 입력을 바꾸지 않으며, 고정 사본이 누락·변조됐으면 현재 파일로 대신 채우지 않고 실패를 기록한다. 이 파일은 수행 actor의 작업장에 제공하지 않는다.

대화·활동 로그·observer 판정은 재현 검토자에게 제공하지 않는다. 실제 새 컨텍스트 검토자를 실행하고 공개 결과를 보존하는 것은 operator의 별도 작업이다. 검토자가 원래 자료를 고쳐 성공시키면 원본 재현 성공으로 계산하지 않는다.

## 무결성과 검사

freeze는 Git blob의 정확한 바이트를 바이너리로 추출한다. `git archive`나 checkout 텍스트 변환을 사용하지 않으며 CRLF와 LF 수를 각 source 파일에 기록한다. 결과 해시는 원문/공개 파일의 바이트 해시이고, native prompt의 wire bytes나 모델 내부 정규화에 대한 주장은 하지 않는다. 이 폴더의 `.gitattributes`는 평가 자료의 저장 바이트를 유지한다.

```powershell
python -m unittest discover -s tests/research-foundation -p "test_*.py"
```

fixture 생성·바이트 복사·경로 방어·부분 수집·원본 훼손 탐지·정답 분리·독립 재현 준비를 검사한다. deterministic helper 테스트는 네 native Research 평가를 대신하지 않는다.
