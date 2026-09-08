# 사진 기능 재료 인계

이 폴더의 `photo_material.py`는 제공 합성 입력을 읽어 메타데이터, 이미지 검사 상태, 동일 파일 그룹, 실행하지 않는 후보 JSON을 만든다. 실제 라이브러리 실행·비교 근거는 [R001](../../research/R001-metadata.md)과 [R002](../../research/R002-identity-candidates.md)에 있다. 최종 제품 UX·화면·동선·파일 배치 정책은 정하지 않았다.

## 재실행

Windows/Python 3.12.10에서 Pillow 12.3.0, ExifRead 3.5.1로 확인했다. Python 3.12 이상의 별도 환경을 권장한다. 이 `R001` 폴더를 작업 디렉터리로 하여 PowerShell에서 실행한다.

```powershell
python -m venv .venv
New-Item -ItemType Directory -Force -Path .tmp | Out-Null
$env:TEMP = "$PWD/.tmp"
$env:TMP = "$PWD/.tmp"
.venv/Scripts/python.exe -m pip install --cache-dir pip-cache -r requirements.txt
.venv/Scripts/python.exe -B -m unittest -v test_material
$photoRunStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
.venv/Scripts/python.exe -B photo_material.py ../../../inputs --output "results/scan-$photoRunStamp.json"
.venv/Scripts/python.exe -B photo_material.py fixtures --output "results/fixtures-$photoRunStamp.json"
```

이미 설치된 `.venv`를 사용하면 설치 명령은 생략할 수 있다. 설치 이후 테스트·스캔은 네트워크를 사용하지 않는다. `fixtures/`가 없으면 테스트가 `generate_fixtures.py`로 만든다. 기존 fixture는 보존하므로 생성 스크립트를 직접 재실행하면 FileExistsError를 반환한다. CLI도 기존 출력 파일을 덮어쓰지 않고 새 이름을 요구한다. 입력 안이나 연구 lab 밖으로 출력하는 요청은 거절한다. 사진 읽기 모듈에는 원본 이동·삭제·수정 함수를 두지 않았다.

다른 디렉터리로 전달할 때 `project/inputs/`, `project/inputs.sha256.json`, `project/existing-product.txt`와 `project/.elenchus/lab/R001/`의 코드 3개·requirements·baseline·fixtures·README를 상대 구조 그대로 함께 둔다. `.venv`와 pip 캐시는 재구성용이며 전달에 필수가 아니다. 기존 입력 manifest는 원본 그대로 유지한다. 복제 재현은 `../R002/repro/project/`에서 실제 실행했으며 22개 테스트가 통과했다. 동일한 별도 venv를 사용했으므로 새로운 운영체제/패키지 설치 검증을 뜻하지 않는다.

## 재사용 진입점과 데이터 의미

| 함수/출력 | 의미 |
|---|---|
| `analyze_bytes(data, name)` | 이미 읽은 바이트의 형식·메타데이터·검증/디코드 상태. 확장자는 보조 신호이며 실제 형식은 디코더가 식별한다. |
| `snapshot_file(path)` | 파일 크기 한도 내에서 읽기 모드로 스냅샷 취득. 같은 바이트로 SHA-256과 메타데이터를 만든다. 전후 통계는 변경 탐지이며 원자적 스냅샷이나 공격자 격리가 아니다. |
| `scan(root)` | 하위 디렉터리 순회, 파일별 실패 보존, 동일 파일 그룹과 후보 생성. 심볼릭 링크·junction은 제외한다. |
| `exact_groups(records, blobs)` | 크기·SHA-256으로 묶은 뒤 메모리 바이트를 비교. 파일 객체 수로 하드링크 별칭과 별도 파일을 구분한다. |
| `files[].dates` | IFD/태그 이름, 원시 값, 시간대/소수초 원시 값, 파싱 결과와 문제. DateTime은 수정 시각이고 DateTimeDigitized는 디지털화 시각이다. |
| `capture_date` | 유효하고 서로 충돌하지 않는 DateTimeOriginal만 연구용 촬영 후보로 선택. 태그의 진실성을 보증하지 않는다. 파일 시스템 시각·파일명으로 누락을 채우지 않는다. |
| `local`, `utc`, `timezone` | 기록된 벽시계 시각을 보존. UTC는 명시 offset이 유효할 때만 계산. 시간대 없음/잘못된 offset은 UTC null과 문제 사유로 남긴다. |
| `stored_size`, `header_size`, `display_size`, `orientation` | 파일 저장 크기·라이브러리 header 크기·방향 반영 표시 크기와 로드 전 원시 방향을 분리. TIFF는 이 값이 처음부터 다를 수 있다. |
| `metadata_status`, `verify_status`, `decode_status` | 태그 읽기·컨테이너 검사·모든 허용 프레임 디코드 상태를 각각 기록한다. |
| `display_rgba_sha256` | 첫 프레임을 방향 반영 후 RGBA8로 바꾼 픽셀 지문. ICC 색 관리·고정밀 데이터·추가 프레임을 대표하지 않으며 동일 파일 그룹에 사용하지 않는다. |
| `exact_duplicate_review` | 전체 바이트가 같은 스냅샷 경로들의 검토 후보. 보존할 파일이나 제거할 경로를 고르지 않는다. |
| `date_bucket_candidate` | 기록된 현지 촬영 날짜를 연/월/일 데이터로 변환한 예시. 파일명·최종 경로·이동 명령이 아니다. |
| `metadata_review`, `input_review` | 날짜 누락·충돌·잘못된 값·다중 프레임·확장자 불일치·손상/미식별/읽기 실패 등의 검토 근거. |

## 확보된 결과와 시행착오

- 최신 대표 결과: `results/original-scan-verified.json`. 입력 8개, 정상 디코드 5개, 손상 이미지 1개, 문서/텍스트 2개. 정확히 동일한 파일은 `copies/duplicate.jpg`와 `session A/dated.jpg` 한 그룹. 후보 9개는 동일 그룹 1, 날짜 후보 2, 날짜 메타데이터 검토 3, 입력 검토 3이다.
- 메인 회귀 테스트 22개: `results/tests-final.txt`. 8방향 픽셀 배치 PNG/TIFF, JPEG/TIFF 실제 방향, 달력 오류, offset/소수초, 상충 날짜, 잘린 JPEG, 확장자 위장, 같은 픽셀/다른 바이트, 강제로 주입한 해시 충돌, 읽기 실패/변경 감지, 자원 한도, 하드링크, 재실행·원본 불변을 검증했다.
- `fixtures/`는 29개 주입 파일과 manifest다. 제공 손상 파일 관찰과 새로 잘라 만든 JPEG 반례를 구분한다. 허가 오류·파일 변경·해시 충돌은 테스트 경계에서 주입한 상황이며 실제 충돌이 발견된 것이 아니다.
- 독립 Pillow/ExifRead 실험은 `agent_metadata/`에 있고, 메인이 복제한 코드를 실행한 `replay_metadata/`에서 14개 행과 방향·원본 해시 결과를 대조했다. `results/independent-replay-checks.json`을 참조한다.
- 독립 대안 실험은 `../R002/agent_alternatives/`의 안내·코드·10개 체크 결과에 있다. Pillow11.3.0에서 실행했고 메인은 `../R002/replay_alternatives/`에서 Pillow12.3.0으로 같은 체크를 재실행했다. 바이트·픽셀·유사 해시·다중 프레임·하드링크·캐시의 반례와 ctime API 차이가 포함된다. 비교 스크립트의 getdata 폐기 경고도 기록했다.
- 첫 복제 재현에서 Windows stat/fstat의 ctime 의미 차이로 모든 사본을 변경중으로 오판했다. API 사이에서는 dev/ino/size/mtime를, 같은 API 전후에는 ctime까지 비교하도록 수정했다. 이전 실패 로그와 수정 후 22개 통과 로그는 `../R002/repro/project/.elenchus/lab/R001/`에 함께 보존했다.
- Pillow `verify()`를 통과하는 후미 손상 JPEG가 실제 `load()`에서 실패했다. 단순 메타데이터 반환 성공이나 ExifRead `strict`는 이미지 정상의 증거가 아니다.
- 독립 조사자의 TIFF fixture 생성에서 중첩 `Image.Exif` 객체 저장이 실패했다. EXIF bytes 직렬화 후 저장하는 대안을 성공시켰다. 이는 원본 읽기 오류가 아닌 fixture 생성 경로의 실패다.

## 한계와 이후 제작자의 재량

현재 정상 경로는 JPEG·PNG·TIFF만이다. HEIC/RAW, 실제 카메라 MakerNotes·XMP/IPTC/sidecar 충돌, 전체 TIFF 압축 조합, 네트워크 드라이브, 대량 성능, 적대적 파일에 대한 프로세스 수준 자원 제한은 미검증이다. 메타데이터는 첫 프레임 중심이며 디코드는 최대 32프레임을 확인한다. 파일 64 MiB·전체 256 MiB·파일별 누적 2천만 픽셀·1만 파일의 연구용 제한이 있다. 바이트를 메모리에 유지하는 방식은 작은 자료에 적합하며 대규모 재료에는 스트리밍/별도 스냅샷 저장을 재설계해야 한다.

같은 파일명의 목표 경로 충돌, 실제 보존본 선정, 시간대 없는 날짜의 해석, 유사 이미지 임계값은 확정하지 않았다. 링크/경로 교체와 내용 수정의 모든 경합을 방어하지 않으며 후보를 나중에 적용할 때 최신 파일을 재검증해야 한다. 코드·폴더·JSON 스키마·예시 날짜 묶음은 임시 재료다. 최종 제작자는 이를 교체하거나 감쌀 수 있다. 사용자가 정한 원본 보존과 데이터 의미·불확실성을 유지해야 한다.

의존성 라이선스: Pillow MIT-CMU, ExifRead BSD-3-Clause. 배포 시 해당 패키지의 라이선스 고지를 보존한다. 외부 코드를 통째로 복사하지 않았으며 조사한 ExifTool/fdupes/ImageHash는 최종 제품에 포함된 것으로 간주하지 않는다.
