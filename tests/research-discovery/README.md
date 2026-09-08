# Research 탐색 개선 평가

이 디렉터리는 이슈 #12의 변경 전후 통제 평가와 별도 실제 웹 평가를 보존한다. 이전 `tests/evaluation-*.md`는 역사적 기록이며 이번 결과로 덮어쓰지 않는다.

## 고정 조건과 해석

- 기준은 `132eea57d10baa68cd6482a9d0d2e170afd7357e`의 스킬 runtime이다. `freeze`가 Git archive에서 추출한 파일별 SHA-256을 고정한다. 후보도 실행 전 runtime을 커밋하고 해당 커밋의 Git archive·파일별 SHA-256을 고정한다. runtime에 미커밋 변경이 있으면 후보 freeze를 거부한다. Windows 체크아웃의 CRLF는 이 확인에만 LF로 정규화하며 두 평가군의 실행 사본은 모두 Git의 원래 바이트를 사용한다.
- 통제 비교는 카지노·로컬 사진 정리 도구 × 기준/후보 × 독립 표본 두 개, 총 8회다. 모델은 `gpt-6-astra`, reasoning `xhigh`, 회당 최대 8개 응답·600초다. 같은 사례의 원요구·선호·근거·사용자 후속 응답은 동일하다.
- 카지노 입력은 첫 실사용의 **최초 사용자 요청만** 재현한다. 이후 리뷰·예상 해법·개선 이슈·판정 기준은 평가 모델에 전달하지 않는다. 사진 정리 도구는 새로운 합성 요구다.
- 고정 근거는 **가상의 제품·개발 문서**다. 비교·적용·직접 관찰 범위·출처 중복·상충 조건을 통제할 수 있지만, 실제 제품의 존재나 웹에서 사례를 발견하는 능력을 입증하지 않는다. 링크는 예약 도메인 `.example`이며 접근하지 않는다. 시각 자료는 제공되지 않았다는 원문 사실이 있다.
- 실제 웹·subagent 평가는 두 사례를 사전 후보 없이 별도 새 컨텍스트에서 진행한다. 회당 최대 12개 응답·1,200초이고 통제 비교와 합산하지 않는다. 도구 미지원은 통과로 계산하지 않는다.
- 프롬프트에 쓰인 공통 실행 경계 외에 새 동작을 가르치는 요약은 넣지 않는다. 사용 모델은 해당 runtime 사본과 필요한 단계 문서를 직접 읽는다.

## 실행과 보존

Python 3.10 이상과 인증된 Codex CLI만 사용한다. 계정 인증은 기존 CLI 경로로 접근하며 복사하거나 출력하지 않는다. `--ignore-user-config --ephemeral`, 웹 비활성화, 승인 `never`, 제품 파일에 쓰기 권한이 있는 `workspace-write`를 사용한다. 설치된 동명 스킬은 호출별 설정으로 비활성화하며 사용자 설정·스킬을 수정하지 않는다.

```powershell
python tests/research-discovery/runner.py freeze --variant baseline
python tests/research-discovery/runner.py freeze --variant candidate --label candidate-v1
python tests/research-discovery/runner.py probe --cli <Codex실행파일>
python tests/research-discovery/runner.py run --snapshot tests/research-discovery/snapshots/baseline.json --case casino --sample 1 --cli <Codex실행파일>
python tests/research-discovery/runner.py run --snapshot tests/research-discovery/snapshots/candidate-v1.json --case casino --sample 1 --cli <Codex실행파일>
python -m unittest discover -s tests/research-discovery -p "test_*.py"
```

스냅샷과 실행 결과를 덮어쓰지 않는다. 후보 수정 후에는 새 label로 freeze하고 재검증하며 실패 기록도 유지한다. CLI 버전은 매 실행 저장한다. `probe`는 설치·인증 가능성만 보는 setup 실행이며 본평가가 아니다. 호스트 권한 문제로 CLI 실행에 바깥 권한 상승이 필요하면 이유를 기록하며 내부 모델의 sandbox는 그대로 유지한다.

임시 프로젝트와 runtime 사본·사용자 대화·제품 stub은 OS 임시 디렉터리에 만든다. 후속 응답은 같은 파일 상태와 **공개된 이전 사용자/assistant 대화**를 새 ephemeral CLI에 제공한다. 원래 agent의 숨은 상태를 복원하는 CLI resume 평가는 아니다. 초기에는 원요구, 첫 후속에는 고정 선호 packet, 이후에는 같은 범위의 확인·진행 응답을 사용한다. 제시하지 않은 새 선택이나 기능을 자동 승인하지 않는다.

첫 선호 packet을 전달한 뒤, Research 문서에 선택된 결론이 있고 공개 응답도 결론을 명시하면 `reported_research_verdict`로 종료할 수 있다. `Verdict`뿐 아니라 `결론과 다음 행동` 같은 한국어 기록도 허용하지만, 미선택 enum·TODO 틀이나 단순히 `공백`을 언급한 응답은 종료 신호가 아니다. 이는 실행 구간을 자르는 보고 경계 추정이며 품질 통과가 아니다. 최초로 사용자에게 보인 Research 결과는 별도 수동 지표로 확인해 자동 경계 누락으로 늘어난 후속 처리 시간과 구분한다. 그 외에는 응답·시간 상한에서 종료한다. 에러·시간 초과·제품 수정·소스 오염을 보존하고 자동으로 성공 처리하거나 재시도하지 않는다.

각 실행은 manifest·fixture·source·실제 입력 해시, 공개 응답·도구 이벤트, 문서 산출물, 제품 파일 전후 해시, 종료 사유, host usage와 시간을 남긴다. hidden reasoning 이벤트는 읽어 분류한 뒤 버리고 공개 로그에 쓰지 않는다. 사용자 경로·인증 관련 문자열은 저장 전에 비식별화한다. JSONL에 기록되지 않은 도구 내부 행동은 관찰했다고 주장하지 않는다. 질문 수는 후보 문장 자동 집계이며 실질 결정·재확인·수정은 수동 검토한다.

Windows 첫 카지노 두 실행에서는 sandbox가 만든 문서 디렉터리를 host가 읽지 못했다. 원래 collector의 빈 결과는 파일 불변·문서 부재의 증거가 아니다. [복구 시도와 원래 runner](infrastructure/host-read-repair.json)를 별도로 보존했다. 이후 새 임시 프로젝트에는 모델 실행 전에 해당 host의 읽기 상속 ACE만 준비한다. 모델 권한이나 지침은 바꾸지 않는다. 접근 오류는 strict walk로 검출해 `artifact_collection: incomplete`로 기록하고 파일 변경 여부를 미관찰로 남긴다. 수집이 미완료이면 정리 시도를 건너뛰고 해당 작업장을 보존한다. 실행별 `runner_sha256`·`host_read_setup`과 [수집·종료 경계 보완](infrastructure/closure-and-retention-repair.json)에 기록한 차이를 비교할 때 확인한다.

## 사전 판정 기준 — 평가자 전용

이 README와 manifest·runner·다른 실행 결과는 모델 프로젝트에 복사하지 않는다. 평가는 각 항목을 `충족 | 부분 충족 | 미충족 | 미관찰`로 적고 실제 응답/문서/도구 증거를 연결한다.

| 기준 | 평가할 내용 |
|---|---|
| 접근법 비교 | 서로 다른 방식과 선택 조건을 비교했는가. 후보/예시를 필수 제약으로 바꾸지 않았는가 |
| 적합한 직접 근거 | 자료·원문 위치를 확인했는가. 문서 설명/직접 관찰/추론을 구분하고 동일 원천·버전 충돌·없는 화면을 정직하게 처리했는가 |
| 적용 가능성 | 가져올 부분, 바꿀 조건, 적용 어려움·비용·실패 경험을 우리 요구와 연결했는가 |
| 결정 영향 | 채택/제외/보류/유지 근거와 필요한 사용자 선택 또는 선행 검증을 제시했는가 |
| 종료 이유 | 결론을 바꿀 공백을 남긴 채 완료라 하지 않았는가. 웹 비교와 실제 실험으로만 풀 공백을 적절히 구분했는가 |

함께 확인할 경계는 초기 탐색 시점, 단순 사실 질문의 과잉 조사, 위임 지원/권한 설명, 조사 승인 반복, 계획 중 제품 변경, 세션 진입·종료와 문서 호환이다. 통제 환경은 위임 호출 자체를 제공하지 않으므로 실제 역할 분담은 별도 live 기록으로 판정한다.

질문 후보·실질 결정·재확인·사용자 수정·도구 호출·시간·host가 제공한 토큰을 기록한다. 모의 사용자 결과를 실제 사용자 만족도나 피로로 해석하지 않는다. 표본이 작고 모델 응답은 비결정적이므로 일반적인 우위나 완전한 위험 발견을 선언하지 않는다. 실패 수정 후에는 영향받는 사례와 표적 회귀만 다시 실행하고 최초 결과를 합산해 숨기지 않는다.
