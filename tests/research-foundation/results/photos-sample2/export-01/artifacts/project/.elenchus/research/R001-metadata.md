# R001: 형식·날짜·방향·손상 입력의 메타데이터
- 상태: 확정
- 기준: ../topology.md
- 환경: Windows, Python 3.12.10, 2026-09-08

## 질문·달성 조건
메타데이터 추출과 이미지 디코드는 어떤 차이가 있으며, 날짜와 방향의 정보를 잃거나 확실성을 과장하지 않으려면 어떤 데이터가 필요한가? 공식 원문과 최소 두 실제 추출 접근을 비교한다. 입력 전체를 실행하고, 날짜 누락·잘못된 값·시간대·회전·손상을 추가 합성 fixture로 검증한다. 테스트에 실제 입력과 주입 fixture를 구분한다.

## 조사 준비
직접 해법은 메타데이터 전용 파서·범용 이미지 디코더·외부 도구로 비교한다. 작은 샘플이 대표하지 못하는 형식은 미검증으로 남긴다. Web 발견 단서: Pillow lazy open/verify, ExifTool read mode/date tags. 결정적 본문은 별도 확인한다. metadata_options agent가 독립 직접 해법 조사를 담당한다.

## 현재 재료
실험 작업장: ../lab/R001/ (메인), ../lab/R001/agent_metadata/ (조사자 전용).

## 접근 비교와 직접 근거
| 접근 | 확인 수준·적용 차이 | 이번 재료에 대한 판단 |
|---|---|---|
| 이미지 디코더와 메타데이터 API | [Pillow Image 문서](https://pillow.readthedocs.io/en/stable/reference/Image.html)의 open/verify/load 계약 및 [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html)의 EXIF 방향 적용을 본문 확인. 12.3.0을 실제 설치·실행. | 형식 식별·태그 읽기·픽셀 디코딩·방향 반영을 연결하는 실험 주재료. 메타데이터 반환만으로 파일 정상 판정 불가. |
| 메타데이터 전용 파서 | [ExifRead 공식 저장소](https://github.com/ianare/exif-py)의 process_file, IFD별 태그 이름, strict 계약을 확인. 3.5.1 실제 실행. | 디코드를 생략하는 다른 접근. Pillow와 교차 비교용 재료를 남김. 빈 dict/strict 성공은 이미지 정상이나 날짜 유효성을 뜻하지 않음. |
| 범용 외부 CLI | [ExifTool 공식 명령 소스](https://raw.githubusercontent.com/exiftool/exiftool/master/html/exiftool_pod.html)의 읽기·JSON·그룹·fast 옵션 확인. 공식 master 소스는 13.59이나 설치/실행하지 않음. | 더 넓은 태그·형식·그룹을 원하는 후속 개발의 대안. 외부 런타임 배포와 프로세스 관리가 필요. 문서 확인을 실행 성공으로 계산하지 않음. |

실행 버전은 requirements와 결과 JSON에 고정했다. Pillow MIT-CMU, ExifRead BSD-3-Clause 라이선스를 공식 자료와 설치본에서 확인했다. ExifTool은 Perl과 같은 Artistic/GPL 조건의 후보이며 이번 코드에 복사·포함하지 않았다. 홈페이지 fetch 실패/403은 공식 GitHub 원문 및 SourceForge의 동일 프로젝트 문서로 보완했다. 같은 원천의 미러를 독립 근거로 세지 않는다.

## 실제 입력 결과
입력 8개 모두 스캔, JPEG 3개·PNG 1개·TIFF 1개 디코드 성공. 제공된 32바이트 JPG는 Pillow open에서 `Truncated File Read`, 텍스트와 README는 미식별이다. 자세한 결과: [original-scan-verified.json](../lab/R001/results/original-scan-verified.json).

- dated.jpg와 duplicate.jpg의 날짜는 IFD0가 아닌 ExifIFD에 있었다. DateTimeOriginal `2024:07:15 10:20:30`과 OffsetTimeOriginal `+09:00`으로 UTC `2024-07-15T01:20:30+00:00`을 만들었다. 태그가 없는 PNG·회전 JPEG에 파일명/mtime 기반 촬영 시각을 채우지 않았다.
- sample.tiff에는 IFD0 DateTime만 있다. 이는 촬영 시각과 구별해 보존했다. [ExifTool EXIF 태그 원문](https://exiftool.sourceforge.net/TagNames/EXIF.html)의 0x0132, 0x9003, 0x9004, 0x9010–12가 날짜 의미·동반 offset을 구분한다. 이 확인으로 IFD0 DateTime의 offset을 ExifIFD에서 읽도록 보완했다.
- TIFF 저장 IFD 크기는 8×6, open 크기는 6×8이고 Orientation=8이다. load 뒤에는 Orientation이 제거됐다. JPEG Orientation=6은 load 뒤에도 남아 `exif_transpose`로 6×8이 된다. [Pillow TIFF 소스](https://pillow.readthedocs.io/en/stable/_modules/PIL/TiffImagePlugin.html)의 `_setup`과 `load_end`를 메인이 재확인했다. 로드 전 방향을 따로 보존하고 로드 후 최신 EXIF로 방향을 적용한다.

## 반증·수정·검증
| 관찰/실패 | 원인·대안 | 확보한 검증 |
|---|---|---|
| JPEG 후미 20B 절단 주입 시 태그와 verify는 성공, load는 실패 | 태그 읽기/컨테이너 검사/실제 픽셀 디코드는 별개 | 별도 세 상태와 오류 단계를 출력, 손상 입력으로 후보 분리 |
| ExifRead strict가 제공 32B 손상 입력을 빈 dict로 반환 | strict는 유효하지 않은 태그 처리 옵션이며 이미지 전체 검증 아님 | 독립 파서 비교 결과에 빈 dict와 Pillow 오류를 함께 보존 |
| 잘못된 달력 날짜를 두 파서가 그대로 반환 | 파서는 태그 해석, 날짜 의미 검증은 별도 | 월/일·서식·offset·소수초를 파싱; 잘못된 값·시간대 없음·충돌을 검토 사유로 보존 |
| PNG 이름의 JPEG 또는 JPG 이름의 PNG | 확장자는 내용 형식을 보장하지 않음 | 바이트 기반 형식과 확장자 불일치 경고 |
| TIFF 저장 시 중첩 Image.Exif 객체의 fp 오류(독립 fixture 생성) | bytes EXIF로 직렬화 후 저장 | 독립 fixture 6개와 수정 시행착오 보존 |
| sandbox 패키지 설치 실패 | 제한된 네트워크 환경 | 동일 lab venv·캐시 범위로 권한 재시도해 설치 성공 |

메인 29개 주입 fixture, 독립 메타데이터 fixture 6개는 제공 원본과 별도 출처로 표시했다. 메인 테스트 22개 중 날짜·8방향의 실제 픽셀 위치·손상·형식·다중 프레임 항목이 이 질문을 판정한다. [최종 테스트 로그](../lab/R001/results/tests-final.txt). 메타데이터 독립 조사자 코드를 `replay_metadata/`로 복제해 다시 실행했고 제공+주입 14개 행, 태그/verify/load 결과와 방향, 원본 해시를 대조했다. [대조 결과](../lab/R001/results/independent-replay-checks.json).

## 판정·미검증
판정: **결론 가능**. 형식·날짜·방향·손상에 필요한 작동 재료와 재현 가능한 반례를 확보했다. 직접 해법·메타데이터 전용 대안·운영 실패를 비교했으며 핵심 원문과 실제 실행의 적용 범위를 구분했다. 추가 소개문 수집보다 실제 카메라/새 형식 자료가 있어야 다음 결론이 달라진다.

HEIC/RAW, MakerNotes·XMP/IPTC·sidecar의 의미 충돌, 전체 TIFF 압축 조합, 실제 사진/대량 성능, 적대적 입력의 프로세스 격리는 미검증이다. EXIF 태그의 진실성과 시간대 없는 값의 실제 지역도 알 수 없다. 첫 프레임 메타데이터와 최대 32프레임 디코드라는 재료의 한계를 명시한다. ExifTool 실행은 미검증으로 유지한다.

코드·실행·제약·재사용 의미는 [인계 README](../lab/R001/README.md)에 연결했다. 특정 라이브러리를 최종 제품의 필수 조건으로 고정하지 않는다.
