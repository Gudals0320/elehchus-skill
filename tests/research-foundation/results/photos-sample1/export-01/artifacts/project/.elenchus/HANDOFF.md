# 다음 개발자를 위한 사진 기능 재료

Elenchus 세션 완료. 사용자가 연구 결과와 남은 한계를 확인하고 현재 재료·결론으로 종료했다. 아래 실행 범위·미검증·후속 제작자의 선택은 그대로 보존한다.

현재 범위의 작동 재료를 확보했다. 메타데이터·형식/디코딩 상태를 읽고, 동일 바이트 그룹과 이유가 있는 검토 후보 JSON을 만든다. 제공 원본은 삭제·이동·수정하지 않았고, 사용자 화면·전체 동선·대표 파일 보존 정책은 정하지 않았다.

후속 사용자 기준도 반영했다. 먼저 [사람이 읽는 검토 결과](lab/R001/main/review.md)에서 날짜별 후보·동일 그룹·원시 Orientation/표준 해석/실제 표시 치수를 확인할 수 있다. 날짜 없는 파일을 강제로 배정하지 않는다. [로컬 실행 확인](lab/R001/main/local-review-results.json)은 기존 의존성으로 Python 네트워크 진입점을 막은 상태에서12개 연결 확인 통과·네트워크 호출0·원본10개 불변을 기록한다. 설치 뒤 분석/결과 생성에는 외부 서비스·로그인·비밀키가 필요 없다. 독립 검토에서 발견한 Markdown 날짜 근거의 초 미만 원문 누락도 수정하고 합성 fixture로 확인했다.

[후속 독립 재현](lab/R001/metadata-research/reproduction/local-review-notes.md)도 기존 별도 venv에서12/12와 별도6개 audit를 통과했다. 초 미만25/123456789의 실제 표시, 원본/복제10개 불변, 원래 core SHA 유지까지 확인했다. 추가 설치·네트워크 호출은 없었다.

먼저 [실행 README](lab/R001/main/README.md)의 명령으로 재현한다. 주요 모듈은 [photo_materials.py](lab/R001/main/photo_materials.py), 시험은 [test_photo_materials.py](lab/R001/main/test_photo_materials.py), 실제 결과는 [sample-report-final.json](lab/R001/main/sample-report-final.json)이다. 코드·고정 버전 요구 파일·원본8개·추가 합성 fixture·실패 출력이 프로젝트 안에 있다. `.venv`와 cache는 전달 필수 자료가 아니며 재구성 가능하다.

| 목표 | 확보한 증거와 재료 |
|---|---|
| 메타데이터/형식 | Pillow12.3.0과 ExifRead3.5.1 실제 입력 비교. JPEG/PNG/TIFF 정상5개, 손상1개, 비이미지/미지원2개를 분리. [R001](research/R001-metadata-reliability.md). |
| 날짜/회전/손상 | EXIF 날짜 출처·local/UTC·오프셋·누락/오류를 보존. 촬영일 없는 TIFF 수정일을 자동 대체하지 않음. 1~8 회전 치수, 잘못된 날짜/오프셋, PNG CRC/JPEG EOI, 다중 프레임 변형 확보. |
| 동일 파일/후보 | SHA256+크기 후보의 실제 byte 비교로763byte 복사본1쌍 확인. 사진이 닮거나 픽셀이 같아도 원본 byte가 다르면 병합하지 않음. 검토 이유·현지 촬영 날짜 bucket·exact group만 제시. [R002](research/R002-identity-candidates.md). |
| 재실행/원본 보존 | 메인28개 중27통과·symlink1skip. [최신 테스트 로그](lab/R001/main/tests-ifd-final.log). 하드링크 및 별도 junction 실제 확인. 입력8개와 기존 sentinel/manifest2개의 해시 검사. |

시행착오의 핵심은 API 호출이 성공한 것과 사진이 정상인 것을 구분하는 일이다. ExifRead strict도 잘린 JPEG에 빈 태그를 주며 JPEG verify는 EOI가 빠져도 통과했다. PNG에서 metadata 뒤 verify는 오히려 정상 파일을 오류로 만들었다. TIFF는 이미 회전한 파서 크기를 다시 회전하면 틀리고 load 뒤에 태그를 읽으면 원시 Orientation이 사라질 수 있다. Windows DirEntry의0파일ID와 오류 메시지 메모리주소는 각각 전체 입력 변경 오판과 재실행 비교 실패를 만들었다. 수정 전 결과와 수정 후 테스트를 모두 남겼다.

[독립 메타데이터 조사](lab/R001/metadata-research/notes.md), [독립 동일성 실험](lab/R002/identity-research/notes.md), [15항목 통합 대조](lab/R002/identity-research/main-review.json)는 서로 다른 접근의 근거·재현·한계를 담는다. ExifTool/exif/PhotoPrism/Immich/IPFS/ImageHash는 문서 또는 원문 코드 비교이며 호스트에서 해당 제품을 실행한 것으로 보고하지 않는다.

[새 환경 독립 재현](lab/R001/metadata-research/reproduction/notes.md)은 별도 프로젝트 복제·새 venv 설치 후 최종28테스트 중27통과·1skip, 같은 CLI 결과를 확인했다. [audit](lab/R001/metadata-research/reproduction/audit-results.json)의 원본10파일·복제본·핵심 코드 SHA가 일치하며 최종 메인 코드 SHA는 `263c4e70a5d638e4667b03c5fe87d4f0cbc6f06120304d7b52ee6631541d50be`다. 메인은 audit를 읽고 실제 코드 해시와 다시 대조했다. 실행 후 바뀐 README의 테스트 수·junction·보존 검사 안내는 문서 보완이다.

후속 제작자는 임시 스키마·함수/폴더 이름·저장소/캐시·병렬 처리·화면을 재구성할 수 있다. 보존해야 할 것은 사용자 원본 보호 조건과 동일 byte/표시 픽셀/유사 사진 구분, 날짜 출처/불확실성, 오류를 숨기지 않는 동작이다. 파일당16MiB·총64MiB·누적20M픽셀·64프레임은 연구 구현의 한도이며 대량 성능 보장이 아니다. HEIC/RAW·실물 카메라·고급 MakerNote/sidecar·색/알파/고비트 의미·유사도 정확도·동시 변경의 원자적 snapshot은 검증하지 않았다.

라이선스는 각 채택 배포본 고지를 유지한다. Pillow12.3의 실제 LICENSE는 MIT-CMU와 번들 의존성별 조건, ExifRead3.5.1은 BSD-3-Clause다. 자료는 로컬에만 남겼고 외부 게시·업로드·개인 사진/계정/유료 서비스 사용은 없다. 실행자 공개 활동은 작업 루트 `records/activity.jsonl`와 조사자별 activity 파일에 기록한다. 전체 host trace나 숨겨진 추론이 아니다.
