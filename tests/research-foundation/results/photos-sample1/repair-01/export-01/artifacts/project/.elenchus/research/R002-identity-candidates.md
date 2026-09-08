# Research R002: 동일 파일의 증거를 정리 후보에 어떻게 연결하는가?

- 상태: 확정
- 판정: 결론 가능 — 동일 바이트 파일과 비파괴 검토 후보 재료
- 기준: [Topology](../topology.md), 메타데이터는 [R001](R001-metadata-reliability.md)에 의존.

## 질문·달성 기준

동일 파일·같은 표시 픽셀·시각적 유사성을 혼동하지 않고 작은 입력의 복사본을 찾을 수 있는가? 해시 후보의 실제 바이트 확인, 동일 복사본1쌍, 메타데이터만 다른 변형의 미병합, 결정적 검토 JSON·원본 불변·오류 처리·재실행을 실제 검증한다. 대표 보존 파일·삭제/이동·목적지·최종 동선은 정하지 않는다.

## 다른 접근의 비교

| 접근과 근거 | 이번 적용·비적용 |
|---|---|
| [PhotoPrism](https://docs.photoprism.app/user-guide/library/duplicates/)의 SHA1+크기 exact와 RAW/JPEG/XMP 관련 파일 stack 구분 | 위치·같은 파일·관련 파일을 분리하는 개념을 재사용. 해당 서버/이동 기능은 실행하지 않았다. |
| [rmlint 공식 cautions](https://rmlint.readthedocs.io/en/master/cautions.html)의 파일 별칭·경로 중복·해시 충돌 실패 | size+SHA256는 비교 후보, 이후 실제 bytes 비교. 하나의 root를 입력받고 하드링크는 별칭, reparse point는 skip. 문서의 과거 타 도구 실패를 현재 제품 전체에 일반화하지 않는다. |
| [IPFS CID](https://docs.ipfs.tech/concepts/content-addressing/)의 codec/chunking/알고리즘 포함 식별 | 콘텐츠 주소 아이디어는 참고하되 로컬 바이트 SHA256과 CID를 동일시하지 않는다. 네트워크 저장 불필요, 실행/업로드 없음. |
| [ImageHash](https://github.com/JohannesBuchner/imagehash)와 [Immich ML 후보](https://docs.immich.app/features/duplicates-utility/) | 서로 다른 정보를 버리는 유사성·검토 후보의 대안. 이번 원본 동일 판정에 대입하지 않는다. 서버/모델·ImageHash 패키지 성능은 미검증. |
| Pillow EXIF 정규화 후 픽셀 비교 | 표시/변환 재료로 유효하지만 인코딩·메타데이터 의미가 달라 원본 동일 증거로 삼지 않는다. |

상세 원문 위치·관찰·비교·사용 조건은 독립 조사자의 [notes](../lab/R002/identity-research/notes.md)에 있다. 메인은 PhotoPrism/rmlint/Immich 원문을 재확인하고 로컬13개 확인 결과 및 자기 코드의 byte collision 테스트를 대조했다. 같은 프로젝트 재인용과 조사자 동의를 별도 독립 원천으로 세지 않았다.

## 실제 확보한 반례와 코드

제공 입력 `copies/duplicate.jpg`와 `session A/dated.jpg`는 각763bytes, SHA256 `98be3ae374a8913faf97f323ae964374945f54b0aa296958a929fb90e0113491`이며 실제 bytes도 같다. 이름·경로가 달라도 exact group1이다. 손상 JPEG도 해시가 생기므로 정상 표시 여부는 다른 필드다.

조사자의 새 합성 변형에서 JPEG COM 주석 추가는763→813bytes와 다른 SHA를 만들었으나 표시 픽셀이 같았다. 더 큰 파일을 좋은 원본으로 고를 근거가 아니다. JPEG의 이름만 `.png`로 바꿔도 실제 형식은 JPEG이고 바이트는 같다. 회전 정규화 PNG는 원 JPEG와 바이트가 다르지만 정규화 픽셀이 같다. 독립 작성 aHash 데모의 빨강/파랑 단색 충돌은 시각 해시를 동일 파일 판정에 쓰지 말아야 하는 반례이며 ImageHash 패키지를 실행한 것은 아니다.

`photo_materials.py`는 크기 제한 안의 파일을 메모리 스냅샷으로 읽어 metadata·hash·bytes 비교에 같은 관찰 바이트를 사용한다. file ID/mtime/size 전후 검사와 읽기 오류 상태를 보존한다. 해시 충돌을 인위적으로 주입해도 바이트가 다른 파일은 그룹에서 분리한다. 원자적인 OS snapshot·악의적인 동시 수정을 완전히 막는 구현은 아니다.

검토 후보는 파일마다 date_bucket/source/exact_group/review_reasons/action을 반환한다. `action=review_only`는 실행 행동이 없다. 유효한 Original의 **현지 날짜**만 날짜 후보로 쓰며 UTC 일자 경계 테스트를 통과했다. 촬영일 없거나 충돌하면 빈 bucket과 이유를 남긴다. 회전 태그·손상·확장자 불일치·같은 파일 그룹을 동시에 표현하므로 하나의 상태 때문에 다른 증거를 잃지 않는다.

후속 사용자 결정은 정확한 내용 동일성·애매한 날짜 보류·Windows 로컬 실행·사람의 검토 출력이다. 기존 JSON을 [review.md](../lab/R001/main/review.md)로 변환하는 `render_review.py`를 더했다. 두 JPEG만2024-07-15 날짜 후보이며 TIFF 수정일 등 나머지 근거/보류 이유도 노출한다. 두 텍스트와 손상 파일은 각각 비이미지/미지원·손상 판정의 한계를 보존한다. `probe_local_review.py`의12항목은 Python socket 생성/연결/DNS 진입점을 막은 상태에서 core scan+render 재실행·판정 JSON 동일·원본 불변과 합성 초 미만 날짜의 근거 표시를 확인했다. 설치 이후 실행은 로컬이며 OS 수준 네트워크 차단 보장으로 과장하지 않는다. 최종 화면/동선·대표파일/삭제 규칙을 추가하지 않았다.

독립 좁은 검토는 초기 Markdown의 날짜 근거에서 `subsecond_raw`가 보이지 않는 점을 실제 `modified-offset.jpg`로 재현했다. JSON에는 보존됐지만 사람이 보는 정보가 줄어든 문제였다. renderer에 조건부 `subsec` 원문 표시를 더했고9자리 초 미만 합성 fixture 확인을 추가했다. 제공된8개 입력에는 초 미만 태그가 없어 기존 검토 결과 내용은 바뀌지 않았다.

## 실제 실패·복구와 테스트

- 최초 Windows 스캔은 모든 입력을 changed_during_read로 오판했다. 삼자 stat 비교에서 DirEntry의 st_dev/st_ino=0, Path.stat/fstat는 실제 값이었다. [Python3.12 공식 문서](https://docs.python.org/3.12/library/os.html#os.DirEntry.stat)의 Windows 조건을 확인하고 `path.lstat()`로 수정했다. 실패 출력 `sample-report.json`는 보존했다.
- 실제 하드링크 생성 시험은 같은 파일 별칭으로 분류하고 duplicate 그룹을 만들지 않았다. Windows 심볼릭 링크 생성은 WinError1314로 skip하며 지원했다고 보고하지 않는다. Windows junction은 조사자 소유 작업장 내 실제 생성했고 child skip·target 미순회·junction 입력 root 거부를 확인했다. [main-review.json](../lab/R002/identity-research/main-review.json)의 메인/독립 결과 비교 포함15항목이 모두 통과했다.
- 한글/공백 경로, 빈 입력, 읽기 실패·스캔 중 변경 주입, 크기/픽셀/프레임 상한, CLI 입력안 쓰기/기존 출력 덮어쓰기 거부, 동일 JSON 재실행과 원본 해시 검증을 포함한다. 최종 메인28개 중27통과·1skip이며 날짜/디코딩 항목은 R001과 공유한다.

## 재료·판정·남은 선택

[실행 README](../lab/R001/main/README.md), `sample-report-final.json`, 메인 코드·테스트·생성 fixture와 [독립13항목 실험](../lab/R002/identity-research/notes.md)을 인계한다. 원본8개와 기존 sentinel/manifest2개는 baseline 해시를 보존한다. 대용량 처리/DB/유사 사진 정확도/대표파일 순위/편집본과 sidecar 관계/실제 카메라·HEIC/RAW는 미검증이다. 제품의 화면과 전체 사용 동선은 이후 제작자가 정한다.

파일 동일·표시 동일·시각 유사·관련 파일의 주요 대체 접근과 실패를 비교했고 실제 작은 자료의 동일 그룹과 반례를 확인했다. 후보 이유와 바이트 증거를 더 정확히 만들 중요한 열린 충돌이 이 범위에는 남지 않았다. 새로운 제품 소개를 늘리는 것보다 실제 추가 형식/규모 입력이 있을 때 재개하는 편이 의미 있다. 범위를 축소해 실패를 성공으로 바꾸지 않았으며, 자원 제한·도구권한 skip·미검증 영역은 그대로 전달한다.
