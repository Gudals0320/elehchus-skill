# Elenchus

Elenchus는 모호한 개발·연구 아이디어를 질문, 선택적 조사와 검증 가능한 실행 계획으로 확립하는 Codex 스킬이다.

사용자의 답을 받아 적는 데서 멈추지 않는다. 현재 판단의 전제와 반례를 찾고, 사용자 경험을 바꾸는 빈틈을 질문 하나씩 추적한다. 계획이 합의되기 전에는 구현을 시작하지 않는다.

## 흐름

```text
Idea
→ Research (선택)
→ Execution
→ 계획 완료
→ 일반 모드에서 구현 또는 후속 요청
```

- Idea는 문제, 해결 방향과 실제 사용자 경험을 하나의 문서에서 다룬다.
- Research는 외부 사실이나 데이터 공백이 실행 순서를 바꿀 때만 진행한다.
- Execution은 모든 Build를 작성하고 Build마다 사용자 행동과 Approve 조건을 합의한다.

## 주요 특징

- 사용자에게 한 번에 질문 하나만 제시한다.
- 목표·제약·성공 기준·맥락 중 가장 약한 부분을 계속 추적한다.
- 저장소와 문서에서 확인할 수 있는 사실은 먼저 조사한다.
- 비개발자가 화면, 파일, 행동, 비용과 실패 결과를 보고 결정할 수 있게 설명한다.
- 기능 추가뿐 아니라 유지·축소·연기·제거·만들지 않기를 같은 선택지로 다룬다.
- 모든 Build가 합의되고 전체 closure를 통과하기 전에는 계획을 완료하지 않는다.
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
├─ research.md       선택
└─ execution.md
```

## Release 확인과 업데이트

Elenchus는 새 Codex 작업에서 시작될 때 최신 정식 Release를 한 번 확인한다.

- 새 버전이 없으면 바로 진행한다.
- 확인할 수 없으면 현재 버전으로 계속한다.
- 새 버전이 있으면 현재·최신 버전과 Release 링크를 보여 주고 업데이트 여부를 묻는다.
- 명시적인 승인 없이는 설치본을 변경하지 않는다.
- 업데이트가 완료되면 새 Codex 작업에서 다시 호출한다.

## 범위

Elenchus는 아이디어와 실행 계획을 확정하는 데서 끝난다. `[Elenchus · 진행 중]`인 동안에는 제품 코드 구현과 개발 진행 추적을 수행하지 않는다. `[Elenchus · 완료]` 응답 뒤에는 상태 표식을 제거하고 같은 작업의 후속 요청을 일반 모드로 처리한다.

## 라이선스

MIT License
