# Research 단계 분리 진단

이 실행은 최초 인터뷰와 늦게 전달된 선호 packet이 Research에 쓸 시간을 줄였는지 분리해 관찰하는 진단이다. 주 비교 8회나 후보 v2 재실행 4회를 대체하지 않고, 이전 timeout을 통과로 바꾸지 않는다.

- 기준 `132eea57d10baa68cd6482a9d0d2e170afd7357e`와 후보 `655f1c53342abdc8254f354ded168ebf17c6bf22` × 카지노·사진 정리 도구, 각 1개 표본으로 총 4회다.
- 두 버전 모두 같은 Research 시작 상태다. Topology와 조사 진행은 이미 확인됐고, 기존 최초 요구와 고정 선호 packet 전체를 첫 응답 전에 제공한다. Idea 파일에는 그 원문과 동일한 현재 상태만 기록한다.
- 기존 `fixtures/`의 요구·선호·합성 근거 원문은 변경하지 않는다. 예상 결론, rubric, 과거 결과, 수정 이유는 모델 입력에 포함하지 않는다. 추가 방향을 대신 선택하거나 후보별 설명을 주지 않는다.
- 요청은 이미 허용한 Research의 결과까지다. 전체 Execution 계획 합의는 다음으로 남긴다. 한 번의 응답·600초 한도, `gpt-6-astra`/`xhigh`, 동일한 CLI·workspace-write·승인 never·웹/위임 비활성화 조건을 쓴다.
- 네 실행은 각각 독립 OS 임시 프로젝트이며 subprocess 동시 실행은 최대 2개다. 자동 Research 종료 parser를 사용하지 않고 한 응답 또는 시간 제한에서 끝낸다.
- 시작 전에 protocol·script·공통 runner·source snapshot·결합 입력·Idea seed·고정 근거 파일 해시를 `frozen.json`에 고정한다.
- 공개 답변·도구 이벤트·산출물·source/input/output 해시·실제 파일 변경·host usage·시간·오류를 보존한다. 수집이 미완료이면 임시 작업장을 보존하며, 수집 완료 뒤 정리 실패는 독립적으로 기록한다.

종료 상태는 실행 사실이며 의미적 통과 점수가 아니다. 무엇을 발견·비교·판단했는지와 첫 사용자 가시 결과는 별도로 검토한다. 원래 계획 인터뷰 전체의 성능으로 확대 해석하지 않는다. 가상 원문 비교는 실제 웹 사례 발견 증거가 아니다.

```powershell
python -B tests/research-discovery/phase_isolation.py freeze
python -B tests/research-discovery/phase_isolation.py run --cli <Codex실행파일>
```

기존 인증은 일반 CLI 경로로 사용하되 복사·출력하지 않는다. Windows에서는 승인된 바깥 권한 상승과 `PYTHONUTF8=1`을 사용하고 평가 모델 권한은 유지한다.
