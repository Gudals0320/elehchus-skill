# Research R001: 로컬 사진 보관·탐색 접근 비교

- 상태: 작성 중
- 기준: ../idea.md
- 확인 날짜: 2026-09-07
- 영향: Phase 후보

## Repository 기준선

현재 과제는 구현 전 계획이다. 운영 범위에서 제품 접근·구현을 제외했으므로 제품 저장소 분석을 생략했다. request.md와 사용자가 후속 답변으로 전달한 preferences.md만 의도 기준선으로 읽었다. 다른 설치본·저장소·작업·테스트·이슈는 조사하지 않는다.

## Neutral brief

- 중립 질문: 여러 드라이브의 사진을 오프라인으로 훑고 비교·정리할 때 어떤 보관·탐색 접근과 제작 전략을 참고할까?
- 입력: Windows PC, JPEG·PNG·HEIC 약 5만 장, 두 드라이브와 외장 SSD, 촬영일 누락·오류 포함.
- 출력: 공개 제품 경험과 공개 구현 접근의 비교, 적용·제외·보류 이유, 사용자 선택을 위한 Research 권고와 후속 검증 질문. 제품·전체 실행 계획은 이번 산출물이 아니다.
- 사용자 경험: 여러 폴더를 선택해 날짜로 훑고 사진을 크게 비교한다. 인터넷 없이 사용하며 SSD 분리 중에도 이전에 본 사진 정보를 찾는다.
- 성공 조건: 화면과 저장 구조의 대안을 비교하고 현재 제약에 적용할 요소·부담·한계를 설명할 수 있음. 원본 변경은 명시적 적용 전 발생하지 않아야 함. 실제 속도·HEIC 호환·복구 정확성은 공개 자료로 보장할 수 없으며 환경 검증 전 미확인.
- 실패 조건: 특정 예시를 필수 구조로 고정함, 실제 관찰하지 않은 화면·속도를 검증됐다고 말함, 원본 자동 변경·유사 사진 자동 삭제를 포함함, 새 기능·비용·취향을 사용자 결정으로 확정함.
- 확정 제약: 개인용 Windows 로컬, 오프라인 탐색, 원본·메타데이터 명시적 적용, 이동을 선택하면 적용 전 목록과 실패 후 처리 추적, 삭제 후보의 나란히 비교와 사용자 선택. 계정·클라우드 업로드·공유·얼굴 인식·편집 제외. 조사에서 계정·유료 호출·실제 사진·설치·제품 변경 제외.
- 환경 사실: 현재 Windows PowerShell에서 작업 폴더의 Markdown을 읽고 작성할 수 있다. public web 검색·본문 조회 도구가 제공된다. 설치·실행·실제 사진 벤치마크는 수행하지 않는다.
- 미해결 질문: 기본 보관 방식, 화면 배치, 오프라인 미리보기 크기·보관량, 날짜 불명·오류 처리, 파일 이동 채택, 삭제·복구 구체 행동, 엔진·DB·성능 기준.

## 사용자 기술 언급 분류

| 언급 | 분류 | 처리 |
|---|---|---|
| Windows, JPEG·PNG·HEIC, 로컬·오프라인 | 필수 제약·현재 환경 | 비교의 적용 조건 |
| digiKam | 예시 | 독립 탐색의 필수 조건에서 제거; 여러 후보 중 검토 가능 |
| 폴더 직접 관리, 별도 보관함 | 후보 | 둘의 차이와 다른 접근을 함께 탐색 |
| 엔진·DB | 미정 | 특정 기술을 전제로 하지 않음 |

## 증거 계획

| 증거원 | 상태 | 이유 | 바뀔 수 있는 결정 |
|---|---|---|---|
| Repository | 생략 | 구현 전 과제이며 제품 접근 제외 | 기존 코드 연동 판단은 하지 않음 |
| Independent exploration | 필요 | 제품 경험과 제작 전략은 독립 질문 분담에 이점 있음 | 구현 비용·안전 조건 |
| External evidence | 필요 | 공개 제품·구현의 접근 범주, 공식 화면과 실패 조건 확인 | 보관·탐색·정리 권고 |
| Browser Evidence | 생략 | 계정·개인화 환경 관찰을 요청하지 않았고 금지됨 | 공개 화면만 참고 |
| Lab | 생략 | 현재는 비교 Research; 실제 사진·설치·제품 구현 제외. 환경 성능·복구 실행 검증은 별도 후속 과제로 유지 | 실제 속도·정확성·오프라인 복구는 미검증 |

## Subagent 역할·범위·지원 한계

- 사용자 후속 답변이 역할 분담을 허용했다. collaboration.spawn_agent는 fork_turns="none"을 지원하며 대화 이력 없이 중립 brief만 전달했다.
- 공개 구현 역할: 카탈로그·오프라인 참조, 중복·유사성 구분, 안전한 파일 이동·복구의 공개 코드·공식 기술 설명 조사. 06:30 UTC까지 회신 요청.
- 메인 역할: 제품 경험·접근 범주 탐색, 공개 시각 관찰, 결정적 근거 직접 재확인, 결과 통합.
- 지시상 제한: 공개 읽기 전용, 파일 변경·설치·제품 구현·계정·실제 사진·브라우저 제어·재위임 금지. 도구 수준의 별도 읽기 전용 강제를 선언하지 않는다.

## 조사 목적과 범위

탐색·벤치마킹이 주목적이다. 직접 폴더 탐색, 참조형 카탈로그, 파일을 가져오는 관리형 보관함을 비교하고 날짜 탐색·큰 사진 비교 경험을 분리해서 살핀다. 인접 사례로 중복 전문 도구와 파일 이동 API를 검토한다. 제품 전체 채택이나 코드·에셋 복사는 결정하지 않는다.

## Web Evidence

### 조사 깊이와 이유

후보 비교·복합 제약·파일 안전성이 관련되므로 전체 기록을 사용한다.

### Claim map

| 주장·열린 검증 질문 | Verdict 영향 | 필요한 출처 역할 | 최신성 기준 | 적용 환경 | 반증 조건 |
|---|---|---|---|---|---|
| C1 기존 폴더 참조와 로컬 카탈로그·미리보기를 결합하면 원본 이동 없이 오프라인 탐색을 구성할 수 있는가 | 기본 구조 | 공식 동작 문서·관련 구현 | 현재 공개 문서·코드 확인일 | Windows·외장 드라이브 | 원본 복사 필수·분리 시 정보 소멸 |
| C2 날짜 탐색·폴더 탐색·큰 비교 화면은 보관 구조와 별개로 조합 가능한가 | 화면 선택 | 공식 화면·설명 | 현재 공개 장면 | 데스크톱 사진 탐색 | 특정 저장 방식에만 가능·화면 미확보 |
| C3 관리형 보관함·직접 탐색은 어떤 장점과 손실을 갖는가 | 대안 비교 | 공식 가져오기·참조·복구 문서 | 현재 제품 문서 | 사용자 조건에 대한 적용 한정 | 복사량·재연결·운영 부담을 누락 |
| C4 정확한 중복과 시각적 유사성, 파일 이동·메타데이터 처리는 별도 검증·적용 단계가 필요한가 | 원본 안전·범위 | 코드·공식 API·실패 경험 | 현재 구현·API 계약 | Windows·분리 드라이브 | 유사 판정이 동일성 증명·이동이 언제나 원자적 |
| C5 JPEG·PNG·HEIC 5만 장의 실제 성능·오프라인 비교·실패 복구를 공개 주장만으로 보장할 수 있는가 | 검증 보류 | 지원 범위·재현 조건 | 사용 환경 일치 필요 | 사용자 PC·실제 데이터 | 동등한 환경의 검증이 없음 |

### Retrieval plan

- 초기 접근 범주 검색: `open source photo manager Windows offline catalog removable drives referenced files managed library`, `open source photo organizer Windows timeline light table compare photos folders`, `open source duplicate image finder similar photos preview hash HEIC Windows`.
- 후보 검증: 발견된 공식 홈페이지·매뉴얼·GitHub에서 저장·인덱스·오프라인·비교·날짜·가져오기 동작을 확인한다. digiKam은 예시로 별도 검토하고 다른 범주를 제한하지 않는다.
- 반대 근거 검색: offline missing removable drive rescan, referenced files missing, managed import copy disk, similar images false positives, HEIC unsupported, cross-volume move failure. 공개 공식 문서·원 작성자의 이슈 우선.
- 화면 관찰: 공식 매뉴얼의 화면 이미지나 공개 페이지를 별도 조사 탭에서 관찰한다. 기존 사용자 탭·로그인은 사용하지 않는다. 시각 자료를 저장하지 않는다.
- 접근 실패 시: 공식 다른 페이지·공개 raw/API·공개 이미지·새 탭 렌더링을 사용한다. 로그인·CAPTCHA·404는 해당 경로 terminal로 남기며 우회하지 않는다.

## 탐색·벤치마킹과 적용

다음 판정은 에이전트의 Research 제안이다. 사용자의 제품 선택으로 확정하지 않았다. 본문·코드 직접 확인은 읽기 관찰이며 설치·실행 검증을 뜻하지 않는다.

| 접근법·대표 사례 | 실제 근거·관찰 수준 | 우리 조건에서 얻는 것·부담 | 권고 |
|---|---|---|---|
| 필요한 폴더를 그때 읽고 전문 도구로 중복 검사 | Czkawka 공식 FAQ는 탐지 결과를 파일로 내보낼 수 있으나 GUI에서 다시 이어 보려면 재스캔해야 한다고 설명한다. [S9] | 새 도구를 작게 만들거나 기존 도구를 함께 쓰기 쉽다. 지속 카탈로그가 없는 형태만으로는 SSD 분리 후 이전 정보 탐색을 충족하지 못한다는 추론 | 단순 대안으로 비교 유지; 전체 요구의 단독 해법으로는 부족 |
| 기존 폴더를 참조하고 로컬 카탈로그 유지: Diffractor·Lap·digiKam | 공식 문서가 원본 위치와 검색용 정보를 분리한다. Diffractor는 분리된 드라이브의 정보를 오프라인 상태로 유지한다고 명시한다. [S1,S3,S4,S6] | 일괄 복사 없이 시작하고 폴더·날짜·비교 화면을 조합할 수 있다. 인덱스 생성·보관, 외부 이동 감지·재연결을 책임져야 한다 | 현재 조건의 우선 검토안 |
| 관리형 보관함으로 복사하거나 가져오기: Shotwell·Apple Photos | Shotwell은 복사와 제자리 등록을 구분한다. Apple Photos는 기본 복사와 참조 파일 옵션, 참조 파일의 분리·이름 변경·백업 한계를 설명한다. [S7,S8] | 하나의 소유 위치를 만들기 쉬워진다는 추론. 현재 5만 장의 최초 복사 공간·시간과 원래 폴더와의 관계를 추가 결정해야 한다. 두 제품은 각각 Linux/GNOME·Mac의 인접 사례로만 사용 | 일괄 보관 위치를 원할 때 유력; 지금은 복사·이동을 기본으로 제안하지 않음 |
| 로컬 서버와 브라우저: PhotoPrism | 공식 문서는 기존 원본 인덱싱과 선택적 복사·이동 가져오기를 구분하며 Windows를 포함한 Docker Compose 경로를 안내한다. [S18,S19,S20] | 브라우저 UI를 쓸 수 있는 별도 제작 경로다. 개인 Windows 도구에는 서비스·컨테이너·볼륨 운영이 더해진다. 로컬 서버를 곧 클라우드라고 단정하지 않는다 | 현재 목적에서는 우선순위 낮음; 계정 없는 구체 배포 가능성은 검증하지 않았고 채택하지 않음 |

기존 제품을 그대로 쓰는 선택도 남아 있다. 장점은 제작·유지 부담을 줄이는 것이고, 손실은 원본 명시적 적용과 SSD 분리 동작을 원하는 수준으로 통제하려면 제품별 설정·검증이 필요하다는 점이다. 이번에 설치·구매하거나 사용 전환을 권고하지 않는다.

### 사용자 경험의 실제 비교 자료

| 장면 | 직접 관찰한 것 | 자료의 설명·추론·미확인 |
|---|---|---|
| [Diffractor 공식 화면](https://www.diffractor.com/static/images/screenshot.png) | 새 공개 조사 탭에서 정지 이미지를 봤다. 가운데 큰 사진, 오른쪽 썸네일 모음, 위쪽 경로, 아래 사진 정보가 함께 있다 | 목록과 큰 미리보기를 한 화면에 둘 수 있는 사례. 실제 전환 속도·5만 장 사용감은 관찰하지 않음 |
| [digiKam 타임라인](https://docs.digikam.org/en/left_sidebar/timeline_view.html) | 공식 페이지의 화면에서 왼쪽 기간 막대와 가운데 사진 목록을 확인했다 | 문서는 기간 선택을 검색으로 연결한다고 설명한다. 사진을 날짜 폴더로 이동시켜야 한다는 뜻은 아님. 애니메이션 전체·실제 조작은 검증하지 않음 |
| [digiKam Light Table](https://docs.digikam.org/en/light_table/lighttable_overview.html) | 상단 후보 띠, 두 개의 큰 사진 영역, 양쪽 사진 정보가 있는 정지 화면을 확인했다 | 별도 비교 창을 쓰는 사례. 창 분리를 사용자의 취향으로 확정하지 않음 |
| [darktable culling](https://docs.darktable.org/usermanual/development/en/lighttable/lighttable-modes/culling/) | 문서 본문을 읽었으며 실제 앱 동작은 보지 않음 | 문서는 나란히 비교와 동기화된 확대·이동을 설명하며 큰 미리보기 캐시의 공간 부담을 알린다. 개발 버전 문서여서 현재 배포판 전부에 일반화하지 않음 |

이 사례에서 가져올 수 있는 것은 날짜로 범위를 좁힌 뒤 큰 비교로 이어가는 흐름이다. 폴더 탐색과 타임라인의 공존, 비교 창의 분리 여부, 두 장 또는 여러 장 비교는 모두 제품 선택으로 미정이다. 지도·통계·평가·태그 등 화면에 보였다는 이유만으로 기능을 추가하지 않는다.

### 제작 방법 비교

| 전략·참고 | 확인한 근거 | 적용 제안·수정 부담 |
|---|---|---|
| 필요한 범위의 데스크톱 앱과 별도 검색 데이터 | Lap은 Tauri/Rust·Vue·SQLite 구조와 로컬 정리 정보를 설명한다. Diffractor 구현 문서는 C++20·Direct2D/Direct3D·SQLite와 UI 밖의 스캔·디코딩·DB 작업을 설명한다. [S2,S3] | 프레임워크는 동등한 후보로 남긴다. 항상 연결된 로컬 위치에 사진 목록을 저장하고, 무거운 스캔과 화면 반응을 분리하는 구조를 우선 제안한다. Windows 패키징과 HEIC 디코더, 메모리 예산 검증이 필요 |
| 중복·유사 이미지 코어의 부분 재사용 | Czkawka의 `check_files_hash`는 사전·전체 해시 경로를, `collect_image_file_entry`는 디코딩 후 시각 해시 경로를 사용한다. 코어 README는 UI 의존이 없고 MIT라고 명시한다. [S10,S11,S13] | 엔진 후보로 검토할 수 있으나 캐시를 영속 사진 목록으로 쓰지 않는다. Windows HEIC 준비 상태와 오류·취소·진행·사용자 선택 보관의 연결을 먼저 검증해야 함 |
| 기존 사진 앱 전체를 수정 | Lap의 공개 저장소에는 촬영·분류·편집·AI 등 현재 제외 범위를 넘는 기능과 GPL-3.0-or-later 표시가 있다. [S3] | 완성된 탐색 경험을 얻지만 전체 구조와 업데이트를 이해·유지해야 한다. 현재 기능 일부만 필요한 도구에는 통째 복제보다 부분 패턴 참고를 먼저 검토할 이유가 있음. 포크·코드 복사는 하지 않음 |
| 파일 처리 알고리즘 참고 | rclone `copy.verify`·`copy.copy`와 `operations.move`의 복사 후 확인·이름 확정·원본 삭제 경로를 읽었다. [S14,S15] | 제품에 rclone을 넣기로 하지 않았다. 파일별 처리 상태를 나누는 전략을 참고하되, 기존 대상 덮어쓰기·백업·중단 후 상태 대조는 별도 설계가 필요 |

코드·에셋 재사용은 승인·수행하지 않았다. 라이선스 표시는 조사한 구성요소 범위의 문서 사실이다. 선택한 버전과 의존성의 배포 조건은 실제 재사용 후보가 좁혀질 때 다시 확인한다.

## 시험한 주장과 반증 조건

실행 실험 없이 공개 동작 계약과 코드를 검토했다. C1은 복사 없는 카탈로그 및 오프라인 보존 사례로 지지된다. C2는 원본 위치와 날짜 검색·큰 비교가 분리된 사례로 지지된다. C4의 반증 후보였던 ‘유사도 0이면 같은 파일’과 ‘이동 API 성공이면 원본은 없어졌다’는 각각 시각 해시·Windows API 계약에 의해 반박된다. C5는 사용자 PC와 데이터에서 실행한 근거가 없어 보장할 수 없다.

## External evidence와 반대 근거

- **SSD 부재와 삭제를 구분해야 한다.** Czkawka 캐시 정리의 `effective_delete_outdated && !path.exists()` 조건을 직접 읽었다. 일반 스캔 캐시는 오프라인 정보 보존 계약이 아니다. Diffractor 컬렉션 문서의 오프라인 보존과 차이가 있다. [S4,S12]
- **날짜에는 출처가 필요하다.** Diffractor는 촬영 내용의 날짜·파일 생성·수정 날짜를 분리하고 날짜가 온 태그를 보여 준다고 설명한다. 현재 도구에도 같은 구분을 참고할 수 있으나 날짜 없는 사진을 어느 날짜로 대신 분류할지는 미정이다. 잘못된 촬영일을 원본에서 자동 수정하자는 제안은 하지 않는다. [S1]
- **시각적 유사성은 동일 파일 증명이 아니다.** Czkawka FAQ는 흑백 변환·단색 면적의 오탐과 형식별 지원 차이를 설명한다. 전체 해시와 시각 해시를 별도 증거로 보여 주는 것이 사용자 직접 선택 원칙에 맞는다. [S9,S10,S11]
- **‘비슷함’의 범위는 아직 열려 있다.** Czkawka의 시각 해시는 같은 컷의 변형을 찾는 후보이고, Lap의 로컬 시각 검색은 다른 후보다. 내용이 비슷한 장면까지 찾을지, 연사·변환본까지만 찾을지는 사용자 응답으로 정하지 않았다. 정확도·모델·임계값 결론은 보류한다. [S3,S9]
- **다른 드라이브로의 이동에는 부분 완료가 있다.** Microsoft MoveFileExW의 `MOVEFILE_COPY_ALLOWED`는 복사 성공 후 원본 삭제 실패에서도 성공 반환이 가능하다고 명시한다. 따라서 단일 성공 표시 대신 원본·임시 대상·확정 대상의 관찰 결과가 필요하다는 추론이다. [S17]
- **임시 파일만 쓰면 안전하다는 결론도 성립하지 않는다.** rclone은 전송 완료 후 최종 이름으로 바꿀 때 기존 대상을 덮어쓸 수 있고, move 보고서에는 실제 완료 내역과 차이가 생길 수 있다고 설명한다. 적용 전 충돌 검토와 확인된 처리 이력은 별도로 필요하다. [S16,S22]
- **DB 트랜잭션은 사진 파일까지 한꺼번에 되돌리지 않는다.** SQLite 원문이 보장하는 것은 DB 변경의 원자성이다. 파일 복사·삭제와 기록 사이에 종료된 경우 재시작 시 실제 상태를 대조해야 한다는 추론이다. [S23]
- **오프라인 정보와 원본 해상도 비교는 다르다.** Adobe는 원본이 분리됐을 때 별도의 Smart Preview를 사용할 수 있다고 설명한다. 현재 사용자는 이전 사진의 정보를 원했으며 큰 미리보기 상시 보관량은 정하지 않았다. 썸네일·큰 미리보기의 해상도·기간·공간을 별도 선택으로 남긴다. [S21]
- **제품 지원 설명은 실행 검증이 아니다.** Lap의 규모·HEIC 표기, digiKam의 DB 규모 안내를 우리 PC 성능 보장으로 쓰지 않는다. Czkawka Core README의 Windows HEIC 준비 제약 때문에 기본 바이너리로 세 형식이 모두 동작한다고도 확정하지 않는다. [S3,S5,S13]

## 결과 통합과 근거 재확인

공개 구현 agent가 반환한 Czkawka 코드·FAQ·Core README, rclone 코드·move/임시 파일 설명, Microsoft API, SQLite 문서를 메인이 직접 열고 결정적 본문·심볼을 다시 확인했다. digiKam 최신 컬렉션 코드는 Invent raw·blob 경로 모두 확보하지 못했다. agent가 읽은 보관된 GitHub 미러는 최신 구현의 근거로 채택하지 않고 현재 공식 매뉴얼과 독립 제품 문서로 구조 비교의 근거를 제한했다. 같은 제품의 README·매뉴얼·코드는 독립 사용 사례 수로 중복 계산하지 않는다.

## Evidence matrix와 gap loop

| 주장 | 지지 근거 | 반대 근거 | 공개 화면 관찰 | 적용 범위·상태 | 남은 공백 |
|---|---|---|---|---|---|
| C1 원본 유지·카탈로그 | S3,S4,S6,S21 | S8의 경로 변경·참조 백업 한계, S12의 캐시 제거 | Diffractor 공개 화면 | 범위 제한: 구조 선례 확인 | 우리 앱의 드라이브 재연결·영속 정보 보존 검증 |
| C2 화면과 저장 구조 분리 | S1,S3,S24,S25,S26 | 큰 캐시의 공간 부담 S26 | 날짜 막대·비교·목록 옆 미리보기 | 확인: 조합 가능성. 취향은 미정 | 사용자가 선호할 화면, 실사용 속도 |
| C3 관리형·참조형 대안 | S7,S8,S18,S19,S20 | 복사·경로 재연결·서버 운영 부담 | 관리형 앱의 전체 흐름은 미관찰 | 범위 제한: 문서상의 소유·입력 동작 비교 | 실제 가져오기 UX 검증, 관리형 선택 시 공간 |
| C4 안전 처리 | S9~S17,S22,S23 | 시각 오탐, 캐시 소멸, 원본 남음 성공, 예측 로그 | 실제 파일 작업 미수행 | 확인: 분리할 책임과 반례. 안전 구현 자체는 미검증 | 종료·충돌·잠금·재연결 실험 |
| C5 실제 성능·형식·복구 보장 | 지원 설명 S3,S5,S13 | 환경 불일치·HEIC 제약 | 정지 화면만 | 근거 부족 | 합의 후 검증 과제로 연결; 성능 숫자·호환성 보장 금지 |

초기에는 폴더·보관함·중복 전문 도구를 발견했다. 첫 검증 후 영속 카탈로그와 재생성 캐시의 차이가 선택에 중요해 S4·S12를 확인했다. 다음으로 원본 분리 중 큰 비교 가능 범위를 S21에서 확인했고, 파일 이동의 실제 완료 판정을 S17·S22·S23으로 좁혔다. 마지막으로 서버형과 선택적 가져오기 사례 S18~S20을 확인했다. 다음 공개 검색으로 구조 권고가 바뀔 가능성은 낮으며, 남은 큰 공백은 사용자 선택과 실제 실행 환경의 검증이다.

## 접근 기록

아래 S 번호는 출처 목록의 정확한 URL을 가리킨다. 모든 확인일은 2026-09-07이다.

| 주장 | 출처·URL | 접근 경로 | 본문 확보 | 증거 판정 | 실패·terminal reason | 남은 공개 경로 |
|---|---|---|---|---|---|---|
| C1~C5 | S1~S8, S18~S26 | 공개 검색→공식 HTML·GitHub 본문→필요한 위치 재조회 | 본문 확보 | 해당 제품 계약·구조·한계만 지지 | 일부 GitHub 공통 오류 문구가 있었으나 관련 Markdown 본문은 실제 확보 | 추가 사용후기·실행 관찰은 현재 구조 권고의 전제 아님 |
| C4 | S9~S17,S22,S23 | 공식 raw 코드·FAQ·API·문서, find로 심볼/조건 확인 | 본문 확보 | 지지·반박 범위를 Evidence matrix에 연결 | Microsoft 상단에 권한 안내가 있었지만 API 본문과 flag 설명은 확보 | 권한·로그인 없이 필요한 본문 확보; 추가 경로 불필요 |
| C2 | digiKam 공식 이미지 링크 | web click | 미확보 | 이미지 URL만으로는 시각 근거로 미채택 | Internal Error | 같은 공식 HTML을 새 공개 CUA 탭으로 열어 실제 이미지 관찰 완료 |
| C3 | https://help.gnome.org/users/shotwell/stable/other-files.html.en | web open | 미확보 | 미사용 | Internal Error, 원인 미판명 | 공식 프로젝트의 S7로 동일 import 질문 확인 완료 |
| C1 | https://invent.kde.org/graphics/digikam/-/raw/master/core/libs/database/collection/collectionscanner_scan.cpp | web open | 미확보 | 최신 코드 미사용 | Internal Error | blob 공개 경로 시도 |
| C1 | https://invent.kde.org/graphics/digikam/-/blob/master/core/libs/database/collection/collectionscanner_scan.cpp | web open | terminal | 최신 코드 미사용 | safe-to-open 검사에서 non-retryable error | 우회하지 않음. 현재 코드 채택 결론 보류, 공식 문서·독립 제품 S4로 구조만 비교 |
| 제작 후보 | https://github.com/julyx10/lap/tree/main/src-tauri/src | web open | 부분 확보 | 폴더 페이지만; 구체 소스 구현 주장의 근거로 사용하지 않음 | 관련 코드 본문 미검토 | 핵심 구현은 확보한 Czkawka·rclone과 작성자 기술 문서로 범위를 제한 |

## Browser Evidence와 공개 관찰 환경

사용자 계정의 Browser Evidence는 생략했다. 공개 시각 관찰은 CUA getBrowser({url})로 선택된 Chrome extension ID 1에서 새 탭 552629695를 만들어 진행했다. 다른 탭·방문 기록·계정은 조회하지 않았다. getAXState·getScreenshot 기능이 실제로 동작했다. Diffractor 정지 이미지→digiKam Light Table→digiKam 타임라인을 조회했으며 화면·DOM·HTML은 파일로 저장하지 않았다. 공개 원문 화면을 본 것이며 설치된 제품·속도·사용자 환경의 검증은 아니다. 도구가 제공한 권한은 일반 브라우저 제어이며 observation-only 경계는 이 작업의 지시상 제한이다.

## Web closure와 Discovery 완료 판정

| 기준 | 판정·근거 |
|---|---|
| 핵심 주장·출처 연결 | 완료. C1~C5의 범위·반례·미확인을 표에 연결했고 본문과 코드 조건을 직접 확인했다 |
| 깊이·접근·반대 근거 | 완료. 전체 Claim map·계획·접근 기록·matrix를 유지했다. 원본·캐시·이동·오프라인 비교의 반례를 검토했다 |
| 독립 근거 | 카탈로그는 Diffractor·Lap·digiKam·Adobe, 보관형은 Shotwell·Apple·PhotoPrism을 비교했다. 특정 API 자체 계약은 Microsoft 원문이 통제하므로 동일 계약의 형식적인 제2 출처를 요구하지 않는다 |
| 접근법 비교 | 직접 스캔, 참조형 카탈로그, 관리형 가져오기, 로컬 서버, 기존 도구 활용을 비교했다 |
| 적합한 직접 근거 | 화면 배치는 공개 정지 화면, 파일 처리 전략은 코드, 동작은 공식 설명으로 관찰 수준을 구분했다. 실제 동작·속도 관찰 완료로 확대하지 않는다 |
| 적용 가능성 | 원본 유지, 영속 정보·캐시 분리, 포맷 준비, 재연결, 파일별 적용·이력 책임과 부담을 명시했다 |
| 결정 영향 | 우선 검토안과 낮은 우선순위·보류 이유를 제시한다. 사용자 미응답을 채택으로 바꾸지 않는다 |
| 종료 타당성 | 현재 질문의 구조 비교는 결론 가능. 추가 후보 이름보다 미리보기 범위·유사성 의미·파일 이동 선택과 실제 환경 검증이 더 크게 결과를 바꾼다. 그 선택과 실험은 아래 보류에 연결했다 |

## Lab 관찰 의미

Lab은 실행하지 않았다. 성능, HEIC 디코딩, SSD 분리·재연결, 파일 충돌·전원 차단·잠금·복구는 검증 완료가 아니다. 공개 코드 읽기를 테스트 통과로 기록하지 않는다.

## Verdict

- 판정: **결론 가능 — 보관·탐색 접근의 비교와 제작 전략 권고 범위.** 특정 앱·DB·엔진의 최종 채택, 화면 선호, 실제 성능·복구 성공은 결론 보류다.
- 권고: **기존 원본 폴더를 참조하고, 항상 연결된 로컬 위치에 영속 사진 목록을 두는 방식**을 다음 계획의 우선 검토안으로 삼는다. 원본 일괄 복사 없이 여러 드라이브를 아우르고 SSD 분리 때 이전 정보를 유지한다는 목적에 맞는다.
- 근거: S3·S4·S6의 참조 구조, S21의 별도 오프라인 표현, S7·S8·S19의 가져오기 선택 구분.
- 반대 근거: 로컬 목록도 동기화·재연결·보관 비용이 필요하다. 관리형은 일관된 소유 위치를 원하는 경우 더 적합할 수 있다. 카탈로그나 미리보기만으로 원본 백업·원본 해상도 비교를 대신할 수 없다.
- 단순화 제안: 보기·비교·후보 선택부터 다루고 실제 이동은 별도 선택으로 남긴다. 구현·실패 복구 부담을 줄이는 대신 폴더 자체가 자동 정돈되는 결과는 얻지 못한다. 사용자는 아직 이 축소안을 승인하지 않았다.
- 한계: 정지 화면과 문서·공개 코드만 확인했다. 5만 장의 실제 스캔·스크롤·HEIC·실패 복구·로그인 없는 서버 배포를 실행하지 않았다. 현재 사용자 사진·드라이브·기존 브라우저 탭은 사용하지 않았다.
- 신뢰도: 보관 구조 권고 **중간 이상**, 파일 처리 책임 분리 **높음(공식 계약·코드 근거)**, 실제 성능·형식 호환·유사 판정 품질 **미검증**.
- 사용자 확인 전에는 문서 상태를 작성 중으로 유지한다. Research 권고를 계획 기준으로 사용할지 확인할 질문 하나를 응답 2에 제시한다.

## Idea 변경과 Execution 영향

Idea에는 확인된 사용자 제약을 유지하고 이 Research 링크와 미승인 권고만 추가한다. 상세 결론은 이 문서에 둔다. 사용자 요청대로 execution.md와 Phase·Build 전체 합의는 만들지 않는다. 영향은 Phase 후보로 유지한다.

## 보류·다음 검증

| 공백 | 다음 행동·선행 조건 |
|---|---|
| 원본 유지·로컬 목록이라는 권고의 사용자 채택 | 현재 Research 결과 확인 질문. 수락 전 확정하지 않음 |
| SSD 분리 때 정보만·썸네일·큰 미리보기 중 범위 | 다음 Idea 인터뷰에서 사용자 결과·공간 부담을 비교해 선택. 고해상도 캐시 자동 생성 미승인 |
| 비슷함이 변환본·연사·내용 유사 중 어느 범위인지 | 다음 사용자 결정. 그 범위에 맞는 샘플과 오탐·누락 검증을 이후 계획에 연결 |
| 날짜 없음·틀림 | 원본 값과 출처 표시를 참고안으로 유지. 대체 날짜·사용자 정리값·원본 메타데이터 적용 여부를 다음에 합의 |
| Windows HEIC·JPEG·PNG와 규모 | 검증 Build 후보: 실제 승인된 환경에서 공개·합성 사진과 형식별 데이터로 디코딩·회전·실패 표시·스캔/탐색 자원을 확인. 지금 실행하지 않음 |
| SSD 분리·문자 변경·재연결 | 검증 Build 후보: 매체 부재·파일 부재를 구분하고 이전 정보가 남는지 시험. 제품 구조를 확정하기 전에 수행할 조건으로 제안 |
| 파일 이동·삭제·복구 | 이동 채택 시 충돌·원본 변경·잠금·중단·용량 부족·원본 삭제 실패·재실행을 검증. 사전 목록과 완료 이력·실제 파일을 대조. 이 Build는 아직 합의되지 않음 |
| 엔진·DB·프레임워크·비용 | 목적을 충족하는 후보를 환경 검증 뒤 선택. 새 의존성·계정·구매·유료 호출 승인 없음 |

## 출처

- S1 [Diffractor 사용자 문서: 날짜·비교·파일 작업](https://www.diffractor.com/docs)
- S2 [Diffractor 작성자 구현 설명: System shape, Async execution, thumbnail pipeline](https://github.com/diffractor/diffractor/blob/master/docs/implementation.md)
- S3 [Lap README: Features, Metadata/Collections, Architecture, License](https://github.com/julyx10/lap)
- S4 [Diffractor Collections: §8 Truth, staleness, and honesty](https://github.com/diffractor/diffractor/blob/master/docs/collections.md)
- S5 [digiKam Database Settings](https://docs.digikam.org/en/setup_application/database_settings.html)
- S6 [digiKam Collections Settings](https://docs.digikam.org/en/setup_application/collections_settings.html)
- S7 [Shotwell: Importing from your hard disk](https://www.shotwell-project.org/doc/html/import-file.html)
- S8 [Apple Photos: 파일의 보관 위치와 참조 파일](https://support.apple.com/en-gb/guide/photos/pht1ed9b966d/mac)
- S9 [Czkawka 공식 FAQ: Similar Images, Saving & Loading, Duplicate Detection](https://raw.githubusercontent.com/qarmin/czkawka/master/instructions/FAQ.md)
- S10 [Czkawka exact duplicate 코드: check_files_hash, full_hashing](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/src/tools/duplicate/core.rs)
- S11 [Czkawka similar images 코드: collect_image_file_entry](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/src/tools/similar_images/core.rs)
- S12 [Czkawka cache 코드: effective_delete_outdated](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/src/common/cache.rs)
- S13 [Czkawka Core: Requirements, Windows, License](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/README.md)
- S14 [rclone copy.go: verify, copy](https://raw.githubusercontent.com/rclone/rclone/master/fs/operations/copy.go)
- S15 [rclone operations.go: move](https://raw.githubusercontent.com/rclone/rclone/master/fs/operations/operations.go)
- S16 [rclone move: logger flags의 한계](https://rclone.org/commands/rclone_move/)
- S17 [Microsoft MoveFileExW: MOVEFILE_COPY_ALLOWED](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw)
- S18 [PhotoPrism Indexing Originals](https://docs.photoprism.app/user-guide/library/originals/)
- S19 [PhotoPrism Import to Originals](https://docs.photoprism.app/user-guide/library/import/)
- S20 [PhotoPrism Setup](https://docs.photoprism.app/getting-started/)
- S21 [Adobe Lightroom Classic Smart Previews](https://helpx.adobe.com/lightroom-classic/desktop/viewing-photos/lightroom-smart-previews.html)
- S22 [rclone --inplace](https://rclone.org/docs/#inplace)
- S23 [SQLite Atomic Commit](https://sqlite.org/atomiccommit.html)
- S24 [digiKam Time-Line View](https://docs.digikam.org/en/left_sidebar/timeline_view.html)
- S25 [digiKam Light Table Overview](https://docs.digikam.org/en/light_table/lighttable_overview.html)
- S26 [darktable culling, development manual](https://docs.darktable.org/usermanual/development/en/lighttable/lighttable-modes/culling/)
