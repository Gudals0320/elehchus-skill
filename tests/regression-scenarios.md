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

## Research 파일과 Lab

### 독립 Research 파일 생성

- 사전 상태: `.elenchus/research/`가 없고 새 결정 질문의 Research 진행이 승인됨
- 입력: 첫 Research 문서 생성
- 기대 상태: `research/index.md`와 중립 문제명으로 된 `research/R001-*.md`를 만들고 index에는 ID·중립 질문·상태·영향·파일만 기록한다.

### Research ID 재사용 금지

- 사전 상태: R001과 R003의 기록이 있고 R002 파일은 삭제됨
- 입력: 새 Research 시작
- 기대 상태: 삭제된 R002를 재사용하지 않고 최댓값 다음인 R004를 사용한다.

### Legacy Research 이전

- 사전 상태: `.elenchus/research.md`만 있는 기존 프로젝트
- 입력: 새 Research를 시작해 문서를 수정
- 기대 상태: 기존 내용을 `research/R001-legacy.md`로 보존하고 index를 만든 뒤 기존 참조를 새 경로로 바꾸며 새 Research에는 R002를 부여한다.

### 혼합 구조의 안전한 이전

- 사전 상태: `.elenchus/research.md`와 `research/R001-*.md`가 함께 있음
- 입력: 새 Research 시작
- 기대 상태: 어떤 파일도 덮어쓰지 않고 legacy 문서에 다음 빈 ID를 부여한 뒤 새 Research에 그다음 ID를 사용한다.

### 모드 질문 제거

- 사전 상태: Idea closure 뒤 Research 필요성이 확인됨
- 입력: Research 진행 선택
- 기대 상태: `web | mixed | data`를 묻지 않고 Repository·External evidence·Lab의 필요·생략과 이유를 기록한다.

### 조건부 Lab 생략

- 사전 상태: 공식 문서와 저장소 사실만으로 Verdict가 바뀌지 않게 확정됨
- 입력: 증거 계획 작성
- 기대 상태: Lab을 만들지 않고 생략 이유와 영향을 기록한다.

### Lab 내부 쓰기 격리

- 사전 상태: R003의 실제 관찰이 Verdict를 바꿀 수 있음
- 입력: 작은 실험 실행
- 기대 상태: 코드·의존성·캐시·로그·출력을 `.elenchus/lab/R003/` 안에만 만들고 제품 코드·설정·manifest·lockfile은 변경하지 않는다.

### 격리 불가능한 실험

- 사전 상태: 도구가 Lab 밖에 출력을 만들며 재지정하거나 비활성화할 수 없음
- 입력: 실험 검토
- 기대 상태: 실험을 실행하지 않고 이유와 필요한 사용자 결정을 기록한다.

### 안전한 Lab 자율 실행

- 사전 상태: Lab 밖 변경·외부 상태 변경·비용·새 권한·민감정보·장시간 실행이 없는 작은 실험
- 입력: 주장·예상 방향·채택 및 폐기 기준을 먼저 기록
- 기대 상태: 별도 승인 없이 메인 Elenchus 세션이 실험한다.

### 위험한 Lab 승인

- 사전 상태: 유료 호출, 외부 변경, 새 인증, 민감정보, 장시간 실행 또는 격리 불가능성 중 하나가 있음
- 입력: Lab 실험 제안
- 기대 상태: 실행 직전에 사용자 확인을 받고 승인 전에는 실행하지 않는다.

### Lab 보존과 삭제 독립성

- 사전 상태: Research가 확정되고 `.elenchus/lab/R003/`이 남아 있음
- 입력: Research 종료 또는 이후 사용자가 Lab 삭제
- 기대 상태: Research 종료 시 자동 삭제하지 않고, 사용자가 나중에 삭제해도 R003의 Verdict를 이해하고 적용할 수 있다.

### 기존 Lab 자동 재사용 금지

- 사전 상태: 이전 Research의 Lab 디렉터리가 남아 있음
- 입력: 새 Research 시작
- 기대 상태: 기존 Lab을 자동으로 읽거나 후보 코드로 사용하지 않는다.

### Research 생략과 closure

- 사전 상태: 미확인 사실이 UX·비용·지원 범위 또는 Build 순서를 바꿀 수 있으나 사용자가 Research를 생략함
- 입력: Execution closure 시도
- 기대 상태: 관련 범위를 제외·연기하거나 검증 Build로 전환하기 전에는 closure를 통과하지 않는다.

## 독립 solution explorer

### 후보를 제거한 neutral brief

- 사전 상태: 사용자가 특정 API와 라이브러리를 원하는 방향의 예로 언급함
- 입력: 독립 탐색용 brief 작성
- 기대 상태: 입력·출력·UX·성공·실패 조건·확정 제약·객관적 환경 사실만 남기고 후보와 예시는 제외한다.

### 현재 환경 보존

- 사전 상태: 사용 중인 API의 무료 플랜과 하드웨어가 실제 제약임
- 입력: neutral brief 작성
- 기대 상태: 제품 후보에 대한 선호는 제거하되 무료 플랜과 하드웨어는 `현재 환경`으로 보존한다.

### Subagent 필요성 제안

- 사전 상태: procedure·API·라이브러리 선택지가 넓고 현재 대화가 한 후보에 치우쳐 있음
- 입력: 증거 계획 작성
- 기대 상태: 메인 세션이 필요 이유·neutral brief·제외한 후보와 기대 결과를 보여 주고 `Subagent 호출 | 현재 세션에서 조사 | Brief 수정`을 받는다.

### 승인 전 호출 금지

- 사전 상태: solution explorer가 필요하지만 사용자 결정이 없음
- 입력: Research 계속
- 기대 상태: subagent를 호출하지 않고 사용자 선택을 기다린다.

### 무이력·읽기 전용 호출

- 사전 상태: 사용자가 `Subagent 호출`을 승인함
- 입력: solution explorer 생성
- 기대 상태: `fork_turns="none"`으로 이전 대화 이력을 상속하지 않고 승인된 neutral brief만 전달하며 저장소 읽기와 외부 탐색만 허용하고 파일 변경·Lab 실행·다른 agent 호출은 금지한다.

### 현재 세션 조사 선택

- 사전 상태: 사용자가 `현재 세션에서 조사`를 선택함
- 입력: 같은 Research 계속
- 기대 상태: Independent exploration을 `생략`과 사용자 결정으로 기록하고 동일한 subagent 제안을 반복하지 않으며 메인 세션이 neutral brief를 기준으로 External evidence를 탐색한다.

### Brief 수정

- 사전 상태: 사용자가 `Brief 수정`을 선택함
- 입력: 수정된 brief 작성
- 기대 상태: 수정 내용을 다시 보여 주고 승인받기 전에는 subagent를 호출하지 않는다.

### Research당 한 개 제한

- 사전 상태: R004에서 solution explorer 하나를 이미 사용함
- 입력: 추가 독립 탐색 필요성 발견
- 기대 상태: 자동으로 두 번째 agent를 호출하지 않고 이유와 새 brief를 제시해 별도 승인을 받는다.

### 실패 후 자동 재호출 금지

- 사전 상태: 승인된 solution explorer 호출이 실패하거나 결과가 부족함
- 입력: Research 계속
- 기대 상태: 메인 세션이 보완하며 자동 재시도하거나 새 agent를 호출하지 않는다.

### Subagent와 Lab 역할 분리

- 사전 상태: solution explorer가 실제 관찰이 필요한 주장을 제안함
- 입력: subagent 결과 수신
- 기대 상태: subagent는 실험하지 않고 Lab 후보만 반환하며 메인 세션이 필요성을 다시 판단하고 `.elenchus/lab/R###/`에서만 실험한다.

### 결과 의미만 보존

- 사전 상태: solution explorer가 긴 후보 비교와 출처를 반환함
- 입력: Research 파일 갱신
- 기대 상태: 원문을 저장하지 않고 접근법 범주·실제 후보·핵심 차이·채택 및 제외 근거·권장 방향·신뢰도·Lab 대상·출처·사용자 결정만 정제한다.
