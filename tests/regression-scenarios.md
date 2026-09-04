# Elenchus 회귀 시나리오

이 문서는 Elenchus의 호출·지속·완료 계약을 입력과 기대 상태로 검토한다. 각 시나리오는 독립적으로 실행한다.

## Lifecycle

### 명시적 최초 호출

- 사전 상태: Elenchus 상태 표식이 없는 새 작업
- 입력: `$ELENCHUS 를 사용해 아이디어를 구체화해 줘.`
- 기대 상태: `[Elenchus · 진행 중]`으로 시작한다.

### 대체 호출 토큰

- 사전 상태: Elenchus 상태 표식이 없는 새 작업
- 입력: `SKILL:Elenchus 로 이 계획을 검토해 줘.`
- 기대 상태: 토큰의 대소문자와 관계없이 `[Elenchus · 진행 중]`으로 시작한다.

### 일반 이름 언급

- 사전 상태: Elenchus 상태 표식이 없는 작업
- 입력: `Elenchus가 작성한 계획을 요약해 줘.`
- 기대 상태: Elenchus를 시작하지 않고 상태 표식 없이 일반 요청으로 처리한다.

### 프로젝트 문서와 계획 용어

- 사전 상태: 프로젝트에 `.elenchus/`와 확정된 `execution.md`가 있으며 Elenchus 상태 표식은 없다.
- 입력: `Build #4 닫고 Phase #2의 Build #5 얘기해보자.`
- 기대 상태: Elenchus를 시작하지 않고 상태 표식 없이 일반 요청으로 처리한다.

### 진행 중 세션 지속

- 사전 상태: 직전 응답이 `[Elenchus · 진행 중]`이다.
- 입력: `첫 번째 선택으로 할게.`
- 기대 상태: 호출 토큰이 없어도 `[Elenchus · 진행 중]`으로 현재 질문 흐름을 계속한다.

### 완료 후 일반 모드

- 사전 상태: 직전 응답이 `[Elenchus · 완료]`이며 계획이 확정되었다.
- 입력: `Build #1부터 구현해 줘.`
- 기대 상태: Elenchus를 재활성화하거나 상태 표식을 붙이지 않고 일반 구현 요청으로 처리한다.

### 완료 후 명시적 재진입

- 사전 상태: 이전 응답에 `[Elenchus · 완료]`가 있고 `.elenchus/` 문서가 존재한다.
- 입력: `$elenchus 로 기존 계획을 재검토해 줘.`
- 기대 상태: 기존 문서를 읽고 `[Elenchus · 진행 중]`으로 재진입한다.

### 진행 중 구현 요청

- 사전 상태: 직전 응답이 `[Elenchus · 진행 중]`이다.
- 입력: `지금 코드까지 구현해 줘.`
- 기대 상태: 제품 구현을 시작하지 않고 계획 closure 또는 명시적 종료를 먼저 처리한다.

## Phase와 Build

### 기존 평면 계획 호환

- 사전 상태: Phase 헤더 없이 `### Build #1`부터 `### Build #5`까지 있는 기존 `execution.md`
- 입력: `skill:elenchus 로 새로운 범위를 Phase로 추가해 줘.`
- 기대 상태: 기존 Build를 내용·순서·번호 변경 없이 Phase #1로 묶고 제목 깊이만 `####`로 조정한 뒤 Phase #2를 추가한다.

### Phase 간 전역 Build 번호

- 사전 상태: 진행 중인 Elenchus의 Phase #1에 Build #1부터 Build #5까지 있음
- 입력: Phase #2의 첫 Build를 작성
- 기대 상태: Build 번호를 초기화하지 않고 Build #6을 부여한다.

### 기존 Phase 수정 시 새 Build

- 사전 상태: 진행 중인 Elenchus의 Phase #1과 Phase #2에 Build #1부터 Build #8까지 있음
- 입력: Phase #1을 수정하면서 Build 하나를 추가
- 기대 상태: 새 Build를 Phase #1에 두되 전역 최댓값 다음인 Build #9를 부여한다.

### 삭제 번호 보존

- 사전 상태: 진행 중인 Elenchus에 Build #1부터 Build #6까지 있고 Build #6을 삭제함
- 입력: 새 Build를 추가
- 기대 상태: Build #6을 폐기 이력의 제목으로 보존하고 새 Build에 #7을 부여한다.

### Build 분리

- 사전 상태: 진행 중인 Elenchus에 Build #1부터 Build #7까지 있음
- 입력: Build #3을 두 Build로 분리
- 기대 상태: 원래 범위를 담당하는 Build는 #3을 유지하고 추가 Build에 #8을 부여한다.

### Build 병합

- 사전 상태: 진행 중인 Elenchus에서 Build #3과 Build #4를 병합하기로 합의함
- 입력: 병합 결과를 문서에 반영
- 기대 상태: 더 작은 Build #3을 유지하고 Build #4는 대표 Build와 이유를 적은 폐기 이력으로 이동한다.

### Feature 계층 제거

- 사전 상태: 진행 중인 Elenchus에서 사용자가 새 Feature를 추가하고 싶다고 표현함
- 입력: `결제 Feature를 다음 계획에 넣어 줘.`
- 기대 상태: Feature 번호·헤더·문서를 만들지 않고 범위에 따라 Phase 또는 Build의 이름과 범위에 반영한다.

### 기존 Feature 계층 축소

- 사전 상태: Phase #1 아래 Feature #1과 그 하위 Build #1·#2가 있는 기존 계획
- 입력: `$elenchus 로 기존 계획을 수정해 줘.`
- 기대 상태: Feature 헤더를 제거하고 Build #1·#2를 Phase #1 바로 아래로 옮긴다. Feature의 의미는 각 Build의 이름·범위·설계 근거에 보존하고 Build 번호와 순서는 바꾸지 않는다.

### Phase와 Build closure

- 사전 상태: 진행 중인 Elenchus에 여러 Phase와 활성·폐기 Build가 함께 있음
- 입력: Execution closure audit 수행
- 기대 상태: 모든 활성 Build의 합의와 Phase 경계, 전역 번호의 고유성, 폐기 번호 보존을 검사하며 폐기 Build에는 활성 Build의 전체 필드를 요구하지 않는다.
