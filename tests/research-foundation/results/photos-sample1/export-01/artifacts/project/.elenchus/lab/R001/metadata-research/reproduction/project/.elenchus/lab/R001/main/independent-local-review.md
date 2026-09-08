# 로컬 사진 검토 결과

입력 항목 8개 · 동일 내용 그룹 1개 · 분석기 Pillow 12.3.0

이 문서는 검토용 결과다. 파일 삭제·이동·병합 명령이나 보존할 대표 파일 선택은 포함하지 않는다. 원본 바이트가 같다는 판정과 비슷한 사진이라는 판단은 별개다.

## 날짜별 정리 후보

날짜는 유효한 DateTimeOriginal의 현지 날짜를 사용했다. 파일명·파일 시스템 시각·수정일을 촬영일로 대체하지 않았다. 시간대가 없으면 UTC를 추정하지 않으며, 충돌/해석 실패는 날짜 미지정으로 남긴다.

### 2024-07-15

| 파일 | 날짜 근거 | 검토 이유 | 동일 그룹 |
|---|---|---|---|
| copies/duplicate.jpg | ExifIFD.DateTimeOriginal &#91;촬영&#93; = 2024:07:15 10:20:30; offset=+09:00; 상태=offset&#95;known | 다른 경로의 파일과 내용이 정확히 같음 | exact-001 |
| session A/dated.jpg | ExifIFD.DateTimeOriginal &#91;촬영&#93; = 2024:07:15 10:20:30; offset=+09:00; 상태=offset&#95;known | 다른 경로의 파일과 내용이 정확히 같음 | exact-001 |

### 날짜 미지정

| 파일 | 날짜 근거 | 검토 이유 | 동일 그룹 |
|---|---|---|---|
| README.md | 날짜 메타데이터 미확인 | 비이미지 또는 현재 파서 미지원 | — |
| broken/truncated.jpg | 날짜 메타데이터 미확인 | 이미지 식별·구조 검사 또는 디코딩 실패 | — |
| formats/sample.tiff | IFD0.DateTime &#91;수정&#93; = 2024:07:15 10:20:30; offset=없음; 상태=timezone&#95;unknown | 촬영 날짜 태그 없음; 표시를 위한 회전/반전 해석 있음 | — |
| notes.txt | 날짜 메타데이터 미확인 | 비이미지 또는 현재 파서 미지원 | — |
| plain.png | 날짜 태그 없음 | 촬영 날짜 태그 없음; 회전 태그 없음; 방향을 촬영 사실로 확정하지 않음 | — |
| 회전/rotated.jpg | 날짜 태그 없음 | 촬영 날짜 태그 없음; 표시를 위한 회전/반전 해석 있음 | — |

## 동일 파일 그룹

파일 크기·SHA-256 후보를 실제 바이트 비교로 확인했다. 그룹 안에서 어느 파일을 보존할지는 선택하지 않았다.

### exact-001

각 763 bytes · 근거: sha256&#95;and&#95;equal&#95;bytes

SHA-256: 98be3ae374a8913faf97f323ae964374945f54b0aa296958a929fb90e0113491

- copies/duplicate.jpg
- session A/dated.jpg

## 회전 원시값과 해석·실행 결과

원시값은 최초 메타데이터 조회에서 얻은 값이다. 표준 해석은 그 값이 지시하는 변환이며 실제 표시 치수는 디코딩 후 EXIF 정규화를 실행해 얻었다. PNG의 메타데이터 조회는 내부 디코딩을 유발할 수 있고, TIFF는 파서가 이미 회전할 수 있어 변환을 수동으로 중복 적용하지 않았다. 치수만으로 화상 내용이나 촬영 당시 방향의 진실을 증명하지 않는다.

| 파일 | 형식 | 읽은 Orientation | 표준 해석 | 저장 치수 | 최초 파서 치수 | 실제 표시 치수 | 디코딩 |
|---|---|---|---|---|---|---|---|
| copies/duplicate.jpg | JPEG | 1 | 정방향 (변환 없음) | 8×6 | 8×6 | 8×6 | passed |
| formats/sample.tiff | TIFF | 8 | 반시계 방향 90도 회전 | 8×6 | 6×8 | 6×8 | passed |
| plain.png | PNG | — | 태그 없음 | 8×6 | 8×6 | 8×6 | passed |
| session A/dated.jpg | JPEG | 1 | 정방향 (변환 없음) | 8×6 | 8×6 | 8×6 | passed |
| 회전/rotated.jpg | JPEG | 6 | 시계 방향 90도 회전 | 8×6 | 8×6 | 6×8 | passed |

## 오류·미검증

| 파일 | 확인 상태 | 오류 단계/내용 |
|---|---|---|
| README.md | non&#95;image&#95;or&#95;unsupported | identify: UnidentifiedImageError — cannot identify image from byte snapshot |
| broken/truncated.jpg | invalid&#95;image | identify: OSError — Truncated File Read |
| notes.txt | non&#95;image&#95;or&#95;unsupported | identify: UnidentifiedImageError — cannot identify image from byte snapshot |

검증 범위는 제공된 작은 합성 JPEG·PNG·TIFF와 손상 입력, 연구 작업장의 명시적 합성 변형이다. HEIC·RAW·실제 카메라 원본·대량 사진 정확도/성능은 검증하지 않았다. 설치된 의존성을 사용한 분석과 이 문서 생성은 로컬에서 실행된다. 최종 화면·동선·저장소 설계는 이후 제작자의 선택이다.
