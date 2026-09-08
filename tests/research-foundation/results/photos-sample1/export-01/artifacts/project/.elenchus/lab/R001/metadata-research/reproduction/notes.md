# 독립 복제 재현·코드 검토

확인일: 2026-09-08. 대상은 메인의 사진 기능 재료이며 최종 IFD 보완 뒤 `photo_materials.py`, `generate_fixtures.py`, `test_photo_materials.py`를 다시 복제해 검증했다. 제공된 기능 경로와 검토한 코드에서 추가 수정을 요구할 직접 결함은 발견하지 않았다.

## 실제 결과

- 새 Python 3.12.10 venv에 requirements의 Pillow 12.3.0을 설치했다. 기존 main venv/cache는 복사하거나 재사용하지 않았다.
- 최종 기존 테스트 28개 중 27개 통과, 1개 skip. Windows symlink 생성이 WinError1314로 불가능한 테스트를 통과로 계산하지 않았다. 하드링크 생성/alias 확인은 실제 통과했다.
- 복제 입력 8개 CLI 결과: `ok=5`, `invalid_image=1`, `non_image_or_unsupported=2`, `exact_groups=1`, `snapshot_bytes=3538`.
- 별도로 작성한 `audit_reproduction.py`의 출력 의미·해시 대조도 통과했다. 촬영 날짜 버킷을 가진 것은 dated JPEG 두 바이트 복사본뿐이고 모두 `2024-07-15`; TIFF 수정일과 손상 파일에는 버킷이 없고, 모든 후보가 `review_only`다.
- 원본 입력8개+sentinel+manifest 총10개 SHA-256이 작업 전후 동일하다. 복제본10개도 원본과 일치한다. 최종 코드/README/baseline/requirements 6개 사본 SHA-256이 해당 시점 메인 원본과 같았다. 전체 값은 `audit-results.json`에 있다.

## 독립 검토 판단

| 달성 기준 | 코드와 실행에서 확인한 범위 | 남은 한계 |
|---|---|---|
| 실제 형식·손상 구별 | 확장자 대신 Pillow가 연 바이트 형식을 사용. PNG/JPEG의 metadata/verify/decode를 별도 객체로 구분하고 잘린 JPEG·CRC 주입 실패를 검사. 미인식 파일은 손상/코덱 미지원 원인을 단정하지 않는다. | 코덱 없는 실물 HEIC/RAW는 시험하지 않음. status ok는 전체 사양 준수 증명이 아님. |
| 날짜 의미·오프셋 | capture/digitized/modified가 구별되고 오프셋 없는 값을 UTC로 만들지 않는다. 최종 변경은 IFD0 DateTime의 ExifIFD OffsetTime/SubSecTime을 결합해 `2024-07-14T15:10:00.25Z`를 확인한다. 촬영일 대체에는 사용하지 않는다. | 실제 카메라 시간의 진실성·XMP/sidecar 우선순위는 범위 밖. |
| 회전 | 원시 orientation 1~8과 encoded/display 치수의 관계를 PNG/TIFF로 검사. 제공 TIFF는 8×6→6×8이고 원시8을 유지하여 중복 적용을 피한다. | 픽셀 렌더링 결과를 별도로 눈으로 비교하지 않았으며 API의 전달물은 치수/태그다. |
| 동일 바이트·후보 | 크기+SHA 후보 뒤 실제 메모리 바이트 비교를 수행한다. 메타데이터만 다른 같은 픽셀은 병합하지 않고 강제 해시 충돌도 분리한다. 후보에 원본 변경/대표 선택/목적지 명령이 없다. | 시각 유사도와 삭제 의사결정은 구현 목표에 포함하지 않음. |
| 원본 보호·반복 | `rb` 바이트 사본과 해시/메타데이터 동일 snapshot 연결. CLI 입력 안 출력·기존 출력 덮어쓰기 거절. 새 복제 환경의 반복 테스트와 작업 전후 원본 해시 통과. | 시간·파일ID 검사로 원자적 snapshot 보안을 보장하지 않는다. Windows symlink 생성 검증은 skip. |

직접 ExifRead 조사에서 찾은 `strict=True` 손상 JPEG 빈 결과 문제가 메인의 별도 디코딩 상태로 보완된다. `verify` 성공만으로 정상이라고 결론내리는 경로는 없다. 제한 초과는 정상 또는 손상으로 합쳐지지 않는다. 후보가 불확실한 정보를 갖는 경우 이유와 null 버킷을 보존한다.

## 자료와 실행 순서

이 디렉터리의 `project/`는 실제 원본 프로젝트와 독립적인 복제본이다. 복사한 것은 입력 디렉터리·manifest·sentinel, 메인의 코드3개/README/requirements/original-before뿐이며 기존 실험 출력이나 환경은 복사하지 않았다. 테스트가 복제본 안에서 fixtures/test-runs를 생성한다.

1. 원본 보존 기준을 `original-before-reproduction.json`에 읽기 기록하고 Copy-Item으로 상대 구조를 복제했다. 초기 복제 코드 해시는 `copied-code-sha256.json`이다.
2. 새 venv 생성 후 scoped `tmp`, `pip-cache`로 설치했다. 일반 sandbox 설치는 패키지 목록을 얻지 못해 실패했고, 동일 배정 범위의 권한 상승 재시도로 설치 성공했다. 이것을 Pillow 버전 부재로 기록하지 않았다.
3. 최초 27개 테스트 재현 뒤 메인의 IFD 수정 통보를 받아 세 코드만 다시 복제했다. 추가 수정은 하지 않았다. 변경 코드의 해시는 `copied-code-sha256-final.json`이다.
4. 최종 테스트와 CLI를 다시 실행했다. `project/.elenchus/lab/R001/main/independent-tests-final.log`, `independent-cli-final.log`, `independent-cli-report-final.json`이 최종 증거다. 이전 로그도 보존했다.
5. `audit_reproduction.py`가 원본/복제본/코드 해시와 CLI 출력 의미를 독립적으로 대조했다. IFD 수정 전후 제공 샘플 JSON은 완전히 같았다.

복제 project 루트에서 오프라인 재실행:

```powershell
& '.elenchus/lab/R001/main/.venv/Scripts/python.exe' -B '.elenchus/lab/R001/main/photo_materials.py' inputs --output '.elenchus/lab/R001/main/another-new-report.json'
Push-Location '.elenchus/lab/R001/main'
& '.venv/Scripts/python.exe' -B -m unittest -v test_photo_materials
Pop-Location
```

이미 존재하는 출력 이름은 사용하지 않는다. 설치 명령 및 도구 실행 요약은 이 폴더의 `activity.jsonl`과 담당 `records/metadata-activity.jsonl`에 있다. 최종 audit 당시 README에는 이전 27개 수치가 남아 있었고 메인이 갱신 예정이라고 알렸다. 이 보고서의 최종 28개 결과와 로그를 기준으로 삼는다. README 수치 갱신은 기능 코드 검증을 바꾸지 않으나 나중에 audit를 재실행하려면 해당 README 사본도 다시 맞춰야 한다.
