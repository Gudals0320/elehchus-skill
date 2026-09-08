# 사진 기능 재료 재실행

Python 3.12.10 / Pillow 12.3.0 / Windows에서 확인했다. `photo_materials.py`는 디렉터리의 작은 파일을 읽어 형식·EXIF 날짜·회전·검증 상태·바이트 동일 그룹·검토 후보를 연결한다. 읽기 API에는 삭제/이동/수정 기능이 없다. CLI는 입력 안의 출력과 기존 결과 덮어쓰기를 거부한다.

프로젝트 루트(원본 `inputs/`와 `inputs.sha256.json`가 있는 위치)에서 새 환경:

```powershell
python -m venv '.elenchus/lab/R001/main/.venv'
& '.elenchus/lab/R001/main/.venv/Scripts/python.exe' -m pip install --disable-pip-version-check --cache-dir '.elenchus/lab/R001/main/.pip-cache' -r '.elenchus/lab/R001/main/requirements.txt'
& '.elenchus/lab/R001/main/.venv/Scripts/python.exe' -B '.elenchus/lab/R001/main/photo_materials.py' inputs --output '.elenchus/lab/R001/main/my-report.json'
& '.elenchus/lab/R001/main/.venv/Scripts/python.exe' -I -B '.elenchus/lab/R001/main/render_review.py' '.elenchus/lab/R001/main/my-report.json' --output '.elenchus/lab/R001/main/my-review.md'
Push-Location '.elenchus/lab/R001/main'
& '.venv/Scripts/python.exe' -B -m unittest -v test_photo_materials
Pop-Location
```

설치된 환경에서는 분석·검토문서 생성·테스트에 네트워크가 필요 없다. 패키지 설치에만 공개 PyPI 접근이 필요하며 권한 실패를 버전 없음으로 해석하면 안 된다. 이미 존재하는 `my-report.json`/`my-review.md` 대신 새로운 파일명을 사용한다. 테스트는 합성 변형을 `fixtures/`, 작은 독립 입력을 `test-runs/`에 만든다. 원본 입력과 `existing-product.txt`, `inputs.sha256.json`를 수정하지 않는다. 별도 복제 재현은 프로젝트 상대 구조 그대로 입력·manifest·sentinel과 이 폴더의 코드·requirements·`original-before.json`를 복사한 뒤 실행하면 된다. 기존 `.venv`, `.pip-cache`, `test-runs`를 복사할 필요는 없다.

사람이 읽는 결과는 [review.md](review.md)다. 날짜별 후보·날짜 미지정 이유·동일 파일 그룹·Orientation 최초 조회 값/표준 해석/실제 표시 치수·오류를 나란히 보인다. 날짜의 초 미만 값도 있으면 원문을 표시한다. 정리 행동은 실행하지 않으며 최종 UX를 고정하지 않는 검토 재료다. `render_review.py`는 표준 라이브러리만 쓰고 기존 JSON을 읽는다. `probe_local_review.py`는 분석·문서 생성 중 Python socket 진입점을 차단한 채12개 연결 확인을 실행한다. `local-review-results.json`의 네트워크 호출0/원본10개 불변 결과는 그 실행 범위의 증거이며 OS 방화벽 격리를 증명한다고 주장하지 않는다. 프로브가 쓰는 초 미만 합성 fixture가 없으면 작업장 `fixtures/`에 생성한다.

## API와 출력 의미

- `scan_directory(Path) -> dict`: Python 자료 반환. 스캔 시간·절대 입력 경로를 결과에 넣지 않아 같은 파일/mtime/버전/정책에서 결정적 JSON을 만든다.
- `inspect_bytes(bytes, suffix)`: 형식 판별, 메타데이터, 별도 `verify()`, 전체 프레임 `load()`를 구분한다. 알려진 확장자로도 인식 못 하면 `unrecognized_image`; 손상인지 미지원 코덱인지 확정하지 않는다.
- `parse_exif_date(value, offset, subsecond)`: 원문·태그 의미·local/UTC·누락/오류 상태를 남긴다. 오프셋 없는 시각은 UTC로 만들지 않는다. 초 미만 문자열은 원래 자릿수를 보존한다.
- `exact_groups`: 파일 크기+SHA-256 후보를 실제 메모리 바이트 비교로 확정한다. SHA 충돌을 주입한 테스트에서도 서로 다른 바이트는 분리한다. 하드링크는 `same_file_alias`이며 별도 복사본으로 세지 않는다. 심볼릭 링크/Windows reparse point는 따라가지 않는다.
- `build_candidates`: `action=review_only`. 유효한 `DateTimeOriginal`의 **현지 날짜**만 `date_bucket`에 사용한다. TIFF DateTime(수정일), digitized 시각, mtime, 파일명은 촬영일 대체값으로 쓰지 않는다. 날짜 충돌/누락/오류·회전·동일 바이트 그룹을 이유로 연결한다. 보존할 대표 파일·삭제 대상·목적지 경로는 정하지 않는다.
- `encoded_size`는 TIFF 태그 256/257 또는 타 형식의 파서 크기, `reported_size`는 최초 Pillow 객체 크기, `display_size`는 첫 프레임 디코딩+EXIF 정규화 후 크기다. TIFF에서 파서 자체의 회전을 중복 적용하지 않는다. `orientation`은 첫 메타데이터 조회 값이며 회전 2~8에는 반전도 있다. 픽셀 동일성과 원본 파일 동일성은 다르다.

`status=ok`는 이 버전의 제한된 디코딩·메타데이터 읽기 성공이며 실제 촬영일의 진실, 전체 형식 사양 준수나 파일 무해성을 증명하지 않는다. `verify_status`와 `decode_status`를 함께 보고, 다른 오류 때문에 남은 메타데이터를 버리지 않는다. 해시가 있어도 디코딩 실패일 수 있다.

## 확보한 검증과 의도적 한계

`sample-report-final.json`: 8개 입력, 정상 5·손상1·비이미지 또는 미지원2, 동일 그룹1. 최신 `tests-ifd-final.log`: 28개 중 27 통과, 심볼릭 링크 생성은 Windows WinError1314로 1개 skip. 하드링크는 실제 생성·확인했다. 별도 R002 조사자는 Windows Junction의 skip·대상 미순회·입력 루트 거부를 실제 검증했다. 테스트는 1~8 회전 치수, 잘못된 날짜/오프셋, IFD 날짜 충돌과 수정일/오프셋의 IFD간 결합, UTC 일자 경계·초 미만, PNG CRC 손상, JPEG EOI 누락, 다중 TIFF 프레임, 파일 변경/읽기 실패 주입, 출력 보호·재실행·원본 불변을 포함한다. 원본 보존은 프로젝트 루트에서 `python -B .elenchus/lab/R001/main/verify_originals.py`로 별도 재검사할 수 있다.

소규모 재료의 메모리 상한은 파일당16 MiB, 총64 MiB, 누적 디코딩20M 픽셀, 파일당64프레임이다. 초과는 정상·손상이 아닌 `*_limit`로 보고한다. 대량 성능 목표를 임의로 충족한 것으로 보지 않는다. 파일을 읽기 전후 크기·mtime·파일 ID를 검사하지만 잠금을 잡는 원자적 filesystem snapshot은 아니다. 악의적인 동일 길이/mtime 복구 변경, 부모 디렉터리 교체 등 경쟁 조건을 완전히 막는 보안 도구가 아니다. 본 연구의 고정 합성 입력에는 변경이 없었다.

HEIC/RAW·실제 카메라 MakerNote·XMP/sidecar 날짜·GPS·ICC/고비트/알파 의미·유사 사진 정확도·대량 성능은 직접 검증하지 않았다. `pretend.heic`는 명시적인 가짜 입력이며 HEIC 지원 시험이 아니다. 다중 프레임은 전체 디코딩하되 메타데이터는 첫 프레임 기준이다. 외부 파서 업그레이드 시 테스트를 다시 실행한다. 최종 제품 UX·대표 파일 선택·폴더명·DB·병렬 처리 방식은 후속 제작자의 재량이다.

## 실패 자료와 라이선스

- `probe.py`, `probe-results.json`: 최초 라이브러리 탐색; PNG 잘못된 verify 순서 실패를 보존했다. 이 파일은 최종 판정이 아니다.
- `sample-report.json`: Windows DirEntry stat의 0 파일 ID를 실제 stat와 비교해 모든 파일 변경으로 잘못 판정한 첫 결과.
- `sample-report-v2.json`: lstat 수정 후 입력 판정. 당시 오류 메시지의 BytesIO 주소가 실행마다 달랐다.
- `tests-first.log`: 그 재실행 동일성 실패. 최종 코드는 오류 객체 주소를 표준 문구로 바꿨다.
- `fixtures/fixture-manifest.json`, `generate_fixtures.py`: 새로 주입한 날짜·회전·손상 변형의 출처. 제공 입력에서 관찰한 현상과 구분한다.
- `original-before.json`: 입력8개 및 sentinel/manifest 파일2개 SHA-256. 원본 보존 검증 기준이다. `probe.py`를 다시 실행하면 이 기준도 다시 기록되므로 원본 보존 비교용 baseline 재생성에 쓰지 않는다.

설치된 Pillow 12.3.0의 LICENSE 본문은 MIT-CMU License를 명시한다. 배포 시 해당 원문과 wheel에 포함된 의존성별 고지를 보존한다. 이번 기능 코드는 연구 중 작성했고 외부 프로젝트 코드는 복사하지 않았다. 설치된 배포본 라이선스 경로는 `.venv/Lib/site-packages/pillow-12.3.0.dist-info/licenses/LICENSE`다. [Pillow 라이선스 원문](https://github.com/python-pillow/Pillow/blob/12.3.0/LICENSE)을 참조한다.
