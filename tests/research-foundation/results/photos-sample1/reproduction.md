독립 재현 기록 — 사진 기능 재료, 2026-09-08

핵심 분석 CLI, 사람이 읽는 검토 Markdown, 메인 테스트는 제공 재료로 재현됐다. 메인 테스트는 28개 중 27개 통과·Windows symlink 권한 부족 1개 skip이다. 다만 전달된 `probe_local_review.py`는 11/12, 종료 코드 1이었다. 저장 JSON과 실제 전달 입력의 파일시스템 수정 시각 8개가 달랐으며, 이를 고쳐서 전체 성공으로 보고하지 않았다. 동일성 프로브는 13/13, 안내에 따른 junction 재구성 후 통합 검토는 15/15였다.

이 문서는 이 디렉터리에서 수행한 독립 재현 기록이다. 원래 대화, 원래 actor 작업장, 다른 작업의 기록, 상위 평가 자료나 평가기준은 읽지 않았다. 전체 host trace가 아니며, 아래 증거는 이 재현에서 실행한 명령과 그 출력이다.

작업 루트는 `C:/Codex/Elenchus/tests/research-foundation/.work/photos-sample1-reproduction-clean`이다. 아래 상대 경로는 이 루트를 기준으로 한다.

먼저 `input.md`를 읽고 `rg --files --hidden -g '!**/.git/**' project`로 전달 파일을 확인했다. 시작 문서로 다음 자료를 읽었다.

- `project/.elenchus/HANDOFF.md`
- `project/.elenchus/topology.md`
- `project/.elenchus/research/index.md`
- `project/.elenchus/research/R001-metadata-reliability.md`
- `project/.elenchus/research/R002-identity-candidates.md`
- `project/.elenchus/lab/R001/main/README.md`
- `project/inputs/README.md`, `project/existing-product.txt`

그다음 main의 requirements, `photo_materials.py`, `render_review.py`, `test_photo_materials.py`, `generate_fixtures.py`, `probe_local_review.py`, `verify_originals.py`; metadata-research의 requirements, bootstrap, `probe_exifread.py`; identity-research의 두 probe 코드를 읽었다. 추가 실행 방법과 실패 원인을 확인할 때 두 연구 작업장의 `notes.md`에서 설치·재현·junction 관련 부분을 검색해 읽었다. 저장된 `sample-report-final.json`, `review.md`, 해시 baseline은 전달된 기대결과/검증 데이터로만 사용했다. 이전 실패 관찰 JSON이나 활동 trace를 조사 근거로 다시 읽지는 않았다.

환경은 Windows NT 10.0.26200.0, PowerShell 7.6.5, AMD64, Python 3.12.10이었다. 시스템 Python 경로는 `C:/Program Files/Python312/python.exe`다. `Get-Command python, py`, `python --version`, PowerShell 및 OS 버전 확인 명령은 종료 코드 0이었다.

`project/` 전체 114개 파일의 SHA-256·크기·mtime_ns를 먼저 저장했다. 이어 `execution/project/`에 `shutil.copy2`로 사본을 만들었다. README의 안내대로 기존 venv/cache/test-runs는 재사용하지 않았으며, `deps`, `__pycache__`도 제외했다. 실제 사본은 90개 파일이고 복사 직후 원본과 내용·크기·mtime가 모두 일치했다. [초기 환경](evidence/environment-initial.json), [원본 baseline](evidence/source-before.json), [사본 baseline](evidence/copy-before.json)에 남겼다.

새 venv는 `execution/project/.elenchus/lab/R001/main/.venv/`에 생성했다. `include-system-site-packages = false`이며, 설치 후 해당 Python에서 Pillow 12.3.0과 venv 안의 실제 import 경로를 확인했다. ExifRead 3.5.1은 metadata-research의 전용 `deps/`에 설치했다. 요구 파일에 있는 SHA-256 `e5426ce2857423ad401e575ea9d159dc97449dc041fb6e61b35109caea72c311`을 `--require-hashes`로 강제했다. 기존 venv·전역 site-packages를 가져오지 않았다.

실행을 감싸는 `reproduce.py`는 이 검토자가 만든 기록 도구다. 각 하위 명령의 **실제 argv, cwd, 시작/종료 시각, 종료 코드**를 `evidence/<실행명>.json`에, stdout/stderr를 같은 이름의 `.stdout.txt`/`.stderr.txt`에 기록한다. Python 하위 프로세스의 bytecode를 막고 UTF-8 출력을 사용했으며 TEMP/TMP는 `execution/tmp/`로 한정했다. 이는 OS 수준 격리를 증명하지 않는다.

아래 표의 명령은 작업 루트에서 실제 실행했다. `run` 명령의 하위 argv는 연결된 JSON에서 그대로 확인할 수 있다. 설치에는 재시도 0회·타임아웃 20초를 추가해 제한 환경의 실패를 빨리 드러냈다.

| 실제 명령 | 실행 조건 | 종료 코드와 결과 | 하위 명령 증거 |
|---|---|---|---|
| `python -B reproduce.py init` | 원본 hash 후 사본 생성 | 0, 원본 114·사본 90개 일치 | `environment-initial.json`, `copy-before.json` |
| `python -B reproduce.py run venv` | 새 venv | 0 | [venv-01](evidence/venv-01.json) |
| `python -B reproduce.py run pip-pillow` | README 계열 pip 명령, 기본 sandbox | 1, `No matching distribution found for Pillow==12.3.0` | [pip-pillow-01](evidence/pip-pillow-01.json) |
| `python -B reproduce.py run pip-context` | 안전한 pip 환경값만 확인 | 0, PIP_NO_INDEX/CONFIG_FILE/INDEX_URL 설정 없음, venv 분리 확인 | [pip-context-01](evidence/pip-context-01.json) |
| `python -B reproduce.py run pip-pillow-public` | `--isolated --index-url https://pypi.org/simple`, 기본 sandbox | 1, 같은 버전 검색 실패 | [pip-pillow-public-01](evidence/pip-pillow-public-01.json) |
| `python -B reproduce.py run pip-pillow-public` | 같은 명령, scoped 권한 상승 | 0, 7.2 MB Windows CPython 3.12 wheel 다운로드·설치 | [pip-pillow-public-02](evidence/pip-pillow-public-02.json) |
| `python -B reproduce.py run environment` | 설치된 venv의 실제 import 확인 | 0, Python 3.12.10 / Pillow 12.3.0 | [environment-02](evidence/environment-02.json) |
| `python -B reproduce.py run scan` | 사본 `inputs/` 실제 분석 | 0, 8개·정상 5·손상 1·비이미지/미지원 2·동일 그룹 1 | [scan-01](evidence/scan-01.json) |
| `python -B reproduce.py run render` | 새 JSON → 새 Markdown, `-I -B` | 0 | [render-01](evidence/render-01.json) |
| `python -B reproduce.py run tests` | main 디렉터리에서 `-B -m unittest -v test_photo_materials` | 0, 28개 중 27 통과·1 skip | [tests-01](evidence/tests-01.json), [테스트 출력](evidence/tests-01.stderr.txt) |
| `python -B reproduce.py run local-review` | 제공 probe 그대로 실행 | **1, 12개 중 11 통과, Python socket 호출 0** | [local-review-01](evidence/local-review-01.json), [실제 결과](execution/project/.elenchus/lab/R001/main/local-review-results.json) |
| `python -B reproduce.py run verify-originals` | 제공 원본 보존 검사 | 0, 보호 대상 10개·두 baseline 모두 일치 | [verify-originals-01](evidence/verify-originals-01.json) |
| `python -B reproduce.py run pip-exifread` | bootstrap의 hash 고정 설치 조건, 새 venv의 pip 사용, 기본 sandbox | 1, `No matching distribution found for ExifRead==3.5.1` | [pip-exifread-01](evidence/pip-exifread-01.json) |
| `python -B reproduce.py run pip-exifread` | 같은 명령, scoped 권한 상승 | 0, 59 kB wheel 다운로드·hash 검증·설치 | [pip-exifread-02](evidence/pip-exifread-02.json) |
| `python -B reproduce.py run exifread` | 기본 sandbox | 1, `exifread.__version__` AttributeError | [exifread-01](evidence/exifread-01.json) |
| `python -B reproduce.py run exifread` | 같은 로컬 probe, scoped 권한 상승 | 0, ExifRead 3.5.1, 8개 입력·strict 두 모드, 원본 hash 보존 | [exifread-02](evidence/exifread-02.json) |
| `python -B reproduce.py run identity` | 새 venv, `-B` | 0, 13/13 | [identity-01](evidence/identity-01.json) |
| `python -B reproduce.py run identity-review` | junction 생성 전 | 1, `linked-target` FileNotFoundError | [identity-review-01](evidence/identity-review-01.json) |
| `python -B inspect_results.py` | 별도 진단 코드, 저장 기대결과와 실제 산출물 비교 | 0, 차이 8개가 모두 mtime_ns임을 확인 | [report-comparison](evidence/report-comparison.json) |
| `python -B reproduce.py run identity` | 하위 notes의 명령대로 `-I -B` 추가 | 0, 13/13 재확인 | [identity-03](evidence/identity-03.json) |
| `python -B reproduce.py run prepare-junction` | 하위 notes에 있는 fixture 복원 안내 | 0, 사본 안 형제 target으로 연결 | [prepare-junction-01](evidence/prepare-junction-01.json), [대상 경로](evidence/junction-setup.json) |
| `python -B reproduce.py run identity-review` | junction 준비 후, `-I -B` | 0, 15/15 | [identity-review-02](evidence/identity-review-02.json) |
| `python -B reproduce.py audit` | 원본 전체 및 사본 보호 파일·코드 재검사 | 0, 원본 114개 불변 | [preservation-audit](evidence/preservation-audit.json) |

실제 핵심 하위 실행은 다음 형태였다. 모든 상대 경로는 이 코드 블록에서만 `execution/project/` 기준이다. `$replayPython`은 이번에 만든 venv의 Python이다. 전체 절대 argv와 실제 cwd는 위 JSON에 남아 있다.

```powershell
$replayPython = '.elenchus/lab/R001/main/.venv/Scripts/python.exe'
& $replayPython -B '.elenchus/lab/R001/main/photo_materials.py' inputs --output '.elenchus/lab/R001/main/my-report.json'
& $replayPython -I -B '.elenchus/lab/R001/main/render_review.py' '.elenchus/lab/R001/main/my-report.json' --output '.elenchus/lab/R001/main/my-review.md'
```

공개 네트워크를 사용한 경로와 로컬 fixture 결과는 다음처럼 구분한다.

| 경로 | 실제 실행한 것 | 관찰과 주장 범위 |
|---|---|---|
| 공개 네트워크 | PyPI에서 고정 버전 Pillow 및 hash 고정 ExifRead 설치 | 두 패키지의 wheel 다운로드와 설치가 실제 성공했다. 기본 sandbox 실패를 버전 부재로 단정하지 않았다. 같은 명령이 권한 상승에서 성공하므로 실행 환경의 접근 조건과 라이브러리 존재 여부를 구분했다. 실패 출력 자체는 자세한 원인을 주지 않았다. |
| 전달된 저장 입력 | `inputs/`의 합성 JPEG·PNG·TIFF, 손상 JPEG, 텍스트 8개 | 파일을 실제 읽고 메타데이터·decode·동일성·후보를 새로 계산했다. 온라인 사진 API, 개인 사진, 원격 이미지 다운로드는 사용하지 않았다. |
| 전달 코드로 생성한 fixture | main unittest의 날짜·회전·손상 변형과 identity의 5개 반례 | 실행 사본에서 fixture를 다시 생성해 검사했다. 생성된 fixture들의 내용은 전달본과 같았으며 원본 `project/`의 fixture는 변경하지 않았다. |
| 저장 기대결과 대조 | `sample-report-final.json`, `review.md`, hash baseline | 저장 JSON을 성공 결과로 단순 재사용하지 않았다. 새 report와 비교하여 mtime 차이 8개를 발견했다. 새 Markdown은 저장 Markdown과 텍스트가 같았다. identity의 통합 리뷰는 코드상 저장 main report와 이번에 재실행한 identity 관찰을 비교한다. |
| 설치 후 로컬 연결 확인 | `probe_local_review.py`의 scan+render+재실행 | socket 생성·연결·DNS 진입점을 막고 실행했으며 시도 0이다. 이 실행의 11/12와 mtime 대조 실패를 함께 남긴다. OS 방화벽 차단이나 모든 미래 실행의 네트워크 부재를 증명하는 실험은 아니다. |

대표 입력의 실제 결과는 다음과 같다. 새 JSON은 [my-report.json](execution/project/.elenchus/lab/R001/main/my-report.json), 사람이 읽는 결과는 [my-review.md](execution/project/.elenchus/lab/R001/main/my-review.md)다.

| 입력 | 이번 관찰 |
|---|---|
| `copies/duplicate.jpg`, `session A/dated.jpg` | 둘 다 JPEG 8×6·763 bytes. SHA-256 `98be3ae374a8913faf97f323ae964374945f54b0aa296958a929fb90e0113491`과 실제 바이트가 같아 exact-001. 촬영일 `2024-07-15`, +09:00, UTC `2024-07-15T01:20:30Z`. |
| `회전/rotated.jpg` | JPEG 저장 8×6, Orientation 6, 실제 표시 6×8. 촬영일 후보는 null. |
| `formats/sample.tiff` | TIFF 저장 8×6, 최초 파서 및 표시 6×8, Orientation 8. IFD0 수정 날짜는 보존되지만 capture 및 날짜 후보는 null. |
| `plain.png` | 정상 decode, 촬영 날짜 및 날짜 후보 없음. |
| `broken/truncated.jpg` | Pillow 식별 단계 `OSError: Truncated File Read`, invalid_image. ExifRead는 strict=False/True 모두 빈 태그·경고 없음. 따라서 빈 EXIF가 정상 decode를 뜻하지 않는 반례가 재현됐다. |
| `README.md`, `notes.txt` | non_image_or_unsupported. 입력 폴더 설명 파일도 스캔 대상에 포함되어 총 8개다. |

모든 후보는 `action=review_only`였고 날짜가 배정된 것은 같은 JPEG 두 개뿐이었다. 테스트에서 날짜 누락·충돌·잘못된 오프셋·초 미만 9자리·1~8 회전·PNG CRC·JPEG EOI·다중 프레임·자원 상한·읽기/변경 오류 주입·해시 충돌 후 실제 byte 비교·출력 보호·재실행을 통과했다. 하드링크 시험은 실제 통과했다. symlink는 WinError 1314 때문에 skip됐으므로 성공으로 세지 않았다. identity 반례에서는 JPEG 주석 변경/회전 정규화가 바이트 동일성을 깨면서 표시 픽셀을 유지했고, 다른 단색의 aHash 충돌도 재현됐다.

실패와 보완은 다음처럼 남겼다.

1. **저장 보고서와 mtime 불일치 — 미수정 실패.** `local-review`의 유일한 false 항목은 `same_scanner_output_as_verified_sample`이다. 새 JSON과 저장 JSON의 차이는 `records[0..7].filesystem_mtime_ns`뿐이었다. 예를 들어 dated.jpg는 저장값 `1788854622047703200`, 전달 원본 및 사본은 `1788859362346341500`이다. 실행 사본을 만들기 전부터 전달 파일과 저장 보고서가 달랐고, 사본의 mtime는 전달본과 같다. README가 동일 mtime를 결정성 조건으로 명시한 점은 확인했으나, 이 배포본에서 golden 대조가 실패할 수 있다는 준비/판정 방법은 직접 비교해야 알 수 있었다. golden JSON이나 입력 mtime를 재작성하지 않았고, `probe_local_review.py`도 수정하지 않았다. 검토 Markdown 일치, 동일 디렉터리에서의 재실행 결정성, socket 0, 원본 보호 등 나머지 11개는 통과했다. [전체 차이](evidence/report-comparison.json)를 보존했다.
2. **네트워크/설치 및 ExifRead import의 환경 의존성.** 기본 실행에서 두 패키지 설치가 실패했다. 새 사본의 설치 범위로 한정한 권한 상승에서 같은 고정 버전 다운로드가 성공했다. ExifRead는 설치 후 기본 sandbox에서 `__version__` 없는 모듈로 보여 probe가 실패했지만, 같은 코드·같은 deps를 scoped 상승 실행하자 버전 3.5.1과 전체 결과가 정상 반환됐다. 문서가 설명한 설치/접근 장애 범주와 일치하지만 이 검토에서 ACL 자체를 별도로 분석한 것은 아니다. 라이브러리 소스 수정이나 시스템 설정 변경으로 우회하지 않았다. 자동 승인 거절은 없었다.
3. **junction fixture 누락 — 안내된 준비로 복원.** 전달본에는 marker 파일 두 개가 있으나 `source/linked-target` junction은 없었다. 따라서 준비 없이 실행한 review는 종료 코드 1이었다. 이후 하위 `identity-research/notes.md`의 “새 위치로 복사하여 Junction이 보존되지 않았으면” 안내에 따라 사본 안 junction을 만들었다. `prepare_junction.ps1`은 생성 경로와 target의 절대 경로가 실행 사본 안인지 확인하고 기존 경로를 대체하지 않는다. 제품 코드 변경 없이 15개 검증이 통과했다. child skip, target 미순회, junction 입력 root 거부가 실제로 확인됐다. 처음 실패도 보존했다.
4. **전달 설명의 일부 근거 링크 부재.** README/HANDOFF가 가리킨 `tests-ifd-final.log`, `tests-first.log`, metadata-research/reproduction의 `notes.md`, `audit-results.json`, `local-review-notes.md`는 이 project에 없었다. 관련 위치의 존재 여부만 확인했으며 다른 작업장에서 찾지 않았다. 따라서 그 문서에 인용된 이전 독립 실행 이력을 이 전달본에서 열어 검증할 수는 없었다. 이번 메인 테스트 결과는 실제 새 실행에서 확보했다.

보완 코드는 `reproduce.py`(격리 사본·실행 기록·원본 감사), `inspect_results.py`(저장값 비교), `prepare_junction.ps1`(문서에 있는 fixture 준비)뿐이며 모두 전달 `project/` 밖에 있다. `bootstrap.ps1`을 그대로 호출하지 않고 그 hash 고정 pip 설치 조건을 새 venv의 pip로 실행했다. 제품 코드의 결함을 고쳐 성공한 것으로 바꾸는 보완은 하지 않았다.

최종 원본 감사에서 `project/` 114개 파일의 SHA-256·크기·mtime_ns가 모두 최초와 같고 추가/삭제 파일도 없었다. 사본의 입력 8개와 sentinel/manifest 2개도 보호 baseline과 일치했다. 핵심 코드 SHA-256은 원본·사본 모두 `263c4e70a5d638e4667b03c5fe87d4f0cbc6f06120304d7b52ee6631541d50be`로 유지됐다. 사본의 기존 파일 중 내용이 바뀐 것은 재실행이 출력하는 `local-review-results.json`, ExifRead `probe-results.json`, identity `observations.json`, `main-review.json` 네 파일뿐이다. 제품 Python 코드·requirements·기존 fixture 바이트·saved golden report는 그대로다. 새 report/review, tests의 임시 입력, venv/cache/deps 및 내부 junction은 실행 사본에 남겼다. [전후 보존 결과](evidence/preservation-audit.json)에 상세 목록이 있다.

재사용 가능한 범위는 Windows/Python 3.12.10/Pillow 12.3.0의 작은 합성 JPEG·PNG·TIFF 입력에 대한 메타데이터/날짜 불확실성 보존, 실제 byte 동일 그룹, 비파괴 검토 JSON/Markdown, 명시적인 오류 처리와 테스트다. 설치 이후 핵심 분석/렌더 경로는 이번 실험에서 Python 네트워크 호출 없이 작동했다. 고정 JSON 기대값을 새 위치에서 대조할 때는 파일시스템 mtime를 포함한다는 조건과 이번 실패를 고려해야 한다. junction은 하위 안내에 따라 재구성해야 한다.

HEIC/RAW·실제 카메라 EXIF/MakerNote·sidecar·색관리/고비트/알파 의미·유사 사진 정확도·대량 성능·원자적 파일시스템 snapshot·최종 UX·대표 파일 선택이나 삭제/이동 정책은 이번 재현으로 확인하지 않았다. PhotoPrism, Immich, IPFS, ImageHash, ExifTool 등의 공개 서비스/도구 실행도 수행하지 않았다. 이 기록은 제공된 연구 문서의 해당 비교 주장을 새 실행 성공으로 확대하지 않는다. 재현을 마치는 데 필요한 사용자 질문은 없었다.
