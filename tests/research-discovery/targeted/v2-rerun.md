# 후보 v2의 표적 재검증

원래 `manifest.json`·`fixtures.json`·`protocol.md`·`frozen.json`·v1 결과를 보존한다. 새 준비 label은 별도 `preparations/` 파일을 만들며, 실행 label은 별도 결과 디렉터리를 만든다. 기본 인자를 생략하면 기존 `frozen.json` 경로와 원래 manifest의 snapshot 선택을 유지한다. frozen source/runner의 해시가 달라진 경우 기존 기록을 바꾸지 않고 오류를 낸다.

후보 v2는 `655f1c53342abdc8254f354ded168ebf17c6bf22`이다. 중복 Research/Web Evidence 문서 작성을 줄인 변경의 영향을 받는 `single-fact`, `version-conflict`, `delegation-unavailable`만 기존 입력·판정 기준·모델·한 응답/180초 제한으로 재실행한다. 기존 lifecycle 세 사례를 다시 실행한 것처럼 계산하지 않는다. 결과는 v1과 별도로 보존하고 timeout을 통과로 바꾸지 않는다.

```powershell
python -B tests/research-discovery/targeted.py prepare --snapshot tests/research-discovery/snapshots/candidate-v2.json --preparation-label targeted-v2
python -B tests/research-discovery/targeted.py run --snapshot tests/research-discovery/snapshots/candidate-v2.json --preparation-label targeted-v2 --label targeted-v2 --case single-fact --cli <Codex실행파일>
```

나머지 두 사례도 `--case`만 바꿔 같은 준비 기록을 사용한다. 첫 평가의 코드와 해시는 `infrastructure/targeted-before-preparation-labels.py.txt` 및 관련 변경 기록에 보존한다. 새 인자는 결과 분리와 명시적 source 선택만 바꾸며 모델에게 전달하는 사례 원자료·AGENTS 지침을 변경하지 않는다.
