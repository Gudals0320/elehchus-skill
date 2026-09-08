# Research R001: 형식·날짜·회전·손상 입력을 어떤 증거로 읽는가?

- 상태: 확정
- 판정: 결론 가능 — 작은 JPEG/PNG/TIFF 자료에 대한 기능 확보 범위
- 기준: [Topology](../topology.md). 조사일 2026-09-08, Windows/Python3.12.10/Pillow12.3.0/ExifRead3.5.1.

## 질문과 달성 기준

메타데이터가 비어 있으면 정상 이미지인지 알 수 있는가, 촬영 날짜·수정 날짜·오프셋을 어떻게 구분하는가, 회전과 형식별 디코딩이 다른 점은 무엇인가? 두 실제 라이브러리 실행, 제공 입력 전체 관찰, 누락/오류/회전/손상 변형, 재현 가능한 읽기 모듈·테스트를 요구했다. 최종 UX와 모든 실물 카메라 지원은 요구하지 않았다.

## 비교와 직접 근거

| 접근 | 자료 설명과 실제 실행 | 이번 판단 |
|---|---|---|
| Pillow | [Image12.3](https://pillow.readthedocs.io/en/stable/reference/Image.html)의 `open`은 lazy, `verify`는 전체 픽셀 디코딩이 아니다. 메인에서 8개 입력의 metadata/verify/load를 실제 실행했다. [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose)는 EXIF 변환 후 태그를 제거한다. | 이미지 디코딩과 표시 치수까지 필요한 기본 재료로 채택. EXIF IFD별 날짜는 직접 정규화하며 고급 MakerNote/sidecar 처리는 미포함. 설치본 LICENSE는 MIT-CMU와 번들 의존성별 고지를 담는다. 코드 복사 없이 공개 API 사용. |
| ExifRead3.5.1 | 독립 조사자가 strict 두 모드로 입력8개 실행. 메인이 32byte truncated JPEG에서 strict=True 결과 `{}`를 직접 재확인했다. [공식 process_file](https://raw.githubusercontent.com/ianare/exif-py/master/exifread/__init__.py)은 초기 InvalidExif에서도 빈 사전을 반환한다. | 디코딩과 별개의 메타데이터 파서 비교 재료를 유지. 빈 태그 결과를 정상·손상·EXIF 없음으로 단정하지 않는다. BSD-3-Clause 조건과 고정 설치 방법은 [조사 notes](../lab/R001/metadata-research/notes.md)에 있다. |
| ExifTool | [공식 README](https://raw.githubusercontent.com/exiftool/exiftool/master/README), [CLI](https://raw.githubusercontent.com/exiftool/exiftool/master/html/exiftool_pod.html), [EXIF 코드](https://raw.githubusercontent.com/exiftool/exiftool/master/lib/Image/ExifTool/Exif.pm)의 형식/JSON/태그 의미를 확인했다. 본 사이트 403 뒤 GitHub raw를 사용했다. | 넓은 형식·태그 진단의 외부 프로세스 대안. 현재 실행은 미검증이며 다음 형식 확대 시 비교할 근거를 남긴다. 별도 배포/Perl·라이선스·Unicode 경로 시험이 필요. |
| exif 패키지 | 독립 조사자가 [공식 문서](https://exif.readthedocs.io/en/latest/index.html)의 속성식 읽기/쓰기 API와 저자 유지 여력 고지를 확인했다. | 원본 읽기와 디코딩 연결에 더 직접적인 두 파서를 시험했으므로 이번 채택은 보류. 실행 성공을 주장하지 않는다. |

독립 질문은 `metadata_sources`(직접 라이브러리)와 `identity_alternatives`(대체 접근/실패)에 새 맥락 `fork_turns=none`으로 배정했다. 메인은 관련 원문·결과와 자기 실행을 합쳤다. 역할상 작업 범위이며 OS 격리로 표현하지 않는다. 외부 UI의 기능을 주장하는 연구가 아니므로 계정/브라우저 관찰은 사용하지 않았다.

## 실제 입력 결과

| 입력 | 확인한 결과 |
|---|---|
| dated.jpg와 duplicate.jpg | JPEG8×6, EXIF Original `2024:07:15 10:20:30`, `+09:00`, UTC `2024-07-15T01:20:30Z`, Orientation1. 두 파서 일치. |
| rotated.jpg | JPEG 저장8×6, Orientation6, 표시6×8. 촬영 날짜 없음. 한글 경로 정상. |
| sample.tiff | 태그 저장8×6, Orientation8. Pillow 최초 reported/표시 크기6×8. IFD0 DateTime은 있으나 Original 촬영 날짜는 없음. |
| plain.png | PNG8×6 정상 디코딩, EXIF 촬영 날짜 없음. |
| truncated.jpg | 입력 자체가 제공된 손상 사례. Pillow 식별에서 `Truncated File Read`, ExifRead는 strict 두 모드 모두 빈 태그. |
| README.md·notes.txt | Pillow 미식별, ExifRead 빈 태그+경고. 미지원/비이미지와 손상을 서로 섞지 않는다. |

코드의 촬영 날짜는 메타데이터 선언일 뿐 실제 촬영 사건을 검증한 것은 아니다. 원문·source·offset·subsecond·local·UTC·status를 보존한다. 오프셋 누락 시 UTC=null, 잘못된 날짜/오프셋과 IFD 상충은 검토 이유다. DateTime/DateTimeDigitized/mtime를 자동으로 촬영일로 바꾸지 않는다. IFD0 DateTime은 ExifIFD OffsetTime/SubSecTime과 짝짓되 의미는 modified로 남는다.

## 시행착오와 수정

1. 초기 PNG `getexif→verify`가 정상 입력도 RuntimeError로 보고했다. [버전 고정 PNG 소스](https://github.com/python-pillow/Pillow/blob/12.3.0/src/PIL/PngImagePlugin.py)의 verify 조건을 확인하고 metadata·verify·load를 각각 별도 메모리 open으로 분리했다. 실패 프로브를 보존했다.
2. TIFF는 파서 자체의 회전 때문에 raw 태그8×6과 최초 파서 치수6×8이 다르다. [12.3 TIFF 소스](https://github.com/python-pillow/Pillow/blob/12.3.0/src/PIL/TiffImagePlugin.py)와 실제 회전1~8 PNG/TIFF 치수 테스트를 대조했다. 태그를 load 전에 보존하고 `exif_transpose` 후 실제 표시 치수를 사용한다. 조사자의 load 후 Orientation 누락도 수정됐다.
3. 합성 JPEG EOI2byte 제거는 verify 통과/load 실패했다. 합성 PNG CRC 훼손도 검출했다. 제공 손상 파일과 새 주입 실패를 구분했다.
4. 새 테스트에서 오류 문자열의 BytesIO 주소 때문에 재실행 JSON 비교가 실패했다. 식별 오류 메시지를 일정한 문구로 바꿨다. `tests-first.log`에 실패를, `tests-ifd-final.log`에 최종 결과를 남겼다.
5. 설치는 sandbox 네트워크 WinError10013 후 허용된 로컬 venv/cache 범위 권한 상승으로 성공했다. ExifRead 설치본은 sandbox에서 namespace import로 오인됐으며 배정 deps를 읽는 scoped 상승 재실행에서 정상3.5.1 및 `{}`를 확인했다. 파서 결함과 도구 접근 오류를 분리한다.

## 재료·재현·판정

[main/README](../lab/R001/main/README.md), `photo_materials.py`, `generate_fixtures.py`, `test_photo_materials.py`, `sample-report-final.json`, `original-before.json`; 비교 파서는 [metadata-research](../lab/R001/metadata-research/notes.md). 테스트는 총28개 중27통과·Windows symlink 생성1skip이며 R002 통합 항목도 포함한다. 실제 하드링크와 별도 junction 검증은 R002에 있다. 초기 실패 출력은 현재 결론과 구분해 남겼다.

독립 조사자가 문서와 코드만 새 프로젝트·새 venv로 복제해 재현했고 최종28개 중27통과·1skip, 같은8개 입력 결과를 확인했다. [재현 notes/audit](../lab/R001/metadata-research/reproduction/notes.md)의 최종 코드 SHA를 메인 실제 파일과 재대조했다. 원본10파일과 복제본 내용도 일치했다.

후속 사용자가 회전 값과 해석을 구분해 달라고 확인했다. [검토 출력](../lab/R001/main/review.md)은 JPEG Orientation6=시계90도, TIFF8=반시계90도라는 표준 해석과 실제 저장/최초파서/표시 치수를 분리한다. '원시값'은 최초 메타데이터 조회 값으로 명시했다. PNG는 조회 내부에서 load될 수 있어 모든 형식이 디코딩 전에 읽혔다고 단정하지 않는다. 형식/날짜 판정코드를 변경하지 않고 설명 재료를 보완했다.

직접 해법·속성 API·외부 CLI와 형식별 실패를 비교했고, 현 입력의 판단을 바꾸는 PNG 순서·TIFF 회전·빈 EXIF/손상 혼동을 실제로 해소했다. 추가 후보 소개가 이 범위의 결론을 바꿀 가능성은 작다. 광범위 형식 지원은 다음 입력을 확보해야 확인된다. HEIC/RAW/실물 카메라/고급 메타데이터·ICC·대량 성능을 테스트 통과 범위로 확대하지 않는다. 파일당16MiB/총64MiB/누적20M픽셀/64프레임의 소규모 구현이며 자원 초과는 별도 결과다. 연구 자료와 실행은 확보했으며 세션 자체의 결과 검토·종료는 공통 지침을 따른다.
