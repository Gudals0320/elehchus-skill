# 날짜·방향·형식 메타데이터 연구 결과

확인 시각: 2026-09-08 UTC. 질문: 로컬 합성 JPEG·PNG·TIFF 및 손상 입력에서 날짜·방향·형식 메타데이터를 안정적으로 읽을 실제 라이브러리/도구 접근은 무엇인가?

## 후보별 직접 근거와 실험 범위

| 접근 | 공식 본문/버전/라이선스 | 실제 적용 범위와 실패 조건 |
|---|---|---|
| Pillow 이미지 파서와 EXIF API | 실행 12.3.0, Python 3.12.10. [Image API](https://pillow.readthedocs.io/en/stable/reference/Image.html), [형식 문서](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html), [12.3.0 release](https://pillow.readthedocs.io/en/stable/releasenotes/12.3.0.html), [MIT-CMU 라이선스](https://pillow.readthedocs.io/en/stable/about.html#license) | `Image.open`은 지연 로딩이며 이미지 식별/메타데이터와 픽셀 디코딩은 별개다. `getexif()`의 IFD0와 `get_ifd(0x8769)`의 ExifIFD를 함께 읽는다. 실제 JPEG/PNG/TIFF의 날짜·방향을 읽었고 확장자가 PNG인 JPEG를 JPEG로 판정했다. `verify`만으로 JPEG 후미 손상을 검출하지 못했다. |
| ExifRead 메타데이터 전용 파서 | 실행 3.5.1. [공식 저장소 README](https://github.com/ianare/exif-py), [PyPI 3.5.1](https://pypi.org/project/ExifRead/3.5.1/). BSD-3-Clause, pure Python/no dependencies라는 프로젝트 설명 | `process_file(open(path,'rb'), details=False, strict=...)`로 읽었다. JPEG/PNG/TIFF EXIF 지원을 실제 확인했다. `strict`는 손상 파일 전체나 날짜 달력 검증을 보장하지 않는다. 제공된 32바이트 truncated JPEG는 기본/strict 모두 빈 dict를 반환했다. 비이미지/EXIF 없는 PNG도 빈 dict가 가능하여 빈 결과만으로 파일 상태를 확정할 수 없다. |
| ExifTool 별도 CLI/Perl 모듈 | [공식 저장소](https://github.com/exiftool/exiftool), [원문 소스의 VERSION](https://raw.githubusercontent.com/exiftool/exiftool/master/lib/Image/ExifTool.pm), [공식 명령 설명 원문](https://raw.githubusercontent.com/exiftool/exiftool/master/html/exiftool_pod.html). 확보된 master 소스 VERSION은 13.59. 실행/최신 릴리스 검증은 하지 않았다. 라이선스는 Perl과 동일 조건(Perl Artistic 또는 GPL) | 문서/소스는 JPEG·PNG·TIFF를 지원하고 JSON·태그 그룹·기계용 숫자 방향을 제공한다. 원천이 다른 같은 이름 태그는 그룹을 유지해 충돌을 다뤄야 한다. CLI와 설치된 런타임 배포 부담이 추가된다. JSON 숫자/문자열 자동 형변환, 같은 JSON 이름의 중복 억제를 문서가 명시한다. `-fast`는 일부 후미 메타데이터 탐색을 생략한다. 현재 환경에 ExifTool 명령은 없었으며 실행 결과를 주장하지 않는다. |

메타데이터 전용 파서는 픽셀 디코딩을 피하는 별도 접근이며, 이미지 파서와 조합하면 형식 식별 및 디코딩 상태를 독립 기록할 수 있다. 특정 라이브러리 채택이나 제품의 날짜 우선순위는 확정하지 않았다. ExifTool의 폭넓은 메타데이터 처리와 Python 내부 함수 호출의 설치/호출 비용은 선택 조건이다. 대규모 성능 비교는 하지 않았다.

## 실제 결과

`probe_results.json`에 제공 입력 8개(이미지 6개 중 손상 JPEG 1개, 문서/텍스트 2개)와 새로 주입한 fixture 6개가 있다. 원본 8개 SHA256 전후가 모두 동일하다. 역할별 폴더 경계와 사후 해시 확인이며 기술적 격리의 증거로 표현하지 않는다.

| 입력/조건 | 실제 관찰 |
|---|---|
| dated.jpg / duplicate.jpg | 두 파서가 ExifIFD DateTimeOriginal `2024:07:15 10:20:30`, OffsetTimeOriginal `+09:00`, IFD0 Orientation 1을 읽음. IFD0만 순회하면 날짜를 놓침. |
| plain.png | Pillow가 PNG/8×6 및 빈 EXIF를 반환, load 성공. ExifRead는 EXIF 없음 메시지와 빈 dict. 날짜 없는 정상 이미지. |
| sample.tiff | IFD0 DateTime `2024:07:15 10:20:30`, Orientation 8. DateTimeOriginal/OffsetTimeOriginal은 없음. 두 날짜 태그를 같은 출처 의미로 합치면 안 됨. |
| rotated.jpg | Orientation 6, 날짜 없음. Pillow open/load 크기 8×6 → exif_transpose 6×8. |
| 제공 truncated.jpg(32B) | Pillow open/verify/load 모두 OSError. ExifRead 기본/strict는 오류 없이 빈 dict. |
| 주입 nested_date.jpg/png/tiff | 세 형식에서 두 파서 모두 중첩 DateTimeOriginal/OffsetTimeOriginal/Orientation을 읽음. |
| 주입 JPEG 후미 20B 절단 | 두 파서 메타데이터 읽기 성공, Pillow verify도 성공. Pillow load에서 `image file is truncated (9 bytes not processed)` 오류. 메타데이터 상태와 디코딩 상태를 분리해야 하는 직접 반례. |
| 주입 invalid_date.png | `2020:99:99 99:99:99`가 두 파서와 ExifRead strict에서 그대로 반환됨. 날짜 유효성은 별도 파싱 조건. |
| JPEG 바이트/.png 확장자 | Pillow format은 JPEG. 파일명 확장자를 실제 형식으로 쓰면 불일치. |

## TIFF 방향 후속 확인

Pillow 12.3.0의 sample.tiff는 open 직후 size 6×8, IFD width/height 8×6, Orientation 8이다. load 이후 size 6×8을 유지하며 Orientation이 사라진다. load 후 exif_transpose와 open 직후 exif_transpose 모두 6×8이다. load 결과와 transpose 결과 픽셀 SHA256도 `5187ed28218cd37820f346d48c22569499ba6cca49ddabec1b703c2e7ac90241`로 동일해 이 입력에서 이중 회전이 없음을 확인했다.

[공식 TiffImagePlugin 소스](https://pillow.readthedocs.io/en/stable/_modules/PIL/TiffImagePlugin.html)의 `_setup`은 Orientation 5–8의 표시 크기를 교환하고, `load_end`는 `ImageOps.exif_transpose(self, in_place=True)`를 거쳐 Orientation을 제거한다. [공식 ImageOps 소스](https://pillow.readthedocs.io/en/stable/_modules/PIL/ImageOps.html)의 `exif_transpose`는 먼저 `load()`를 수행한 후 최신 EXIF Orientation을 조회한다. 따라서 미리 저장한 TIFF 방향 값으로 수동 회전을 다시 적용하는 접근은 별도 주의가 필요하다. 원본 태그가 필요하면 load 전 값을 기록해야 한다. 전체 TIFF 압축/프레임/방향 조합의 검증으로 확대하지 않는다.

## 실제 실패와 수정

- 일반 sandbox pip 설치는 WinError 10013으로 실패했다. 같은 독립 venv/캐시/임시 경로를 유지한 승인된 네트워크 재시도에서 Pillow 12.3.0과 ExifRead 3.5.1 설치에 성공했다.
- 새 `Image.Exif()` 객체에 중첩 ExifIFD dict를 직접 넣어 TIFF로 저장할 때 `AttributeError: 'Exif' object has no attribute 'fp'`가 발생했다. 공식/로컬 TIFF 소스에서 bytes 입력은 Exif.load를 거치는 것을 확인하고 `exif=exif.tobytes()`로 바꾼 뒤 JPEG/PNG/TIFF fixture 생성 및 읽기가 모두 성공했다. 이는 fixture 생성 경로의 오류이고 원본 읽기 실패가 아니다.
- exiftool.org 루트는 403, pod/tag 경로는 도구 fetch 실패. 공식 GitHub와 raw.githubusercontent.com의 동일 프로젝트 원문으로 보완했다. GitHub/raw/ExifTool 홈페이지는 독립 출처 여러 개로 세지 않는다.

## 재현과 범위

실행은 [README](README.md), 고정 패키지는 `requirements.txt`, 실행 파일은 `probe_metadata.py`, 실제 결과는 `probe_results.json`이다. 메인 검증자는 해당 폴더에서 `.venv/Scripts/python.exe probe_metadata.py --inputs ../../../../inputs`로 다시 실행할 수 있다. 재실행은 이 작업장의 fixture/보고서만 갱신하고 입력을 읽기 모드로 연다.

이 결과는 작은 합성 JPEG/PNG/TIFF와 명시한 손상 주입에 한정된다. 실제 카메라 MakerNotes·XMP/IPTC 충돌·HEIC/RAW·전체 다중 프레임·대량 처리·적대적 파일의 자원 제한·ExifTool 실행은 미검증이다. 안정적인 재료를 위해 원시 태그/출처/읽기 오류/디코딩 오류를 구별해야 한다는 사실까지 확보했다. 최종 날짜 우선순위, UX, 도구 채택은 후속 제작자의 선택으로 남긴다.

직접 해법 세 계열, 디코딩과 분리한 메타데이터 전용 접근, 실제 손상/태그 위치/방향/확장자/날짜 유효성 실패 조건을 확인했다. 이 작은 입력의 도구 후보 비교에 필요한 직접 근거는 확보되어, 추가 라이브러리 소개문 수집보다 상위 연구의 통합 재현이 다음 유효 단계다.
