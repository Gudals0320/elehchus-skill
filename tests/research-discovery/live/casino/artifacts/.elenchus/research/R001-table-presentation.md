# Research R001: 카지노 테이블의 화면·조작·제작 접근

- 상태: 작성 중
- 기준: ../idea.md
- 확인 날짜: 2026-09-07
- 영향: Phase 후보

## Repository 기준선

지정 작업 디렉터리 안의 사용자 요청·추가 답변과 Idea를 사용했다. `rg --files`로 현재 계획·기록 파일을 확인했다. 기존 구현·성능의 옳고 그름이 아닌 초기 시각·상호작용 탐색이므로 제품·저장소 코드는 조사하지 않았다. 다른 설치본·저장소·태스크를 읽지 않았다.

## Neutral brief

- 중립 질문: 싱글 카지노에서 공간감·카드 가독성·조작과 제작 부담을 어떤 방식으로 양립할 수 있는가?
- 입력: 게임 선택·초기 자금·게임별 베팅과 플레이 행동. 세칙과 단위는 후속 합의다.
- 출력: 터미널을 먼저 만든 뒤, 게임 진행·카드·룰렛·자금·결과를 보이는 3D 애니메이션 웹게임. 현재 산출물은 그 계획을 위한 사례 비교·제작 대안·미정 선택이다.
- 사용자 경험: 혼자 플레이하며 테이블 주변 공간을 느끼고 카드·숫자를 읽고 조작한다. 실사보다 애니메이션에 가까운 3D 느낌을 원한다. 구체적인 색·재질·카메라는 미정이다.
- 성공 조건: 실제 화면과 상호작용 근거를 구분해 비교하고, 가져올 요소·부담·한계·대안을 제시해 사용자가 미정 선택을 판단할 수 있다. 실제 제품의 수치 기준은 아직 정하지 않는다.
- 실패 조건: 설명·메타데이터를 시각·동작 관찰로 오인, 원자료에 없는 취향·기능 확정, 특정 엔진을 조건으로 넣고 탐색, 성능·제작 기간을 실험 없이 보장하는 경우.
- 확정 제약: Windows 개인 사용, 데스크톱 Chrome 우선, 세 게임, 세션 공동 가상 자금, 저장·계정·공유·통계·현금·결제 없음. 터미널 이후 웹. 카드게임 각각 독립 6덱. 멀티는 미래 맥락만. 이동·캐릭터 조작 불필요. 새 계정·유료 서비스·제품 구현·Lab 실행 없음.
- 객관적인 환경: 호스트 Windows, 공개 web 검색·open과 CUA 새 공개 탭 관찰이 제공된다. 프로젝트 성능·설치 라이브러리·GPU 사양은 검증하지 않았다.
- 미해결: 카메라/테이블 비중/주변 공간, 입력을 3D에 배치할 범위, 색·재질, 움직임의 종류·길이·생략, 제작 도구·자산과 조정 비용.

## 사용자 기술 언급 분류

Windows·데스크톱 Chrome은 필수 지원 환경, 터미널 후 웹은 확정 순서, 3D 애니메이션은 결과 요구다. 특정 엔진·라이브러리 후보는 사용자가 지목하지 않았다. 아래에서 발견할 도구는 모두 후보로만 다룬다.

## 증거 계획과 지원 조건

| 증거원 | 상태 | 이유 | 바뀔 수 있는 결정 |
|---|---|---|---|
| Repository | 생략 | 현재 질문에 기존 제품 코드는 필요하지 않음 | 기존 코드 재사용·성능에 관한 결론을 내리지 않음 |
| Independent exploration | 필요 | 화면 사례 관찰과 제작 전략은 독립 질문 분담의 이점이 있음 | 제작 접근·비용·한계 |
| External evidence | 필요 | 실제 공개 이미지·동작·개발 문서 비교가 필요 | 화면·조작·제작 방법 |
| Browser Evidence | 생략 | 로그인·개인화·현재 사용자 계정 관찰 불필요 | 없음 |
| Lab | 생략 | 이번 요청은 공개 사례 비교. 제품의 프레임률·실제 체감 판정은 하지 않음 | 구현 전 별도 검증 필요 |

2026-09-07 도구 스키마 확인: collaboration.spawn_agent의 fork_turns=none 사용 가능하며 실제 생성에 성공했다. 공개 검색만 맡기고 파일 접근·브라우저·Lab·재위임을 지시로 제한했다. 이는 기술적인 읽기 전용 격리가 아니다. 메인은 CUA createBrowserTab으로 Chrome의 별도 공개 탭을 실제 생성했고 이미지 스크린샷 관찰에 성공했다. 기존 사용자 탭 나열·선택·로그인은 하지 않았다. 시각 자료는 세션 중 관찰만 하며 파일에 보존하지 않는다.

## Subagent 역할·범위

구현 탐색 역할 하나에 무이력 중립 brief를 전달했다. 범위는 가능한 제작 방식·공개 코드/공식 문서·적용 한계와 사용 조건이다. 선호 후보는 전달하지 않았다. 메인은 실제 화면·자료 본문 검증과 최종 판단을 담당한다.

## 조사 목적·범위와 접근 범주

탐색·벤치마킹: 직접 카지노 UI, 인접 카드/보드게임의 공간·가독성, 브라우저 카드 표현의 작은 구현 방식, 일반 3D 장면 제작 방식을 비교한다. 실제 현금 운영·게임 규칙 검증·멀티 구조는 조사하지 않는다. 발견 단계에서 'stylized 3D blackjack roulette baccarat game table design', 'browser 3d playing cards blackjack demo table github', 'Tabletop Club screenshots playing cards camera'를 검색했고 공개 제작자 사례·카드 데모·테이블 시뮬레이터가 발견됐다. 다음 묶음은 Nintendo 카드게임·직접 카지노 UI·공개 애니메이션과 기술 한계로 좁혔다.

## Web Evidence

### 조사 깊이

후보 비교·시각/기술 적용·접근 실패를 포함하므로 전체 기록을 사용한다.

### Claim map

| ID·주장 | Verdict 영향 | 필요한 출처 역할 | 최신성·적용 환경 | 반증 조건 |
|---|---|---|---|---|
| V1 테이블 공간을 보이면서 카드·숫자를 별도로 강조하는 실제 화면 접근이 있다 | 카메라·UI 역할 | 제작자가 공개한 실제 이미지 | 확인일의 이미지, 제품별 장면 한정 | 관련 장면이 없거나 카드/숫자 배치를 확인할 수 없음 |
| V2 화면 조작과 물체 조작, 이동·뒤집기·회전은 서로 다른 부담을 가진다 | 조작·애니메이션 범위 | 공개 데모/영상, 제작자 조작 설명 | 장면/버전 한정 | 소개 문구 외 관찰이 없으면 체감 판단 불가 |
| T1 웹 중심·CSS 표현·3D 엔진 등 제작 접근이 조건에 따라 달라진다 | 기술 후보 | 공식 문서·관련 공개 코드 | 확인일의 지원 문서 | 필수 계정·유료 서비스·지원 불가 등 확정 제약과 충돌 |
| T2 투명 카드·그림자·물리·에셋에 적용 한계가 있다 | 작업량·후속 검증 | 공식 한계 문서·원 작성자 실패/제약 | 해당 렌더러/포맷/버전 한정 | 다른 조건의 한계를 일반화하거나 실제 실패를 확인하지 않음 |

### Retrieval plan

- V1: 직접 카지노 개발자와 Nintendo·Tabletop Club 공식 이미지에서 카드 크기, 배경/테이블 공간, 숫자 표시를 본다. 정지 이미지로 속도를 판단하지 않는다.
- V2: 공개 카드 데모·공식 소개 영상의 카드 뒤집기/배치/룰렛 회전과 조작 설명을 확인한다. 실제 재생이 막히면 다른 공개 데모를 찾고 남은 동작은 미확인으로 둔다.
- T1/T2: 독립 탐색 결과의 결정적 원문을 메인이 다시 열고 후보 간 비용·조건을 확인한다. 반대 검색은 transparency sorting, shadow performance, web export limitations, asset license를 사용한다.
- 이미지 캐시 실패 시 같은 공식 공개 URL을 별도 Chrome 탭에서 렌더링한다. 연령 확인·지역 제한·로그인·결제 경로는 중단하며 독립 공개 자료로 대체한다. 개인 계정 Browser Evidence는 필요하지 않다.

### 초기 접근 관찰

- Nintendo 공식 제품 본문과 Texas Hold'em 이미지, Tabletop Club 공식 문서와 스크린샷을 확인했다. 이미지의 web open은 Cache miss였으나 같은 URL의 Chrome 렌더링은 성공했다.
- Evolution First Person Blackjack·Roulette 공개 본문의 조작 설명은 확보했다. 본문에 연령 확인·지역별 데모 제한·영상 오류 문구가 함께 있었다. 연령 제출·데모 진입은 하지 않았고 움직임을 관찰했다고 취급하지 않는다.
- 후속 조사에서 Silverconcept 공개 UI 원본, PlayMex 공개 오프라인 데모, CardsJS 레이아웃을 직접 관찰하고 아래 비교에 반영했다.

## 실제 사례 비교

모든 '적용'은 에이전트의 추론·미승인 제안이다. 원본의 색·구도·기능을 그대로 채택하거나 이미지·코드를 제품으로 복사하지 않는다.

| 접근·대표 사례 | 실제 근거·관찰 수준 | 가져올 요소 | 우리 조건의 변경·부담 | 판정 |
|---|---|---|---|---|
| 카드 중심의 테이블 — [Nintendo Clubhouse Games](https://www.nintendo.com/sg/switch/as7t/index.html), Texas Hold'em 이미지 | 직접 관찰: 파란 테이블, 중앙 공용 카드, 하단의 큰 개인 카드, 카드 강조 테두리, 우상단 Pot 숫자. 캐릭터는 작은 초상만 보임 | 카드 표면과 결과 숫자의 강조, 장난감 같은 색·형태의 방향을 비교할 자료 | 원본은 테이블이 화면을 대부분 채움. 사용자가 원하는 주변 공간을 더 보이면 카드 크기 조정이 필요. 포커·멀티 기능은 가져오지 않음 | 시각 후보 유지, 취향·색 승인 아님 |
| 공간 중심의 테이블 — [Tabletop Club 공식 스크린샷](https://docs.tabletopclub.net/en/stable/_images/screenshots.jpg) | 직접 관찰: 좌상단 포커 테이블은 비스듬한 시야·테두리·주변 풍경·가까운 손패를 보여 줌. 먼 중앙 카드는 상대적으로 작음 | 테이블 외곽과 주변 공간이 만드는 깊이 | 낮은 시점/넓은 시야와 먼 카드 가독성의 교환 관계. 자유 이동·임의 물체 조작은 우리 요구가 아님 | 공간 참고 유지, 시뮬레이터 전체 제작은 현재 제외 |
| 테이블과 정면 조작 띠 — [Silverconcept Baccarat Game UI](https://silverconcept.com/work/baccarat-game-ui) | 직접 관찰: 상단 잔액, 하단 Deal·Undo·Clear·칩, 테이블 위 베팅 금액. 자료 설명: 2020년 의뢰 콘셉트이며 모바일 가로 화면을 다룸 | 카드 공간과 조작 공간의 구분, 테이블의 입체 모양과 정면 숫자·버튼 결합 | 어두운 테이블의 Player/Banker 글자는 버튼·숫자보다 대비가 약하게 보임. 주변 공간은 적음. 작동 제품·애니메이션 성공 사례로 취급하지 않음 | UI 역할 비교 자료, 모바일 구성·기능·색 미채택 |
| 실제 3D 장면과 게임 버튼 — [PlayMex Blackjack](https://playmexstudios.com/title/blackjack/), [Roulette](https://playmexstudios.com/title/roulette/) | 직접 관찰: Chrome의 공개 Offline Template 데모를 렌더링. 블랙잭은 가상 칩 10 선택 → 잔액 1000에서 990 → 베팅 칩/10 표시 → Deal → 카드·합계 17·Hit/Stand 표시. Hit 후 행동 버튼 비활성 장면과 이후 빈 테이블을 관찰. 룰렛은 테이블/번호판/주변 바닥/하단 칩, 포인터 위치에 따른 번호 강조, 서로 다른 회전 위치의 휠을 관찰 | 테이블 물체·별도 점수표시·상황에 따른 행동 버튼 구분 | 실사 재질 방향은 사용자 취향과 차이. 카드 전체가 겹치므로 숫자/문양 노출을 조정해야 함. 룰렛 베팅 확정·공 착지/결과 한 판은 확인 못함. 템플릿 구매·사용권·정확성은 검증하지 않음 | 작동/배치 근거. 템플릿 구매·재사용 미제안 |
| 더 작은 카드 표현 — [CardsJS Hand Layouts](https://richardschneider.github.io/cardsJS/hand-layouts.html) | 직접 관찰: 전체 카드가 보이는 수평 배열, 카드가 겹치는 배열, 세로 배열. 본문·코드 설명: HTML 이미지와 CSS 배치, 부채형에는 JS 위치·회전 사용 | 카드 배열·겹침을 3D 엔진 없이 비교하는 작은 접근 | 테이블/룰렛 곡면·조명·공 움직임까지 해결한 사례는 아님. 이번에 hover 애니메이션·라이선스 전체를 검증하지 않음 | 작은 대안 유지, 기존 코드를 제품 출발점으로 지정하지 않음 |

### 움직임 관찰의 한계

공개 데모에서 실제 입력과 상태 변화, 휠의 회전 위치 변화는 봤다. 카드의 연속 이동 경로·뒤집기 중간 프레임·정확한 길이·가속 곡선·장시간 반복 플레이 피로·룰렛 공 착지를 관찰/측정했다고 주장하지 않는다. Nintendo·Tabletop Club·Silverconcept는 정지 화면 근거다. 따라서 현재 자료로 특정 애니메이션의 리듬·자연스러움·권장 초 단위를 확정할 수 없다.

## 제작 접근 비교와 중요한 원문 재확인

독립 구현 탐색은 아래 네 범주를 반환했다. 메인이 결정에 사용하는 모든 원문을 다시 열었다. 같은 원문을 agent와 메인이 각각 읽은 것은 독립 출처 둘로 계산하지 않았다.

| 제작 방법·대표 근거 | 실제 확인 | 적합 조건·얻는 것 — 추론 | 부담·반대 근거 | 현재 판정 |
|---|---|---|---|---|
| HTML/CSS 원근·회전 — [MDN transform-style](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform-style) | Description·Transform style demonstration의 3D 자식과 큐브 코드 확인 | 카메라가 제한되고 카드 이동·뒤집기 정도면 비교할 작은 방식 | opacity·filter·일부 overflow는 preserve-3d 자식을 평면화. 곡면 휠·조명은 별도 표현 필요 | 후보, 특정 CSS 데모의 품질 미검증 |
| 이미지 중심 2.5D — [PixiJS Mesh](https://pixijs.com/8.x/guides/components/scene-objects/mesh#perspectivemesh) | PerspectiveMesh에서 이미지 UV·네 모서리를 조정해 원근을 표현하는 코드 확인 | 정해진 구도에서 입체감만 필요하면 모델링 부담을 이미지 제작으로 옮길 수 있음 | 새 각도·가림·회전 장면용 이미지/합성 작업 필요. 현재 완성 카지노 사례의 품질은 검증 안 됨 | 더 작은 비교 후보 |
| 웹 실시간 3D + 필요 시 HTML — [Three.js HTML 정렬](https://threejs.org/manual/en/align-html-elements-to-3d.html) | 세 가지 글자 방식, 물체를 화면 좌표로 투영하는 코드, 라벨 겹침·가림·zIndex 문제를 메인이 재확인 | 물체를 여러 각도에서 보고 조명·카메라를 조정해야 한다면 비교 가치. 숫자/버튼은 화면 정면에 둘 수 있음 | 모델·재질·클릭 판정·글자 가림을 함께 관리. HTML을 올리는 것만으로 3D 가림이 해결되지 않음 | 기술 후보. 사용자 UI 역할/엔진은 미정 |
| 범용 엔진의 웹 내보내기 — [Godot Web export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html), PlayMex Unity 데모 | Godot 문서의 WebAssembly·WebGL2·Compatibility 렌더러·Godot4 C# 웹 내보내기 제한을 확인. Unity 데모는 실제 Chrome 실행을 관찰 | 장면·타임라인을 편집하는 방식 선호 시 비교 가치 | 브라우저용 내보내기 제약·엔진 데이터 로딩·터미널 로직과 연결 작업. 상용 템플릿은 현재 구매 안 함 | 엔진별 후보 유지, 성능/크기/재사용 보장 없음 |

[k-stopczynska/roulette](https://github.com/k-stopczynska/roulette)의 README Built with·Continued development도 메인이 확인했다. 작성자는 React·Babylon.js·TypeScript와 칩 드래그/휠 회전을 설명하지만, 공 애니메이션 조정·드롭 영역 강조를 후속 작업으로 남겼다. 이는 라이브러리 조합만으로 조작·움직임의 완성도가 보장되지 않는 구체적인 반대 근거다. 공개 README만 확인했으며 소스 동작·데모·재사용 허가는 검증하지 않았다. 서버·로그인·멀티 구조는 현재 요구에 적용하지 않는다.

## 3D 애니메이션을 만드는 작업의 구분

아래는 기능 확정이 아니라 제작 접근에 대한 에이전트 제안이다.

1. 카드가 휘지 않는 배부·뒤집기, 칩 이동, 휠 회전은 물체의 위치·회전·크기 변화를 시간에 따라 제어하는 접근으로 비교할 수 있다. [Three.js Animation System](https://threejs.org/manual/en/animation-system.html)은 transform·shape key·bone 등 서로 다른 애니메이션 대상을 구분하고 재생·시간 배율을 제어한다. 카드마다 복잡한 뼈대를 만드는 방식이 필수라는 근거는 없다.
2. 카드 휨이나 미리 연출한 복잡한 동작이 필요하면 모델링 도구에서 만든 애니메이션을 가져오는 대안을 비교한다. [Blender 5.1 glTF 문서](https://docs.blender.org/manual/en/5.1/addons/import_export/scene_gltf2.html#animations)의 Animations·Scene을 Chrome 공개 탭에서 확인했다. 위치/회전/크기·뼈대·shape key는 지원하지만 물리·조명·재질 애니메이션은 해당 경로에서 그대로 내보내지 않는다. Lights는 Area/World 조명을 무시한다고 명시한다. 따라서 Blender 화면과 웹 결과가 그대로 같다고 약속할 수 없다.
3. 룰렛 공은 미리 정의한 경로·타이밍과 실시간 물리 시뮬레이션을 비교할 여지가 있다. 전자는 결과 표시 순서를 통제하기 쉽다는 설계 추론이고, 후자는 충돌·착지·결과 일치 검증 부담이 생긴다. 아직 양쪽을 우리 조건에서 실행하지 않았으므로 채택하지 않는다. 로직 결과와 화면이 일치한다는 검증은 어느 방식이든 필요하다.

### 자산과 사용 조건

- 직접 만든 카드 면·기본 도형의 카드/칩·테이블/휠 모델을 조합하는 방향과 외부 자산 재사용을 비교한다. 모델의 정교함·텍스처·조명에 따른 실제 작업 시간은 측정하지 않았다.
- 재사용 후보로 [mehrasaur의 Playing Card Assets](https://opengameart.org/node/51975) 원문을 확인했다. 페이지는 CC0로 표시하며 2D 카드·칩·PNG·spritesheet·원본 파일을 설명한다. 검색 결과의 '3D Assets'는 컬렉션 이름이고 실제 자산 유형은 2D다. 아직 파일을 내려받거나 그림의 품질·내용·최종 배포본 라이선스를 검증하지 않았다.
- [Three.js LICENSE](https://github.com/mrdoob/three.js/blob/dev/LICENSE)와 [Godot License](https://godotengine.org/license/) 원문에서 MIT 및 고지 조건을 확인했다. 라이브러리/엔진의 사용 조건이 외부 테이블 모델·카드 그림의 사용 허가를 대신하지 않는다.
- Nintendo·Silverconcept·PlayMex 화면은 참고 자료다. 원본 자산의 복제·구매는 제안하거나 실행하지 않았다.

## 공개 접근 기록

| Claim | 출처·URL | 접근 경로·본문 확보 | 증거 판정 | 실패·terminal reason | 남은 공개 경로 처리 |
|---|---|---|---|---|---|
| V1 | [Nintendo 제품](https://www.nintendo.com/sg/switch/as7t/index.html)·[Texas Hold'em 이미지](https://www.nintendo.com/sg/switch/as7t/img/play05_texas_hold_em.jpg) | web 본문 확보, 이미지 web Cache miss 후 Chrome 실제 이미지 확보 | 장면 한정 지지 | web 이미지 캐시 실패는 사이트 차단으로 일반화 안 함 | 공식 동일 URL 렌더링으로 해소 |
| V1 | [Tabletop Club 문서](https://docs.tabletopclub.net/en/stable/)·[이미지](https://docs.tabletopclub.net/en/stable/_images/screenshots.jpg) | 본문 확보, 이미지 Chrome 관찰 | 장면 한정 지지 | web 이미지 Cache miss | 공식 이미지 렌더링으로 해소 |
| V1 | [Silverconcept](https://silverconcept.com/work/baccarat-game-ui) | web·Chrome 본문/실제 화면 확보, DOM에서 /work/baccarat-game-ui/cover.webp 확인 | 콘셉트 배치 지지 | web 이미지 열기 오류 | Chrome 관찰로 해소, 애니메이션 주장 제외 |
| V1/V2 | [Evolution Blackjack](https://games.evolution.com/first-person/first-person-blackjack/)·[Roulette](https://games.evolution.com/first-person/first-person-roulette/) | 공개 조작 설명 본문만 확보 | 설명 수준 제한 | 연령 확인·지역별 데모 제한/영상 오류 문구. 데모 경로 중단, 제출 없음 | PlayMex의 공개 Offline Template을 대체 관찰. Evolution 데모 품질은 결론에 사용 안 함 |
| V1/V2 | [PlayMex Blackjack](https://playmexstudios.com/title/blackjack/)·[직접 데모](https://playmexstudios.com/wp-content/unitygames/blackjack/index.html) | web 본문, Chrome 실제 입력/상태 관찰 | 흐름·배치 지지 | 연속 이동 중간 프레임/길이는 미관찰 | 해당 체감 비교는 남은 공백 |
| V1/V2 | [PlayMex Roulette](https://playmexstudios.com/title/roulette/)·[직접 데모](https://playmexstudios.com/wp-content/unitygames/roulette/index.html) | 초기 Unity 로딩 후 European 선택·테이블 관찰 | 회전 위치 변화·강조 확인 | 칩 클릭/드래그 이후 BET 0.00 유지. 베팅 성공·원인은 미확인 | 성공한 한 판/공 착지는 주장하지 않음. 정확한 조작/공개 영상 후속 관찰 필요 |
| V1/T1 | [CardsJS](https://richardschneider.github.io/cardsJS/)·[레이아웃](https://richardschneider.github.io/cardsJS/hand-layouts.html) | 첫 slash 없는 web 요청 Cache miss, 공식 링크의 slash URL 본문 성공. 레이아웃 Chrome 관찰 | 평면/겹침 구조 지지 | hover 동작은 미관찰 | 코드 복사·품질 평가 범위를 넘지 않음 |
| T1/T2 | [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform-style)·[PixiJS](https://pixijs.com/8.x/guides/components/scene-objects/mesh)·[Three.js HTML](https://threejs.org/manual/en/align-html-elements-to-3d.html) | web 본문/코드 확보·메인 재확인 | API·구현 제약 지지 | 없음 | API 지원은 우리 제품 성능 증거가 아님 |
| T1/T2 | [Godot 웹](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html)·[공개 룰렛 README](https://github.com/k-stopczynska/roulette) | web 본문 확보·메인 재확인 | 해당 환경·작성자 경험 한정 | 공개 룰렛 개별 코드 접근은 독립 agent 도구에서 실패 | 코드 재사용 판정 안 함. 문서 주장에 필요한 본문은 확보 |
| T1/T2 | [Three.js Animation](https://threejs.org/manual/en/animation-system.html)·[Blender 5.1](https://docs.blender.org/manual/en/5.1/addons/import_export/scene_gltf2.html) | Three.js 본문, Blender web latest/5.1 오류 후 5.1 Chrome 본문 확보 | 포맷/애니메이션 지원 범위 지지 | web fetch 실패 | 공식 Chrome 경로로 해소 |
| T2 | [2D 카드 자산](https://opengameart.org/node/51975)·[Three.js 라이선스](https://github.com/mrdoob/three.js/blob/dev/LICENSE)·[Godot 라이선스](https://godotengine.org/license/) | 원문 확보 | 표기된 사용 조건 한정 | 배포 파일 검사·다운로드 없음 | 자산 실제 채택 직전에 파일/고지 확인 필요 |

## Evidence matrix와 gap loop

| Claim | 지지 근거 | 반대·제한 | 공개 Browser 관찰 | 적용 범위·상태 | 남은 공백 |
|---|---|---|---|---|---|
| V1 공간·가독성을 분담하는 접근 | Nintendo·Tabletop Club·Silverconcept·PlayMex | 넓은 시야의 작은 원경 카드, 어두운 테이블 글자, 겹친 카드 | 실제 이미지/렌더링 확인 | 확인: 비교한 장면의 배치 | 우리 해상도·구도에서의 선호/가독성 기준 |
| V2 조작·상태·움직임 차이 | PlayMex 블랙잭 실제 입력과 상태, 룰렛 강조/회전 위치 | 연속 동작 전체를 보지 못함. 룰렛 베팅 성공 미확인 | 공개 데모만, 사용자 계정 접근 없음 | 범위 제한 | 카드 배부·뒤집기 리듬과 룰렛 공 착지의 충분한 연속 관찰 |
| T1 제작 접근 | MDN·PixiJS·Three.js·Godot·Blender | 방식마다 조명/곡면/출력/웹 제약 | Unity 데모 실제 실행, Blender 본문 | 확인: 기능/문서 범위. 성능은 미검증 | 엔진 선택 전 대표 장면의 실제 Chrome 검증 |
| T2 구현·재사용 한계 | HTML 가림, CSS 평면화, Blender 내보내기, 공개 개발자의 공/드롭 개선 기록 | 개별 조건을 전체 라이브러리 실패로 일반화 못함 | 문서·화면 한정 | 확인: 명시 제약. 비용 정량값은 근거 부족 | 최종 자산·라이선스, 렌더링 예산, 정확한 제작 부담 |

첫 검색 후 정지 배치 근거가 충분해져 추가 유사 이미지 수집의 효용이 낮아졌다. 다음 공백은 실제 입력·움직임이어서 PlayMex 데모를 관찰했다. 구현 탐색 결과는 공식 API의 긍정 근거뿐 아니라 CSS 평면화·HTML 가림·glTF 내보내기·웹 렌더러 제한으로 교차 점검했다. 남은 큰 공백은 취향 결정과 애니메이션 체감이며, 더 많은 라이브러리 이름을 수집해도 이 공백은 해결되지 않는다.

## Web closure·Discovery 완료 점검

- 핵심 주장에 원문·관찰·한계·확인일을 연결했고, Claim map·Retrieval plan·접근 기록·Evidence matrix를 유지했다. 검색 snippet이나 agent 동의만으로 확정한 주장은 없다.
- 각 API의 지원/사용 조건은 해당 공식 원문이 직접 통제하는 사실이므로 형식적 두 번째 출처를 강제하지 않았다. 적용 판단은 실제 화면·다른 구현 범주·한계 문서로 비교했다.
- 접근 실패에는 공개 대체 경로를 시도했다. 연령/지역 제한은 제출·우회 없이 중단했고 별도 공개 데모로 보완했다.
- Discovery 1 접근 비교: 카드 중심·공간 중심·정면 조작 결합·작은 이미지 표현과 제작 네 범주의 차이를 제시했다.
- Discovery 2 직접 근거: 정지 배치와 조작 상태는 충분하다. 카드/공 애니메이션의 연속 체감 비교는 아직 미완료다.
- Discovery 3 적용 가능성: 가져올 요소·원요청 밖 기능·변경 부담·문서상의 구현 제약을 구분했다.
- Discovery 4 결정 영향: 색/구도/UI 역할/엔진은 후보로 유지하며 사용자 승인으로 오인하지 않았다.
- Discovery 5 타당한 종료: 정지 화면과 제작 접근 비교의 추가 검색 효용은 낮다. 애니메이션 체감 비교에는 중요한 미관찰 범위가 남으므로 전체 시각·동작 탐색을 완료로 처리하지 않는다. 현재 비교 결론과 미완료 부분의 처리에 대한 사용자 확인을 기다린다.

## Verdict

- 판정: **결론 가능 — 화면·조작 구성과 제작 접근의 비교. 결론 보류 — 특정 애니메이션의 리듬·자연스러움과 최종 시각/기술 채택.** 문서 상태는 사용자 확인 전 `작성 중`이다.
- 근거: 실제 카드·테이블 UI와 공개 오프라인 데모, 제작 대안의 공식 문서에서 가독성/공간/조작을 분담하는 방식과 구현 조건을 확인했다.
- 반대 근거: 공간을 넓히면 카드가 작아질 수 있고, 테이블에 넣은 어두운 문자는 읽기 어려울 수 있다. HTML 혼합도 가림·정렬 작업이 필요하고, 엔진 내보내기도 브라우저 제약이 있다. 일반 기술 지원만으로 애니메이션 체감·제작 난이도를 보장하지 못한다.
- 후보와 핵심 차이: 카드 중심은 가독성, 공간 중심은 깊이, 정면 UI 결합은 입력 명료성에 비교 가치가 있다. CSS/2.5D는 제한된 구도에서 작은 대안, 실시간 3D는 각도·조명 변경의 유연성, 엔진은 장면 제작 흐름에 강점이 있다는 적용 추론이다.
- 채택·제외: 현재 제품 선택으로 채택한 후보는 없다. 원요청 밖 캐릭터/이동/멀티/계정/통계는 유지해서 제외한다. 유료 템플릿 구매·외부 자산 복사는 미승인/미실행이다.
- 제안: 카드·숫자의 가독성과 공간감을 함께 비교하기 위해 **테이블·카드·휠은 3D, 잔액·베팅액·행동 버튼은 정면 UI**인 안을 비교 기준안으로 두는 것은 타당하다. 단순한 CSS/2.5D와 테이블 직접 조작 안도 함께 유지한다. 이는 엔진·카메라·재질 확정이 아니다.
- 한계: 연속 애니메이션 경로·타이밍·룰렛 한 판·우리 PC 성능·자산 제작 기간 미검증. 공개 사례 전체를 재현해 테스트하지 않았다.
- 신뢰도: 화면 구성·공식 지원 조건은 높음, 우리 조건의 제작 적합성은 중간, 타이밍·자연스러움·성능 예측은 낮음.
- Idea 변경: 사용자 제약을 유지하고 위 비교안은 미승인 제안에만 연결한다. 카메라/색/재질/입력 역할/애니메이션 범위는 열린 선택이다.
- Execution 영향: 아직 전체 Build 계획을 쓰지 않는다. 나중에 대표 장면의 가독성·중복 입력·로직과 표현 결과 일치·웹 성능 검증을 실제 표현 구현보다 앞에 놓을 검증 후보로 남긴다. 이는 합의된 Build도 수행한 Lab도 아니다.

## 보류·다음 확인

이번 사용자 확인은 위 비교 결론과 미관찰 부분의 처리에 한정한다. 카드 배부/뒤집기와 룰렛 공의 연속 움직임 비교를 후속 조사로 남기려면 그 미완료 사실을 유지한다. 연기 합의를 수행 완료로 바꾸지 않는다. 이후 사용자 화면 선호, 규칙 세칙과 전체 Build 계획은 별도 대화에서 이어간다.
