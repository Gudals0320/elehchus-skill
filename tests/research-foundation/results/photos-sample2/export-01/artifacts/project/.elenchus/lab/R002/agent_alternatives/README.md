# 동일성·변경·날짜의 대안 분해와 반증 재료

확인 시각: 2026-09-08 UTC. 역할에 할당된 중립 질문은 같은 사진 파일을 알아내고 정리 후보의 근거를 만드는 다른 접근과 실패 조건이다. 메인의 후보·제품 선택은 전제하지 않았다. 아래 기능 계약과 제안은 최종 UX나 자동 삭제 정책이 아니다.

실행 환경은 Windows 11 10.0.26200, Python 3.12.10, Pillow 11.3.0이다. 작업장 전용 `.venv`, `.cache`, `.tmp`를 사용했다. 입력은 `project/inputs`의 개인 자료 없는 합성 파일 8개이며, 사본과 새 변형만 실험했다. 파일 소유권을 나눈 역할 경계이며 기술적 격리라고 주장하지 않는다. 다른 작업·대화·평가 자료를 읽지 않았다.

## 결론과 선택 조건

| 접근 | 직접 근거·실제 관찰 | 가져올 요소 / 실패·제약 |
|---|---|---|
| 바이트 일치 확인 | [fdupes confirmmatch.c](https://raw.githubusercontent.com/adrianlopezroche/fdupes/master/confirmmatch.c)는 읽은 버퍼의 길이와 내용을 비교한다. 메인 재검토에서 명시적 ferror 검사는 확인되지 않았으므로, 읽기 오류 처리까지 확인했다는 초안 표현을 정정했다. [README](https://github.com/adrianlopezroche/fdupes)는 기본 hard-link 구분, symlink 관련 실패 및 byte confirmation 생략 옵션을 설명한다. | 해시/크기는 후보를 줄이는 인덱스로, 실제 바이트 비교는 관찰 시점의 강한 일치 근거로 재사용 가능. 이 실험의 상수 해시 충돌은 주입한 prefilter 실패이며 SHA-256 충돌을 만든 것이 아니다. fdupes 실행 파일은 설치·실행하지 않았다. |
| 디코딩된 픽셀 일치 | [Pillow 11.3.0 ImageOps 코드](https://raw.githubusercontent.com/python-pillow/Pillow/11.3.0/src/PIL/ImageOps.py)의 `exif_transpose`는 Orientation에 따라 전치한다. 메타데이터가 다른 PNG는 다른 바이트/같은 RGBA였고 Orientation6 PNG와 물리회전 PNG는 정규화 후만 같았다. | 표현 형식·방향을 명시한 파생 근거로 유용. 이번 계약은 8-bit RGBA이며 ICC 변환 없음. 멀티프레임 TIFF의 첫 프레임만 같아도 뒤 프레임은 다를 수 있다. RAW 현상·ICC·HDR·16-bit 보존의 일치 의미는 별도 검증 필요. |
| 지각 해시 / 근접 검색 | [ImageHash README](https://github.com/JohannesBuchner/imagehash)와 [버전 4.3.2를 선언하는 공개 코드](https://raw.githubusercontent.com/JohannesBuchner/imagehash/master/imagehash/__init__.py)의 average/difference/perceptual 방법은 휘도 구조를 사용한다. 독립 소형 aHash 구현으로 빨강/파랑 단색은 거리 0, JPEG 품질95→65 재인코딩도 거리 0이나 픽셀은 달랐다. | 편집·압축 변형 후보 발견에 적합하지만 거리 0도 동일 파일·픽셀의 증명이 아니다. 실제 8×8 이미지 3개에서 거리 (A,B)=1, (B,C)=1, (A,C)=2여서 threshold1 유사 관계는 추이적이지 않았다. 연결성분 전체를 동등한 중복으로 해석하면 잘못된 묶음이 된다. 실사진 threshold·정확도는 미검증. ImageHash 패키지를 직접 실행한 것은 아니며 알고리즘을 독립 구현했다. |
| 파일 ID와 경로 별칭 | [Windows hard links 문서](https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions)는 동일 볼륨의 여러 경로가 한 파일을 참조하고 변경이 공유됨을 설명한다. 새 파일에 `os.link`를 수행해 samefile=true, nlink=2, 한 경로의 쓰기가 다른 경로에 보이는 것을 관찰했다. | 경로 수와 독립 파일 수를 분리한다. hard-link 경로마다 저장 공간 회수량을 합산하면 과대계상할 수 있다. 실제로 제거하지 않았고 확보 가능한 물리 용량은 측정하지 않았다. symlink/junction 순환·경계 탈출은 문서 조사만 했으며 로컬 실행 미검증. |
| 내용 식별자 + 시점별 목록 | [restic 설계 원문](https://github.com/restic/restic/blob/master/doc/design.rst)은 내용 해시 참조, 한 번 쓴 객체의 불변성과 파일/경로 메타데이터를 담은 snapshot을 구분한다. | 백업 분야에서 빌릴 수 있는 대안은 내용 근거와 경로·시각 관찰을 별도 기록하는 것. 현재 경로가 나중에도 같은 내용을 갖는다는 보장은 별도로 해야 한다. restic의 저장소 snapshot을 라이브 원본 파일시스템의 원자적 snapshot 보장으로 해석하지 않는다. 설치·통합 실행 미검증. |
| 날짜를 출처 있는 주장으로 보존 | [ExifTool 실제 Exif.pm](https://raw.githubusercontent.com/exiftool/exiftool/master/lib/Image/ExifTool/Exif.pm) 0x9003/0x9004/0x9011과 SubSecDateTimeOriginal은 원본 시각, 디지털화 시각, 시간대와 조합값을 구분한다. [Windows File Times](https://learn.microsoft.com/en-us/windows/win32/sysinfo/file-times)는 파일시각을 내용 수정 없이 설정할 수 있고 파일시스템별 정밀도·시간대 의미가 다름을 설명한다. | EXIF 원문·태그 출처·명시 offset·유효성·시각 의미를 보존한다. 없는 날짜는 null, 잘못된 날짜는 invalid, offset 없는 값은 local wall-time으로 남기는 재료를 구현했다. offset 없이 UTC/촬영 순서/최초 원본을 단정하지 않는다. 카메라 시계 오차·충돌하는 EXIF/XMP/sidecar 진실성은 미검증. 날짜 파서는 실험용 제한된 EXIF 형식이며 모든 합법 EXIF/XMP 표현을 처리하는 완성 파서가 아니다. |

## 실제 실행 결과

주 실행: `run_20260908T102902324155Z/results.json`, **10/10 체크 통과**. `input_observations.json`에 합성 입력 사본의 실제 디코드/날짜를 남겼다. 정상 사진 5개가 디코드됐고 손상 JPEG 1개는 `Truncated File Read`, 텍스트 2개는 `UnidentifiedImageError`였다. 입력의 dated.jpg와 duplicate.jpg는 SHA-256이 같고 날짜 `2024:07:15 10:20:30`, 명시 offset `+09:00`이 읽혔다. PNG/TIFF/회전 JPEG에는 촬영일이 없었다.

새로 만든 절단 PNG는 `Image.open` 성공 후 `load`가 `image file is truncated`로 실패했다. 헤더 확인을 전체 이미지 디코드 성공으로 보고하면 안 된다. 이 절단 PNG는 기존 입력의 손상 JPEG와 구분되는 주입 사례다.

새 4바이트 파일을 같은 크기로 수정하고 이전 mtime을 복원하자 inode·size·mtime·Path.stat ctime가 그대로여도 SHA-256은 달랐다. 캐시 키나 변경 전후 stat 일치만으로 라이브 데이터의 불변성을 보장할 수 없다는 반례다. 적대적 동시 변경을 완전히 탐지하는 구현은 만들지 않았다. 내용 기반 재검증·읽은 핸들 전후 비교·snapshot/쓰는 쪽 협력은 후속 제작자가 검토할 선택지다.

입력 보존 결과는 `input_manifest_before.json`과 `input_manifest_after.json`의 동일성으로 확인했다. **8개 파일의 내용 SHA-256·크기·mtime_ns가 전후 동일**하다. atime 불변이나 운영체제 수준의 쓰기 차단을 주장하지 않는다.

## 환경 차이로 생긴 추가 실패

메인이 전달한 Windows ctime API 불일치를 별도 작업장 파일로 검증했다. 첫 시도 `ctime_20260908T103010358732Z/results.json`에서는 생성과 변경 시각이 같아 불일치가 재현되지 않았다. 생성 후 50ms 뒤 mtime을 설정한 두 번째 `ctime_20260908T103034236208Z/results.json`에서는 **같은 API의 읽기 전후 값은 모두 안정적인데 Path.stat와 os.fstat 사이의 ctime_ns만 달랐다**. dev/ino/size/mtime/birthtime는 같았다.

[CPython v3.12.10 posixmodule.c](https://raw.githubusercontent.com/python/cpython/v3.12.10/Modules/posixmodule.c)의 `win32_xstat`는 birthtime을 ctime으로 복사한다. [동일 버전 fileutils.c](https://raw.githubusercontent.com/python/cpython/v3.12.10/Python/fileutils.c)의 `_Py_attribute_data_to_stat`는 Windows ChangeTime을 ctime에 넣고 `_Py_fstat_noraise`는 그 결과를 반환한다. [Python 3.12 문서](https://docs.python.org/3.12/library/os.html#os.stat_result.st_ctime)는 Windows ctime의 폐기 예정과 birthtime 사용을 설명한다. 이 특정 패치 버전에서는 API 간 의미 차이까지 실행으로 드러났다. ctime가 mtime와 같다는 일반 법칙은 아니다. 비교할 API·필드 계약을 분리할 근거가 된다.

## 재현

이 디렉터리를 작업 위치로 하여 아래 명령을 실행한다. 모든 새 실행은 별도의 `run_...`/`ctime_...` 디렉터리를 만들고 원본은 보존한다. 표준 입력 폴더 위치는 이 디렉터리에서 네 단계 위 `project/inputs`로 정해져 있다. 프로젝트 밖 독립 이동 시 입력 경로 계약을 먼저 수정해야 한다.

```powershell
$labPath = (Get-Location).Path
$env:TEMP = "$labPath/.tmp"
$env:TMP = "$labPath/.tmp"
python -I -B -m venv .venv
& ./.venv/Scripts/python.exe -I -B -m pip install --disable-pip-version-check --cache-dir .cache -r requirements.txt
& ./.venv/Scripts/python.exe -I -B identity_probes.py
& ./.venv/Scripts/python.exe -I -B ctime_probe.py
```

설치 때 일반 sandbox의 pip 네트워크가 WinError 10013으로 실패했고, 허용된 작업장 전용 설치에 대한 권한 재시도로 Pillow 11.3.0 설치가 성공했다. 별도 계정·키·유료 서비스·업로드는 사용하지 않았다. 최초 release check는 메인의 up_to_date 결과를 재사용해 반복하지 않았다.

## 근거 공백과 조사 종료 범위

ExifTool 본문 HTML과 Pillow 11.3.0 문서 URL은 도구 internal error로 열리지 않았다. 해당 HTML을 확보했다고 세지 않았으며 공개 GitHub의 Exif.pm 및 버전 고정 ImageOps.py로 핵심 동작을 검증했다. ImageHash/fdupes/restic의 master 원문은 조사 시점의 코드이며 설치 실행·고정 커밋 통합 성공으로 확장하지 않았다. 원천별 여러 페이지는 한 구현 원천으로 합쳐 판단했다.

바이트, 픽셀, 유사도, 경로 별칭, 시점별 목록, 날짜 출처와 각 반례를 비교했으므로 이 역할의 개념·실패 조건 판정은 가능하다. 추가로 같은 설명의 링크를 늘리는 효용은 낮다. 실제 사진 threshold, HEIC/RAW/색관리, 대량 성능, 네트워크 파일시스템, 실제 정리 동작의 안전성은 이 작은 합성 실험이 답하지 못한다. 이 부분은 기능 전체의 완료로 표시하지 않는다.
