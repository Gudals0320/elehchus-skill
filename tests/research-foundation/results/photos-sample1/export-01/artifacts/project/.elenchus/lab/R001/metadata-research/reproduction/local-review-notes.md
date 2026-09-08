# 날짜별 로컬 검토 문서 후속 재현

확인일: 2026-09-08. 기존 독립 복제 프로젝트와 설치된 Python 3.12.10/Pillow 12.3.0 venv를 그대로 사용했다. 이번 후속 작업에는 패키지 설치나 네트워크 도구 호출이 없었다. 모든 실행은 Windows 일반 sandbox에서 성공했고 추가 권한 상승도 필요 없었다.

## 최종 결과

- 최신 `render_review.py`, `probe_local_review.py`를 복제해 CLI Markdown 생성과 로컬프로브를 실행했다. 최종 **12개 중12개 통과, Python socket 진입점 호출0**.
- 별도 `audit_local_review.py`의 원본10개/복제10개 불변, CLI·함수·저장 문서 일치, 로컬프로브 통과, socket 호출0, core scanner SHA 동일 확인이 전부 통과했다.
- 제공8개에 대한 날짜별 후보는 2024-07-15의 JPEG 두 파일과 날짜 미지정6개다. TIFF의 수정일은 촬영일 버킷으로 사용하지 않고 원문·출처·오프셋 상태를 보여 준다.
- 정확히 같은 파일 그룹은 763바이트의 두 JPEG이며 SHA-256과 실제 바이트 비교 근거를 보여 준다. 대표 파일·삭제·이동 선택은 없다.
- 회전 원시값6/8, 시계/반시계90도 해석, 저장/파서/표시 치수가 별도 열에 표시된다. 최초 메타데이터 조회가 내부 디코딩을 유발할 수 있다는 표현도 확인했다.

## 발견·보완·재검증

최초 렌더러는 날짜의 `subsecond_raw`를 Markdown에서 생략했다. 기존 합성 `modified-offset.jpg`를 독립적으로 읽은 결과 JSON에는 `25`가 있었지만 날짜 근거 문자열에는 없었다. `local-review-audit-results.json`이 이 실제 결과를 보존한다. 제공8개에는 초 미만 태그가 없어 해당 문서 결과 오류는 아니었지만, 날짜 원문 근거를 사람이 확인하는 범위에는 빠진 값이었다.

메인에 근거와 제안을 전달했고 메인이 `subsec=원문` 표시를 추가했다. 메인의 프로브에는 기존 합성 `offset-date.jpg`의 `123456789` 표시 검증이 추가됐다. 최신 두 파일을 다시 복제한 후 12개 프로브 통과와 독립 `modified-offset.jpg`의 `subsec=25` 표시를 확인했다. 미해결된 추가 수정 요구는 없다. 메인 코드나 원본 입력은 이 담당자가 수정하지 않았다.

## 재현·증거 위치

`project/.elenchus/lab/R001/main/` 아래:

- `independent-local-review-final.md`: 독립 CLI 생성 문서.
- `independent-local-render-final.log`, `independent-local-probe-final.log`: 실제 stdout.
- `local-review-results.json`: 복제본에서 새로 실행한 12개 결과. 처음 복제한 메인의 결과로 성공을 선언하지 않았다.

이 폴더 아래:

- `audit_local_review.py`, `local-review-audit-results-final.json`, `local-review-audit-final.log`: 별도 원본/복제/표시 의미 대조와 실제 subsecond 문자열.
- `local-review-copied-sha256.json`: 최초 새 파일4개 복제 해시. 최종 renderer/probe 해시는 `local-review-copied-sha256-final.json`과 audit 결과에 있다.
- `activity.jsonl`: 이 후속 작업의 명령·결과. 담당 records의 활동 기록에도 같은 요약을 남겼다.

프로브가 기대하는 `sample-report-final.json`은 앞선 독립 CLI로 실제 생성해 검증했던 `independent-cli-report-final.json` 사본이다. core scanner를 다시 구현하거나 메인 샘플 결과를 대신 조작하지 않았다. `review.md`는 비교 기준으로 메인이 생성한 최신 문서를 복제했다. CLI는 별도 새 파일명으로 결과를 만들었으며 함수 렌더링·복제된 기준 문서와 일치했다.

복제 main 폴더에서 재실행:

```powershell
& '.venv/Scripts/python.exe' -B render_review.py sample-report-final.json --output another-new-review.md
& '.venv/Scripts/python.exe' -B probe_local_review.py
```

첫 명령은 이미 존재하는 출력 이름을 사용하면 거부된다. 두 번째는 복제본 `local-review-results.json`을 새 실행 결과로 기록한다.

## 판단 범위

설치가 끝난 환경에서 현재 스캔·문서 생성을 로컬로 실행한 결과다. Python `socket`, `create_connection`, `getaddrinfo` 차단은 해당 진입점의 무호출 확인이며 OS 방화벽/모든 가능한 외부 통신 경로의 격리 증명으로 확대하지 않는다. 사람이 읽는 Markdown 원문과 데이터 의미를 검토했으며 특정 외부 Markdown 뷰어의 실제 시각 렌더링은 관찰하지 않았다. HEIC/RAW·다른 형식·실제 카메라·대량 성능 검증을 추가로 주장하지 않는다.
