# R002: 동일 파일의 근거와 정리 후보
- 상태: 확정
- 기준: ../topology.md, R001 날짜/방향 결과
- 환경: Windows, Python 3.12.10, 2026-09-08

## 질문·달성 조건
동일 바이트, 동일 디코드 픽셀, 유사 이미지가 다른 의미임을 실제 변형으로 검증한다. 동일 파일 그룹은 파일 내용 근거로 만들고, 날짜·손상·형식·충돌을 정리 후보의 검토 사유로 전달한다. 후보는 JSON 데이터만 생성한다. 원본 파일 변경 기능을 실행하지 않는다.

## 조사 준비
직접 비교/해시 기반 파일 도구, 콘텐츠 주소 식별, 픽셀/지각 해시와 이미지 관리 도구의 접근을 비교한다. 파일 변경·링크·해시만으로 판정할 때의 실패 조건을 살핀다. 두 번째 무이력 조사자 생성은 thread limit reached로 실패, 순차 재시도 예정.

## 실제 역할과 접근 비교
메타데이터 독립 조사 종료 후 두 번째 조사자를 `fork_turns="none"`으로 생성해 대안·인접 분야·실패 조건을 맡겼다. 읽기/쓰기 범위·원본 보존·계정/키 금지 조건과 별도 파일 소유권을 전달했다. 첫 생성 실패를 실제 수행으로 계산하지 않았고, 두 명의 조사 결과를 통합했다. 조사자 수를 독립 원천 수로 세지 않는다.

| 접근 | 직접 근거와 적용 조건 | 실험·판단 |
|---|---|---|
| 전체 바이트 일치 | [fdupes README](https://github.com/adrianlopezroche/fdupes)와 [confirmmatch.c](https://raw.githubusercontent.com/adrianlopezroche/fdupes/master/confirmmatch.c)의 버퍼 길이·내용 비교. 이 함수에는 명시적 ferror 검사가 없어 읽기 오류 처리의 모범으로 채택하지 않는다. 크기/해시는 검색 후보 축소와 내용 식별의 재료. | 메인 코드에서는 크기+SHA-256 후 같은 스냅샷의 실제 바이트를 확인하고 Python 읽기 예외를 파일별 보존. 제공 입력의 두 JPG만 일치. 강제로 같은 digest를 준 서로 다른 bytes는 제외. fdupes 실행 파일은 실행하지 않음. |
| 방향을 반영한 디코드 픽셀 | Pillow로 표현 방식과 방향을 명시한 비교. | 메타데이터만 다른 PNG는 bytes 불일치/pixels 일치. Orientation6과 물리회전 파일은 방향 정규화 후만 pixels 일치. 첫 프레임만 같은 다중 TIFF 반례도 실제 확인. 파일 동일성의 대체가 아니며 첫 프레임 RGBA 지문은 파생 관찰로만 보존. |
| 지각 해시·유사도 | [ImageHash README](https://github.com/JohannesBuchner/imagehash)와 [공식 코드](https://raw.githubusercontent.com/JohannesBuchner/imagehash/master/imagehash/__init__.py)의 휘도/색/위치 정보 선택. | 독립 aHash 소형 구현에서 빨강과 파랑의 거리 0, RGBA 불일치. JPEG 재인코딩도 거리0/픽셀 불일치. threshold1의 유사 관계가 추이적이지 않은 (1,2,1) 거리 반례. ImageHash 패키지 실행으로 보고하지 않음. |
| 파일 객체와 경로 별칭 | [Windows hard link 문서](https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions). | 생성한 lab 파일의 하드링크는 같은 객체이고 쓰기가 공유됨. 후보에 경로 수와 unique_file_objects를 분리. 원본 파일을 링크하거나 이동/삭제하지 않음. 회수 가능 용량은 계산하지 않음. |
| 내용 식별자와 관찰 목록 분리 | [restic 설계](https://github.com/restic/restic/blob/master/doc/design.rst)의 콘텐츠 참조·불변 객체·snapshot 구조. | 백업 분야의 분해를 참고해 내용 해시, 상대 경로, 파일 객체·관찰 시각을 구분. restic 저장소 스냅샷을 원본 파일시스템 원자성으로 해석하지 않음. restic 설치·연결 미검증. |
| 출처를 가진 날짜 후보 | [Windows 파일 시각](https://learn.microsoft.com/en-us/windows/win32/sysinfo/file-times)과 R001 EXIF 태그 의미. | 시각은 변경 가능하며 촬영일/원본성의 증거로 자동 승격하지 않음. 명시한 촬영 태그의 recorded local date만 예시 bucket을 생성. 시간대·날짜 오류·충돌을 검토 사유로 유지. |

## 연결된 기능 재료와 원본 결과
[photo_material.py](../lab/R001/photo_material.py)의 scan → metadata/date 분석 → exact_groups → make_candidates 경로를 실제 실행했다. [대표 JSON](../lab/R001/results/original-scan-verified.json)은 8개 파일·동일 그룹1·후보9를 담는다. 그룹은 `copies/duplicate.jpg`, `session A/dated.jpg`이며 두 파일 객체·동일 763바이트·동일 SHA-256·실제 bytes 비교로 확인했다. 후보9개는 정확 중복 검토1, 날짜 bucket2, 메타데이터 검토3, 입력 검토3이다.

후보는 기능 교환 데이터이며 보존할 파일·목표 파일명·최종 경로를 정하지 않는다. 날짜 묶음도 recorded local date 예시로 정의했다. 이후 파일명 충돌 정책이나 실제 정리 동작은 사용자 범위 밖이므로 실행하지 않았다. 원본 및 기존 제품/입력 manifest의 전후 내용 해시가 같음을 메인 테스트와 최종 보존 결과에서 확인했다.

## 실제 실패에서 갱신한 구현
복제한 작업장 `lab/R002/repro/project/`에서 첫 재현은 3개 실패·3개 오류였다. 스캔이 모든 사본을 `file changed before read`로 잘못 거절했다. 값 확인 결과 dev/ino/size/mtime/birthtime는 같고 Path.stat와 os.fstat의 ctime가 달랐다. 원본 해시는 모두 동일했다.

[CPython v3.12.10 posixmodule.c](https://raw.githubusercontent.com/python/cpython/v3.12.10/Modules/posixmodule.c)의 win32_xstat는 birthtime을 ctime에 복사하고, [fileutils.c](https://raw.githubusercontent.com/python/cpython/v3.12.10/Python/fileutils.c)의 handle 경로는 ChangeTime을 사용한다. 메인의 최초 샘플에서 fstat ctime가 mtime와 같았다는 것은 그 샘플 관찰이고 일반 법칙이 아니다. 독립 조사자는 생성/변경 시각이 우연히 같아 최초 재현에 실패한 뒤 50ms를 두고 lab 파일 mtime을 설정해 계약 차이를 재현했다.

수정: API 간 비교는 dev/ino/size/mtime로, 같은 API의 읽기 전후 비교는 ctime를 포함해 수행한다. 읽은 바이트 길이도 사전 크기와 대조한다. 복사된 시각을 보존한 파일 읽기와 주입한 읽기 중 변경을 회귀 테스트로 추가했다. 최종 22개 테스트는 메인 작업장 0.620s, 복제 작업장 0.611s에 통과했다. [이전 실패 로그](../lab/R002/repro/project/.elenchus/lab/R001/repro-tests.txt), [수정 통과 로그](../lab/R002/repro/project/.elenchus/lab/R001/repro-tests-fixed.txt). 복제 재현은 같은 별도 venv를 사용한 경로/자료 독립 재현이며 새로운 OS 설치 검증은 아니다.

별도 대안 실험은 inode·size·mtime를 유지한 내용 변경이 단순 캐시를 속이는 것을 보였다. 위 수정으로 모든 경쟁 변경이 탐지된다고 주장하지 않는다. 최종 제품이 나중에 후보를 적용하려면 실제 시점의 내용 재검증과 쓰는 프로세스의 협력이 필요하다. 현재 기능은 작은 입력을 메모리 스냅샷으로 읽고 그 바이트끼리 비교하는 재료다.

## 독립 반례 실험과 메인 재확인
대안 조사자는 Pillow 11.3.0/별도 venv로 10개 체크를 통과했다. [상세 안내](../lab/R002/agent_alternatives/README.md), [첫 실제 결과](../lab/R002/agent_alternatives/run_20260908T102902324155Z/results.json). 메인은 복제 코드를 자신의 Pillow 12.3.0 venv로 실행했고 같은 10개 체크·하드링크 공유·PNG open 성공/load 실패를 재현했다. [메인 결과](../lab/R002/replay_alternatives/run_20260908T103243670358Z/results.json). 11.3→12.3에서 비교 코드의 getdata 폐기 경고가 나타났으며 현재 고정 버전 실행은 성공했다. 전 라이브러리/형식 호환성 보장으로 확대하지 않는다.

ctime 차이도 별도 복제 코드로 재현했다. [메인 ctime 결과](../lab/R002/replay_alternatives/ctime_20260908T103243898511Z/results.json). 원본의 내용·크기·mtime는 대안 실험 전후 동일했다. 심볼릭 링크/junction 경합·외부 경계 공격은 구현에서 정적 링크를 제외하지만 실제 플랫폼 전 조합을 시험하지 않았다.

## 판정과 열린 범위
독립 보고서 초안의 fdupes 읽기 오류 처리 주장은 메인이 원문을 재확인해 위 표처럼 정정했다. 보고서 동의만으로 근거를 확정하지 않았으며, 오류 처리를 포함한 직접 복사는 하지 않았다.

판정: **결론 가능**. 파일 동일성·픽셀 표현 일치·유사도·경로 별칭·관찰 시점이라는 다른 접근을 조사하고 반례로 구분했으며, 사용자 요청의 같은 파일 판별과 후보 JSON 기능을 구현·실행했다. 빠진 중요한 개념 비교나 접근 가능한 실패 원인 공백은 처리했다. 추가 일반 소개문보다 실제 사진·새 형식·대량 환경이 있어야 유사도 임계값/성능/최종 적용 조건을 판단할 수 있다.

미검증: HEIC/RAW, 색관리·HDR·고정밀 픽셀 의미, 실제 사진 유사도 임계값, 대규모 성능, 네트워크 FS, 완전한 동시 변경 방어, 실제 정리 동작. 사용자 목적의 성공 범위를 낮추어 이를 실행 성공으로 기록하지 않는다. 최종 라이브러리·저장소·스키마·파일명·동선은 이후 제작자가 선택한다. [인계 안내](../lab/R001/README.md).
