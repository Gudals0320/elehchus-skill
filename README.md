# Elenchus

Elenchus는 모호한 개발·연구 아이디어를 질문, 선택적 조사와 검증 가능한 실행 계획으로 확립하는 Codex 스킬이다.

사용자의 답을 받아 적는 데서 멈추지 않는다. 현재 판단의 전제와 반례를 찾고, 사용자 경험을 바꾸는 빈틈을 질문 하나씩 추적한다. 계획이 합의되기 전에는 구현을 시작하지 않는다.

## 흐름

```text
Idea
↔ Research (필요한 시점)
→ Execution
→ 계획 완료
→ 일반 모드에서 구현 또는 후속 요청
```

- Idea는 문제, 해결 방향과 실제 사용자 경험을 하나의 문서에서 다룬다.
- Research는 독립 질문별 파일에서 접근법·사례를 발견·비교하고 필요한 주장을 검증한다. 레퍼런스가 필요한 선택은 Idea 확정 전에도 조사하며 Web·Repository·Browser·Lab을 목적에 맞게 사용한다.
- Execution은 계획을 Phase로 묶고 모든 Build의 사용자 행동과 Approve 조건을 합의한다.

## 주요 특징

- 사용자에게 한 번에 질문 하나만 제시한다.
- 의미가 명확한 답변은 반영 내용을 알리고 이어가며, 새로운 해석이나 충돌은 확인한다. 사용자가 허용한 독립적 저위험 Build는 전체 현재 내용을 제시한 뒤 묶음으로 합의할 수 있다.
- 목표·제약·성공 기준·맥락의 공백을 추적하고, 사용자 결과와 선행 결정에 미치는 영향이 큰 질문부터 다룬다. 미뤄둔 필수 항목도 끝까지 확인한다.
- 저장소와 문서에서 확인할 수 있는 사실은 먼저 조사한다.
- 탐색·벤치마킹은 접근법 발견 → 실제 사례 비교 → 적용 판단으로 진행한다. External evidence는 발견한 후보의 중요한 주장과 공개 근거를 검증한다. 비교·관찰이 미완료인데 후속 Build에 넘겼다는 이유로 탐색을 완료하지 않는다.
- 로그인·개인화 환경은 사용자가 지정한 브라우저 탭에서 observation-only로 확인하고 현재 계정·권한·시점에만 적용한다.
- 비개발자가 화면, 파일, 행동, 비용과 실패 결과를 보고 결정할 수 있게 설명한다.
- 기능 추가뿐 아니라 유지·축소·연기·제거·만들지 않기를 같은 선택지로 다룬다.
- 모든 Phase 경계와 Build가 합의되고 전체 closure를 통과하기 전에는 계획을 완료하지 않는다.
- `[Elenchus · 진행 중]`인 동안만 계획 전용 상태를 유지하고 완료 뒤에는 같은 작업을 일반 모드로 전환한다.

## 설치

Codex에 다음과 같이 요청할 수 있다.

```text
$skill-installer를 사용해 Gudals0320/elehchus-skill 저장소의 루트 스킬을 elenchus라는 이름으로 설치해 줘.
```

설치 스크립트를 직접 사용할 때는 다음과 같이 실행한다.

```powershell
py "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo Gudals0320/elehchus-skill `
  --path . `
  --name elenchus
```

기존 `~/.codex/skills/elenchus`가 있으면 설치 스크립트는 덮어쓰지 않고 중단한다.

## 사용

새 세션을 시작하거나 완료된 세션에 재진입할 때 명시적으로 호출한다. 호출 토큰은 대소문자를 구분하지 않는다.

```text
$elenchus 를 사용해 이 아이디어를 실행 전에 구체화해 줘.
skill:Elenchus 로 기존 계획을 재검토해 줘.
```

일반적인 `Elenchus` 언급, `.elenchus/` 문서의 존재와 `Build`, `Phase`, `execution.md` 같은 용어는 호출로 취급하지 않는다. 진행 중인 세션은 호출 토큰을 반복하지 않아도 계속되지만 `[Elenchus · 완료]` 뒤에는 다시 명시적으로 호출해야 한다.

프로젝트 루트에는 진행 단계에 따라 다음 문서가 만들어진다.

```text
./.elenchus/
├─ idea.md
├─ research/         선택
│  ├─ index.md
│  └─ R###-neutral-topic.md
├─ lab/              조건부 Research 작업장
│  └─ R###/
└─ execution.md
```

`research/index.md`에는 각 조사의 ID·중립 질문·상태·영향·파일만 두고 상세 근거와 Verdict는 `R###` 파일에 기록한다. 탐색에는 [Discovery](stages/discovery.md)의 접근법 비교·직접 근거·적용 가능성·결정 영향·종료 이유를 적용한다. 사실·후보 검증에는 필요한 깊이의 Web Evidence를 사용한다. 승인된 공개 조사에서는 메인이 별도 탭으로 시각 자료를 관찰할 수 있다. 로그인된 사용자 환경은 지정한 탭에서만 Browser Evidence로 관찰하며 기존 탭을 임의로 탐색하거나 외부 상태를 변경하지 않는다.

실제 데이터·하드웨어·API 동작을 격리해 관찰해야 할 때만 `.elenchus/lab/R###/`에서 제품 파일과 분리된 실험을 수행한다. Browser 시각 자료는 Verdict에 필수이고 사용자가 승인한 경우에만 비식별화해 해당 Lab 아래에 저장한다. Lab은 자동 삭제하거나 구현 코드로 승격하지 않으며 사용자가 언제든 삭제할 수 있다.

합의된 조사 범위에서는 메인이 사례 탐색·구현 탐색·집중 검증의 역할 분담과 후속 조사를 판단한다. 독립 탐색에는 목적·확정 제약·열린 선택을, 집중 검증에는 확인할 후보·주장을 전달한다. 인원과 호출별 확인을 고정하지 않으며 범위가 크게 늘어나면 새로 합의한다. 가능한 도구 제한과 실제 권한·독립성의 한계를 구분하고 미지원 위임을 수행했다고 보고하지 않는다. 실제 Lab·로그인 관찰, 결정적 출처 재확인과 최종 Verdict는 메인이 맡는다.

기존 `.elenchus/research.md`는 새 Research를 시작할 때 내용을 보존해 `research/R001-legacy.md` 또는 다음 빈 ID로 이전하고 기존 참조를 갱신한다. 단순히 프로젝트를 읽는 것만으로는 마이그레이션하지 않는다.

`idea.md`는 프로젝트 전체의 누적 의도 계약이며 Phase별 사본이나 별도 `contract.md`를 만들지 않는다. `execution.md`는 하나의 파일에서 다음 두 단계만 사용한다.

```text
Phase #1
├─ Build #1
└─ Build #2

Phase #2
├─ Build #3
└─ Build #4
```

Build 번호는 Phase마다 초기화하지 않는 프로젝트 전체 ID다. 기존 Phase 헤더 없는 계획은 Phase #1로 간주하고, 새 Phase의 Build는 기존 활성·폐기 Build 중 가장 큰 번호 다음부터 시작한다. Feature는 별도 계획 계층으로 만들지 않으며 기존 Feature의 의미는 하위 Build의 이름·범위·설계 근거에 보존한다.

## Release 확인과 업데이트

Elenchus는 새 Codex 작업에서 시작될 때 최신 정식 Release를 한 번 확인한다.

- 새 버전이 없으면 바로 진행한다.
- Windows 샌드박스가 네트워크를 차단하면 승인 가능한 네트워크 권한 상승으로 같은 확인을 한 번 재시도한다.
- 권한 요청이 거절되거나 재시도·GitHub 확인이 실패하면 현재 버전으로 계속하며 같은 작업에서 반복하지 않는다.
- 새 버전이 있으면 현재·최신 버전과 Release 링크를 보여 주고 업데이트 여부를 묻는다.
- 명시적인 승인 없이는 설치본을 변경하지 않는다.
- 업데이트가 완료되면 새 Codex 작업에서 다시 호출한다.

## 범위

Elenchus는 아이디어와 실행 계획을 확정하는 데서 끝난다. `[Elenchus · 진행 중]`인 동안에는 제품 코드 구현과 개발 진행 추적을 수행하지 않는다. `[Elenchus · 완료]` 응답 뒤에는 상태 표식을 제거하고 같은 작업의 후속 요청을 일반 모드로 처리한다.

## 개발 검증

기존 Python 패키지·업데이트 검사는 `python -B -m unittest discover -s tests`로 실행한다. 실제 대화 동작은 [평가 절차](tests/evaluation.md)와 [합성 입력](tests/evaluation-fixtures.md)으로 재실행할 수 있다.

[평가 결과](tests/evaluation-results.md)는 동작 판정과 효용·비용 비교를 구분하며, [실행 기록](tests/evaluation-records.md)에 응답·호출·파일 변화를 연결한다. 시나리오 목록, 실제 모델 실행, 모의 도구와 호스트 검증을 서로의 증거로 대체하지 않는다.

위 평가는 당시 지침의 기록이다. Issue #12의 탐색·자율 위임 개정은 [개발·평가 기록](docs/research-discovery-plan.md)과 `tests/research-discovery/`의 별도 입력·실행·결과에서 확인한다.

## 라이선스

MIT License
