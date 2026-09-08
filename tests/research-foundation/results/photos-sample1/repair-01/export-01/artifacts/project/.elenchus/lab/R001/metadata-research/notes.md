# R001 직접 메타데이터 해법 조사

확인일: 2026-09-08. 담당: metadata_sources. 범위는 로컬 사진의 형식·촬영일·회전 읽기이며 최종 UX와 원본 변경은 결정하지 않았다. 읽은 자료는 배정된 skill 지침과 project 입력·현재 topology/index, 설치한 의존성뿐이다. 최초 release 확인은 메인이 수행한 것을 재사용했다.

## 결론

ExifRead는 작은 Python 메타데이터 읽기 재료로 실행 가능하다. 그러나 빈 태그 사전만으로 정상/손상/EXIF 없음 상태를 분류할 수 없다. ExifTool은 형식 확장과 태그 계열별 진단이 필요할 때 비교할 외부 CLI 후보다. 이 연구에서는 ExifRead만 실행했으며 ExifTool과 exif의 현재 호스트 실행 성공을 주장하지 않는다. 형식 식별과 픽셀 디코딩 검증은 메타데이터 추출과 별도로 연결해야 한다는 판단은 아래 실행의 결과다.

## 접근 비교와 공식 근거

| 접근 | 확인한 자료 설명·코드 | 적용 조건과 판단 |
|---|---|---|
| ExifRead 3.5.1 | [PyPI 배포 문서](https://pypi.org/project/ExifRead/)는 순수 Python, 런타임 의존성 없음, TIFF/JPEG/JPEG XL/PNG/WebP/HEIC/RAW 지원을 명시한다. `process_file()`은 IFD가 포함된 이름의 태그 사전을 돌려준다. [공식 소스](https://raw.githubusercontent.com/ianare/exif-py/master/exifread/__init__.py)는 `ExifNotFound`/`InvalidExif`에서 strict 여부와 무관하게 빈 사전을 반환한다. | Python 3.12.10에서 3.5.1 직접 실행. 필요한 태그에만 집중하려면 `details=False, extract_thumbnail=False`; 이는 MakerNote/썸네일을 생략하는 선택이다. BSD-3-Clause; 설치 배포본 LICENSE 원문까지 읽음. 소스/바이너리 재배포 시 저작권·조건·면책 유지와 저자명 홍보 제한을 지켜야 한다. 이미지 정상 여부·촬영일 의미 검증을 대신하지 않는다. |
| ExifTool | [공식 README](https://raw.githubusercontent.com/exiftool/exiftool/master/README)는 Perl 모듈/CLI 및 JPEG/TIFF/PNG/HEIC/HEIF/여러 RAW 형식과 EXIF/IPTC/XMP/MakerNote 지원을 명시한다. [CLI 원문](https://raw.githubusercontent.com/exiftool/exiftool/master/html/exiftool_pod.html)의 `-j`, `-G`, `-n`, `-config` 설명을 확인했다. | JSON으로 별도 프로세스 경계에서 연결 가능. 현재 PATH에 없었으므로 실행 비교는 미검증. Perl 런타임 또는 적합한 Windows 배포본을 준비하고 Unicode 파일명 처리를 검증해야 한다. README의 재사용 조건은 Perl Artistic License 또는 GPL. 통합할 배포본의 해당 라이선스를 유지해야 한다. |
| exif Python 패키지 | [공식 문서](https://exif.readthedocs.io/en/latest/index.html)는 `Image`, `has_exif`, 속성 접근으로 읽기/수정을 제공한다. 동시에 저자가 현재 유지보수에 쓸 수 있는 시간이 줄었다고 직접 고지한다. [PyPI 배포 메타데이터](https://pypi.org/project/exif/)의 최신 표시는 1.6.1(2024-12-10), Python >=3.7, MIT License다. | 속성 기반 읽기 API는 후보지만 현재 요구가 원본 읽기 중심이고 ExifRead의 실험을 우선했다. 형식 전 범위·배포본 라이선스 원문·실행은 여기서 검증하지 않았으므로 재사용 채택으로 분류하지 않는다. |

PyPI와 GitHub의 ExifRead 설명은 같은 프로젝트의 원천이며 독립 출처로 이중 계산하지 않는다. 검색에서 발견한 구형 [Read the Docs](https://exif-py.readthedocs.io/en/latest/)는 Python 2.6/2.7/3.2~3.4를 나열해 현 배포 문서와 차이가 있었으므로 설치된 3.5.1 코드/PyPI를 기준으로 삼았다. [공식 ChangeLog](https://github.com/ianare/exif-py/blob/master/ChangeLog.rst)의 3.5.1은 MakerNote 오류가 strict=False일 때 예외로 나가지 않게 변경했다고 설명하며, 3.3.0에는 HEIC box 처리 오류 수정 기록이 있다. 지원 형식 표를 모든 실물 카메라 파일의 성공 보장으로 볼 수 없다.

## 실제 실행 결과

실행: `python project/.elenchus/lab/R001/metadata-research/probe_exifread.py` (sample 작업 루트에서). Python 3.12.10, ExifRead 3.5.1. 전체 결과는 `probe-results.json`, 실행 코드는 `probe_exifread.py`에 있다. 메타데이터를 쓰지 않고 입력을 `read_bytes()`로 읽은 뒤 메모리 `BytesIO` 사본만 파서에 전달했다. 입력 8개 모두 제공된 SHA-256과 일치했고 전후 해시가 같았다. 이 해시 검사는 내용 불변 확인이며 OS 수준 격리의 증명은 아니다.

| 실제 입력 | strict=False와 strict=True 공통 결과 |
|---|---|
| session A/dated.jpg, copies/duplicate.jpg | Orientation 원시값 `[1]`; DateTimeOriginal `2024:07:15 10:20:30`; OffsetTimeOriginal `+09:00`. 두 입력의 바이트 SHA-256도 동일. |
| 회전/rotated.jpg | Orientation 원시값 `[6]`, 문자열 `Rotated 90 CW`; 촬영 날짜 태그 없음. 한글 경로 읽기 성공. |
| formats/sample.tiff | Orientation `[8]`, 폭/높이 태그 8×6, Image DateTime `2024:07:15 10:20:30`. DateTimeOriginal 없음. |
| plain.png | 빈 사전, `PNG file does not have exif data.` 경고. 이것만으로 PNG의 픽셀 정상 여부를 검증한 것은 아님. |
| broken/truncated.jpg | 32바이트 입력에서 빈 사전, WARNING도 없음. strict=True도 예외를 내지 않음. 이 파일은 제공된 손상 fixture이며 새로 주입한 손상 사례가 아님. |
| notes.txt, README.md | 빈 사전과 `File format not recognized.` 경고. |

의미상 경계는 [ExifTool 공식 EXIF 태그표](https://raw.githubusercontent.com/exiftool/exiftool/master/html/TagNames/EXIF.html)에서 교차 확인했다. `0x9003 DateTimeOriginal`은 원본 촬영 날짜이고, `0x0132`는 ExifTool 이름 ModifyDate/EXIF 이름 DateTime이다. `OffsetTimeOriginal`은 DateTimeOriginal의 오프셋이다. 따라서 TIFF의 Image DateTime을 촬영일로 이름만 바꾸면 안 된다. Orientation의 1~8은 회전뿐 아니라 반전도 포함하며 6은 90 CW, 8은 270 CW이다. 이 실험은 변환된 픽셀이나 표시 치수를 계산하지 않고 태그만 보존한다.

## 시행착오와 재현

1. 일반 sandbox에서 PyPI 설치가 WinError10013 네트워크 거부로 실패했다. 마지막의 `No matching distribution` 문구를 패키지/버전 부재로 해석하지 않았다. 공식 PyPI 본문에서 3.5.1과 wheel을 확인했다.
2. 같은 배정 작업장에 `--target deps`와 `--cache-dir pip-cache`, TEMP/TMP=`tmp`를 지정한 네트워크 권한 상승 재시도로 설치 성공. 이후 일반 sandbox는 해당 설치 파일 읽기를 ACL로 거부하여 설치본 소스 읽기와 실행만 같은 배정 범위에서 권한 상승했다. 자동 승인 거절은 없었다.
3. ExifTool 본 사이트의 홈/CLI/EXIF 표 접근은 internal error 또는 403으로 본문 확보 실패. 공식 GitHub raw README·CLI·EXIF 표의 공개 대체 경로로 실제 본문을 확보했다. 검색 snippet은 최종 주장의 근거로 사용하지 않았다.
4. `strict=True`이면 손상 구분이 될 것이라는 기대는 실제 truncated fixture에서 반증됐다. 공식 `process_file`의 초기 오류 처리와 일치한다. 이 결과를 오류·빈 결과를 구별하는 통합 모듈 설계에 전달했다.

새 환경에서 `bootstrap.ps1`은 같은 폴더 아래 의존성/캐시/임시 경로만 사용한다. `requirements.txt`의 wheel SHA-256은 공식 PyPI 파일 상세에 게시된 `e5426ce2857423ad401e575ea9d159dc97449dc041fb6e61b35109caea72c311`이다. hash 고정 bootstrap도 실행하여 exit 0을 확인했다. 이미 설치된 target 경고가 있었으며, 이를 빈 환경의 재설치 검증으로 확대하지 않는다. 설치 후 아래 명령은 외부 연결 없이 실행 가능하다.

```powershell
python -B project/.elenchus/lab/R001/metadata-research/probe_exifread.py
```

`deps`, `pip-cache`, `tmp`는 재구성 가능한 환경이며 핵심 전달물은 probe 코드·결과·설치 절차·이 문서다. 입력 `inputs/` 및 `inputs.sha256.json`가 있어야 동일 재현이 된다. 결과 시각은 실행마다 달라진다.

## 남은 범위와 종료 근거

JPEG/PNG/TIFF의 작은 합성 입력에 대한 실행 비교 재료와 중요한 실패 조건은 확보했다. HEIC/RAW/JPEG XL/WebP, 실제 카메라 MakerNote, 대량 성능, 픽셀 디코드, 전체 회전 1~8 및 날짜가 잘못된 변형은 이 담당자의 직접 검증 범위 밖이다. 메인의 변형/디코딩 검증과 통합해야 R001 전체 달성 여부를 판단할 수 있다.

추가 후보 소개를 늘려도 현재 샘플에서 빈 메타데이터 결과를 어떻게 다룰지라는 결정은 바뀌기 어렵다. 공식 도구·가벼운 Python 읽기·속성 기반 읽기/쓰기 접근과 실패 이력을 비교했으며, 최종 UI/라이브러리 고정은 남겨 둔다. 실제 입력 형식이 넓어지면 ExifTool 실행 비교를 다시 여는 것이 유효하다.
