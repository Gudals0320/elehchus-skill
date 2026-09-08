[Elenchus · 진행 중]

Research의 권고는 **원본은 기존 폴더에 두고, 사진 정보는 PC의 로컬 카탈로그에 보관하는 방식**입니다. 여러 드라이브를 모아 보고 SSD가 빠져도 이전 정보를 찾으려는 조건에 잘 맞습니다. 아직 사용자 확정 결정은 아닙니다.

폴더·타임라인은 **보는 방식**, 참조·복사·이동은 **보관 방식**이므로 따로 선택할 수 있습니다.

| 비교한 접근 | 얻는 것 | 현재 조건에서의 부담 |
|---|---|---|
| 폴더를 그때 읽고 중복 전문 도구 사용 | 작게 시작하거나 기존 도구를 활용하기 쉬움 | 지속 목록이 없으면 SSD 분리 후 탐색이 어려움. Czkawka도 저장한 결과를 GUI에서 이어 보려면 재스캔해야 함. [공식 FAQ](https://raw.githubusercontent.com/qarmin/czkawka/master/instructions/FAQ.md) |
| 기존 폴더 + 로컬 카탈로그 | 원본 일괄 복사 없이 검색·분류 가능 | 인덱스 보관과 외부 이동·재연결 처리 필요. Diffractor·Lap·digiKam에서 참고할 구조를 확인함. [Diffractor](https://github.com/diffractor/diffractor/blob/master/docs/collections.md), [Lap](https://github.com/julyx10/lap), [digiKam](https://docs.digikam.org/en/setup_application/collections_settings.html) |
| 별도 보관함으로 가져오기 | 보관 위치를 모으기 쉬움 | 최초 복사 공간·시간과 기존 폴더 처리 결정이 필요. Shotwell과 Apple Photos의 복사·참조 선택을 인접 사례로 비교함. [Shotwell](https://www.shotwell-project.org/doc/html/import-file.html), [Apple](https://support.apple.com/en-gb/guide/photos/pht1ed9b966d/mac) |
| 로컬 서버 + 브라우저 | 서버형 사진 관리 구조 활용 가능 | 개인 Windows 도구에는 서버·컨테이너 운영 부담이 추가됨. PhotoPrism도 기존 원본 인덱싱과 선택적 가져오기를 구분함. [가져오기](https://docs.photoprism.app/user-guide/library/import/), [설치 구조](https://docs.photoprism.app/getting-started/) |

화면은 [Diffractor의 목록 옆 큰 미리보기](https://www.diffractor.com/static/images/screenshot.png), [digiKam의 날짜 막대](https://docs.digikam.org/en/left_sidebar/timeline_view.html), [두 사진 비교 화면](https://docs.digikam.org/en/light_table/lighttable_overview.html)을 실제 공개 이미지로 확인했습니다. 날짜로 범위를 좁히고 큰 비교로 이어가는 흐름을 참고할 수 있습니다. 정지 화면 관찰이므로 전환 속도나 사용감까지 검증한 것은 아닙니다.

제작에서는 다음 세 가지를 분리하는 것이 핵심입니다.

- **사진 목록과 재생성 캐시:** SSD가 없다는 이유로 이전 정보를 지우지 않아야 합니다. 큰 미리보기를 별도로 저장하면 분리 중에도 볼 수 있지만 공간을 더 씁니다. 정보·썸네일·큰 미리보기 중 어디까지 보관할지는 미정입니다. [오프라인 미리보기 사례](https://helpx.adobe.com/lightroom-classic/desktop/viewing-photos/lightroom-smart-previews.html)
- **동일 파일과 닮은 사진:** 전체 파일 해시와 시각 해시는 다른 증거입니다. Czkawka는 두 처리 경로를 분리합니다. ‘비슷함’이 변환본·연사·내용이 비슷한 장면 중 어디까지인지는 다음에 정해야 합니다. [전체 해시 코드](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/src/tools/duplicate/core.rs), [시각 해시 코드](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/src/tools/similar_images/core.rs)
- **적용 전 목록과 실제 완료 이력:** Windows의 다른 드라이브 이동은 복사 후 원본 삭제가 실패해도 API가 성공을 반환할 수 있습니다. 이동을 넣는다면 복사 확인·대상 확정·원본 삭제 확인을 나눠 기록하고 재시작 때 실제 파일과 대조해야 합니다. [Microsoft 계약](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw)

프레임워크·DB·엔진은 확정하지 않았습니다. Czkawka 코어는 재사용 후보지만 Windows HEIC 준비에 제약이 있어 우선 검증이 필요합니다. 5만 장의 실제 속도, HEIC 호환, SSD 재연결과 중단 복구도 이번 조사에서는 미검증입니다. [코어 지원 조건](https://raw.githubusercontent.com/qarmin/czkawka/master/czkawka_core/README.md)

근거·반례·대안·후속 검증은 [Research 문서](<live-fixture>/.elenchus/research/R001-photo-organization-approaches.md)에 남겼습니다. 이번에는 여기까지 정리하고 전체 실행 계획은 다음에 이어갑니다.

다음 계획의 출발점으로 **‘원본 폴더 유지 + 로컬 카탈로그’라는 Research 권고를 받아들일지** 알려주시겠어요?
