# R002 독립 탐색: 동일성의 층과 정리 후보의 불확실성

확인일: 2026-09-08, Windows / Python 3.12.10 / Pillow 12.3.0. 메인이 준 중립 brief로 시작했고 작성된 Topology/index를 후속 확인했다. 질문은 “동일 파일 판정과 정리 후보에 필요한 날짜·형식·회전 불확실성을 다른 문제분해와 인접 분야에서 어떻게 다루며 어디서 실패하는가?”다. 최종 화면·삭제 정책은 결정하지 않는다.

## 결론과 적용 조건

1. **바이트 동일성, 정규화된 픽셀 동일성, 시각 유사성은 별도 관계다.** 현재 요구의 동일 파일에는 `size → SHA-256 → 실제 바이트 비교`가 재현 가능한 근거다. 픽셀/유사 해시는 설명이 다른 선택적 후보 증거로 보존한다. 해시 종류·정규화 방법·도구 버전을 함께 기록해야 비교 의미가 유지된다.
2. **판정 가능 여부도 분리한다.** 손상 JPEG도 바이트 해시는 계산할 수 있다. 이는 사진을 정상 표시할 수 있다는 뜻이 아니다. 확장자, 파서가 식별한 형식, 디코딩 결과, 날짜 출처·원문·오프셋, 회전·표시 치수를 별도 필드로 연결한다. 정리 후보의 이유에는 누락·오류·충돌을 남기고, 날짜 없음에 파일시스템 시각을 촬영 날짜로 자동 대입하지 않는 것은 현재 목적에 맞는 에이전트 제안이다.
3. **큰 파일을 더 좋은 원본으로 확정하면 안 된다.** 실험에서 763-byte JPEG에 주석만 넣자 813 bytes가 되었으나 표시 픽셀은 완전히 같았다. 크기·메타데이터 수는 후보 순위의 신호로 쓸 수 있어도 품질 또는 보존 가치의 증명은 아니다.
4. **현재 기능 재료에 시각 유사성 구현을 강제할 근거는 없다.** 색·자세·크롭·인코딩·ICC·여러 프레임에 대한 기준이 있어야 확장할 수 있다. 이번 프로브는 정확한 바이트 그룹과 반례를 확보했고, 시각 후보 제품의 정확도·성능은 검증하지 않았다.

## 접근 비교와 실제 원문

`자료 설명`은 열린 공식 원문/소스에서 확인한 내용이고 `관찰`은 아래 로컬 실행 결과다. `추론`은 이번 기능에 적용하는 판단이다. GitHub master/main URL은 2026-09-08에 읽었으나 커밋을 고정하지 않았으므로 향후 재실행 시 변경될 수 있다.

| 접근 | 실제 근거와 설명 | 적용 조건·실패·판정 |
|---|---|---|
| 파일 목록과 바이트 해시 | [PhotoPrism Duplicate Detection](https://docs.photoprism.app/user-guide/library/duplicates/), 본문 Duplicate Detection / Related Files: SHA1과 크기를 비교하고, RAW+JPEG+XMP·원본/편집본 등 관련 파일은 별도 stack 관계다. **자료 설명.** | **추론:** 사진 라이브러리라는 단위가 파일 하나와 다를 수 있다. exact와 related를 섞지 않는 분해를 가져온다. 본문 Import의 move는 소스 삭제도 하므로 이번 실험에는 채택·실행하지 않았다. PhotoPrism 서버를 설치·관찰하지 않았다. |
| 후보 해시 후 직접 비교 | [rmlint Cautions](https://rmlint.readthedocs.io/en/master/cautions.html), Traversal Robustness / Collision Robustness / Unusual Characters: 해시 충돌, 겹친 경로, 링크 순회, 특수 파일명으로 오작동하는 재현 예와 바이트 비교의 비용을 설명한다. **자료 설명/공식 문서의 코드 예.** | **추론:** 크기·SHA-256 그룹은 비교량 축소에 쓰고 후보를 바이트로 확인한다. 겹친 입력 경로와 동일 파일 객체는 별도로 제거해야 한다. Junction은 아래 후속 실험에서 확인했고, hardlink·동시 수정은 이 독립 프로브에서 시험하지 않았다. 문서의 오래된 타 도구 사례를 현재 버전 전체의 결함으로 일반화하지 않는다. |
| content-addressed 구조 | [IPFS Content Identifiers](https://docs.ipfs.tech/concepts/content-addressing/), “CIDs are not file hashes” / “Same file, different CIDs”: CID는 구조·codec·chunking·알고리즘에도 의존한다. 동일 바이트라도 설정에 따라 CID가 다를 수 있다. **자료 설명.** | **추론:** 위치와 내용 식별자를 분리하는 개념은 재사용하되, 로컬 사진에 IPFS 네트워크를 도입할 필요는 없다. `sha256`와 전체 원본 바이트를 대상으로 한다는 계약을 명시한다. 다른 시스템의 CID를 그대로 파일 SHA와 비교하지 않는다. IPFS 실행·업로드 없음. |
| 정규화된 디코딩 픽셀 | [Pillow ImageOps 12.3](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose), [실제 소스](https://pillow.readthedocs.io/en/stable/_modules/PIL/ImageOps.html#exif_transpose): Orientation 2~8에 flip/transpose/rotate를 적용하고 적용한 태그를 제거한다. **자료 설명/소스 확인.** | **관찰:** orientation 6의 8×6 JPEG는 표시 6×8. 표시 정규화 PNG와 원래 JPEG는 바이트가 다르지만 정규화 픽셀 SHA가 같다. **추론:** 썸네일·표시 비교에는 유용하지만 메타데이터 차이를 지우므로 원본 파일 동일성으로 승격하지 않는다. ICC·알파·16-bit·프레임 보존 정책은 별도 필요하다. |
| perceptual hash | [ImageHash README](https://github.com/JohannesBuchner/imagehash), [실제 average_hash / phash 소스](https://github.com/JohannesBuchner/imagehash/blob/master/imagehash/__init__.py): 구조 해시는 주로 휘도, colorhash는 색 분포를 사용하며 다른 정보를 버린다. 확인한 소스에는 `__version__ = 4.3.2`가 있다. **자료 설명/소스 확인.** | **관찰:** 독립적으로 작성한 간단한 aHash 데모에서 빨강·파랑 단색 이미지가 같은 64-bit 값이지만 픽셀 SHA는 다르다. 이 실험은 ImageHash 패키지 실행 또는 pHash 정확도 시험이 아니다. **추론:** 유사 후보와 임계값 검토용이다. BSD-2-Clause 프로젝트임을 README에서 확인했으나 외부 코드는 복사하지 않았다. |
| ML 기반 검토 후보 | [Immich Duplicates Utility](https://docs.immich.app/features/duplicates-utility/), 2026-07-27 갱신 표기: 시각 유사성을 ML로 찾아 검토하고 크기·EXIF 수로 사전 선택한다. 보존 파일 수에 따라 메타데이터 동기화 여부가 달라진다. **자료 설명.** | **추론:** 후보 생성과 최종 보존 결정을 나누는 접근, 메타데이터 관계를 보존해야 한다는 문제 분해가 유용하다. 서버/모델 비용과 실제 사진 정확도는 미검증. 이번 목적에 서버를 도입하거나 사용자의 파일을 전송할 이유는 없다. |
| 날짜 해석의 원문 보존 | [ExifTool QuickTime 공식 소스 문서](https://github.com/exiftool/exiftool/blob/master/html/TagNames/QuickTime.html), 첫 설명: 사양의 UTC 규정과 실제 카메라의 local 저장이 다르므로 기본값은 시간대를 가정하지 않는다. `QuickTimeUTC` 설정은 해석을 바꾼다. **자료 설명.** | **추론:** 원시 날짜·태그 그룹·오프셋·해석 정책을 보존해야 한다. 태그 이름 하나의 우선순위로 모든 형식을 처리하면 안 된다. 현재 JPEG/PNG/TIFF 입력 관찰에 MOV/HEIC 정책을 실행했다고 주장하지 않는다. |

## 실행 실험과 실패 경험

입력은 `project/inputs`의 제공된 합성 자료 8개다. 원본은 읽기만 했고, 변형 5개는 이 작업장의 `fixtures/`에 생성했다. 원본 해시를 실행 전후 비교했으며 제공된 `project/inputs.sha256.json`의 모든 항목과도 일치했다. 이는 내용 불변 검사이며 운영체제 수준 읽기 전용 마운트의 증명은 아니다.

| 실제 관찰 | 판정/의미 |
|---|---|
| `copies/duplicate.jpg`, `session A/dated.jpg`: 각 763 bytes, SHA-256 `98be3ae374a8913faf97f323ae964374945f54b0aa296958a929fb90e0113491`, 직접 바이트 비교도 동일 | 제공 입력에 exact group 1개. 파일명·폴더명이 달라도 그룹 성립. |
| 위 두 JPEG의 DateTimeOriginal `2024:07:15 10:20:30`, OffsetTimeOriginal `+09:00`, Orientation 1 | 태그 값의 직접 관찰이다. 실제 촬영 사건의 진실을 검증한 것은 아니다. |
| `회전/rotated.jpg`: Orientation 6, 저장 8×6 → 표시 6×8, 날짜/오프셋 없음 | 회전으로 표시 치수가 달라짐. 날짜 없음과 회전 있음이 독립 상태. |
| `plain.png`: 정상 decode, 확인한 EXIF 날짜 없음. `formats/sample.tiff`: 정상 decode, IFD0.DateTime `2024:07:15 10:20:30` 있음, DateTimeOriginal 없음, Orientation 8, 저장 8×6 → 표시 6×8 | TIFF의 수정 시각 태그를 촬영 시각으로 승격하지 않는다. 형식·디코딩 성공이 촬영 날짜 존재를 보장하지 않음. |
| `broken/truncated.jpg`: 32 bytes, SHA 계산 성공, `OSError: Truncated File Read` | 바이트 식별과 이미지 유효성 분리. 텍스트 2개는 `UnidentifiedImageError`; 코드가 이를 출력에 보존. |
| **합성 변형** `jpeg_with_png_extension.png`: 원 JPEG와 바이트 동일, 파서는 JPEG로 판별 | 확장자는 형식 증명이 아님. 원본 입력에 실제 확장자 불일치가 있었다는 뜻은 아니다. |
| **합성 변형** `jpeg_with_comment.jpg`: JPEG COM 추가, 763→813 bytes, SHA 다름, 표시 픽셀 SHA 같음 | 메타데이터 수정·파일 크기 증가를 exact duplicate 또는 화질 향상으로 처리할 수 없음. |
| **합성 변형** `normalized_rotated.png`: 원 회전 JPEG와 SHA 다름, 표시 픽셀 SHA 같음 | 시각 기준 정규화는 별도 동일성. 픽셀 비교에는 RGB8·치수·EXIF 정규화라는 명시적 정책을 사용함. |
| **합성 변형** `solid_red.png`, `solid_blue.png`: 다른 RGB 픽셀, aHash 데모는 모두 `0000000000000000` | 휘도 대비를 줄인 해시의 정보 손실 반례. “같은 aHash”를 “같은 파일”로 판단하지 않음. |

첫 실행 실패를 실제로 조사하고 수정했다. PNG에서 `getexif()` 다음 `verify()`를 호출하자 정상 PNG 네 개를 모두 손상처럼 보고했다. JPEG는 같은 순서로 통과했다. [Pillow PNG 실제 소스](https://github.com/python-pillow/Pillow/blob/main/src/PIL/PngImagePlugin.py)의 `verify()`는 파일 포인터가 닫혔으면 `RuntimeError: verify must be called directly after open`을 낸다. 메타데이터 읽기와 검증의 순서 문제였으며 PNG 데이터 손상이 아니었다. `open→verify→close`, 새 `open→load→getexif`로 분리해 정상 PNG가 모두 통과했다. 실패 당시 보고서는 `observations-first-failed.json`, 재현한 잘못된 순서는 최종 보고서 `wrong_order_png_failure`에 남겼다. 수정 후 13개 확인 항목이 통과했다.

도구 접근 실패도 별도다. 기본 `python -I -B`에는 Pillow가 없어 `ModuleNotFoundError`였다. 메인이 설치한 R001의 별도 venv를 실행 허용받아 사용했고, 내 작업에서는 전역 설치나 다른 작업장 수정이 없다. ExifTool 문서의 원 도메인/`www` 본문 열기는 도구 Internal Error였고, 같은 공식 저장소의 HTML 소스로 대체하여 UTC 설명 본문을 확인했다. 공식 원문을 못 읽은 검색 snippet을 결론 근거로 남기지 않았다.

## 재현 방법·재료

프로젝트 루트에서 PowerShell:

```powershell
& '.\.elenchus\lab\R001\main\.venv\Scripts\python.exe' -I -B '.\.elenchus\lab\R002\identity-research\probe_identity.py' --inputs '.\inputs'
```

Pillow 12.3.0을 제공하는 다른 Python으로도 실행할 수 있다. `-I -B`는 사용자 Python 설정과 bytecode 쓰기 부수효과를 줄인다. 출력 위치는 스크립트 옆으로 고정되고 입력 안에 출력하는 경우 거부한다.

- `probe_identity.py`: 원본 읽기, SHA와 바이트 그룹, 디코딩/EXIF 관찰, 합성 반례 생성, 확인 항목을 실행하는 독립 코드.
- `observations.json`: 최종 관찰·체크·원본 해시·잘못된 PNG 호출 순서 재현.
- `observations-first-failed.json`: 수정 전 실제 실패. 정상 PNG를 오류 처리했으므로 이 파일의 decode 판정을 현재 결론으로 사용하지 않는다.
- `fixtures/`: 5개 합성 변형. 원본 사용자의 사진이 아니라 제공된 합성 입력에서 파생하거나 단색으로 생성했다.
- `records/identity-activity.jsonl`: 시각·웹 검색/원문 경로·명령·결과의 작업 기록.

## 후속 독립 검토와 Windows Junction 실험

메인의 `R001/main/photo_materials.py`와 `sample-report-final.json`을 읽고 `review_main.py`로 직접 실행·대조했다. 검토한 메인 코드 SHA-256은 `263c4e70a5d638e4667b03c5fe87d4f0cbc6f06120304d7b52ee6631541d50be`이며 실행 전후 동일했다. 메인 코드나 보고서를 수정하지 않았다.

검토 과정에서 **내 프로브의 TIFF 기록 오류**도 바로잡았다. 기존 코드는 TIFF `load()` 뒤에 Orientation을 읽어 원래 8이었던 태그를 누락으로 기록하고, 라이브러리가 보고한 표시 치수 6×8을 저장 치수라고 기록했다. 실제 원시 TIFF 태그는 Orientation 8, ImageWidth 8, ImageLength 6이다. `getexif()`와 TIFF 256/257 태그를 `load()` 전에 보존하도록 내 코드만 수정했다. 이전 결과는 `observations-before-tiff-correction.json`에 보존했다. IFD0.DateTime은 이전 JSON에도 있었으므로 “EXIF 날짜 없음”이라는 notes의 포괄 문구 역시 DateTimeOriginal 없음으로 정정했다.

수정 후 독립 프로브 13개 확인을 다시 통과했고, 메인과 비교하는 후속 확인 15개가 통과했다. 입력 8개에 대한 파일 크기·SHA-256·형식·저장/표시 치수·회전·정상 여부와 exact group에 차이가 없었다. 변형 5개의 형식·디코딩·표시 치수도 메인의 `inspect_bytes()`와 일치했다. 두 날짜 JPEG만 `ExifIFD.DateTimeOriginal` 출처로 `2024-07-15`에 들어가며 TIFF/PNG/회전 JPEG에 촬영 날짜를 자동 대입하지 않는다. TIFF의 IFD0.DateTime은 `dates`에 보존되지만 `capture`로 사용되지 않는다. 모든 후보는 `review_only`다.

Windows Junction은 내 작업장 안 `junction-fixtures/source/linked-target`에서 형제 폴더 `junction-fixtures/target`으로 연결되도록 일반 PowerShell `New-Item -ItemType Junction`으로 실제 생성했다. source에는 직접 marker 1개, target에는 별도 marker 1개를 두었다. 권한 상승이나 symlink 재승인은 요청하지 않았다.

- Junction의 `lstat().st_file_attributes`는 1040으로 Directory+ReparsePoint였다.
- 메인의 `scan_directory(source)`는 `direct.txt`와 `linked-target` 두 행만 냈다. Junction 행은 `skipped_link`, target marker 경로는 결과에 없었다.
- Junction 자체를 입력 root로 주면 `ValueError: input root must not be a symlink or reparse point`로 거부했다.
- target marker의 내용 해시는 실행 전후 동일했다. 만든 Junction과 fixture를 삭제·이동하지 않고 남겼다. Junction은 작업장 내부만 가리킨다.

기존 Junction fixture가 있는 상태에서 프로젝트 루트의 재현 명령:

```powershell
& '.\.elenchus\lab\R001\main\.venv\Scripts\python.exe' -I -B '.\.elenchus\lab\R002\identity-research\review_main.py' --main-lab '.\.elenchus\lab\R001\main'
```

새 위치로 복사하여 Junction이 보존되지 않았으면 `junction-fixtures/source/linked-target`을 같은 작업장 `junction-fixtures/target`으로 가리키게 `New-Item -ItemType Junction -Path <source/linked-target> -Target <target>`로 만든 뒤 실행한다. 경로를 옮기지 않은 현재 fixture에서는 생성 명령을 반복할 필요가 없다. 상세 결과는 `main-review.json`에 있다. 이는 Windows Junction의 실제 성공이며 권한이 없던 symbolic link 생성 시험과 다르다. 다른 reparse point 종류나 공격적인 동시 교체 전체의 안전성을 증명한 것은 아니다.

## 범위·미검증·탐색 종료 이유

사진 도구의 바이트 exact / ML 후보, 범용 dupefinder, content-addressed 구조, 픽셀 정규화, perceptual hash, 날짜 해석까지 서로 다른 접근을 확인했다. 자료의 설명을 현재 도구 실행으로 확대하지 않았고, 이 질문의 선택을 바꾸는 “파일 동일성과 유사성의 혼동”, “형식/날짜/회전의 독립성”, “정상 PNG의 잘못된 오류 판정”을 실제 반례로 해소했다. 추가 제품 비교는 현재 exact-group 재료 결론을 바꿀 효용이 낮다.

이 독립 프로브에서 미검증: 실제 카메라 EXIF의 신뢰도·HEIC/RAW/MOV, ICC·알파·16-bit·다중 프레임 보존, 대량 성능, 유사 사진 정확도와 임계값, 해시 충돌 주입, Junction 외 NTFS 링크·겹친 경로·입력 동시 수정. 메인의 별도 시험 결과는 메인 R 문서와 구분해 읽는다. 프로브는 작은 파일을 메모리에 읽고 정적인 합성 입력을 대상으로 하므로 대용량 스캐너나 삭제 도구로 그대로 쓰지 않는다. 바이트 비교 알고리즘의 동작은 확인했지만 동시 변경 중 일관된 snapshot을 보장하지 않는다. 삭제·이동·업로드는 실행하지 않았다. 최종 후보 스키마·이유 표현·UI와 보존 순위는 메인 통합 및 후속 제작자의 선택으로 남긴다.
