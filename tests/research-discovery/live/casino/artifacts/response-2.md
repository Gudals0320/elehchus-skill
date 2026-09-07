[Elenchus · 진행 중]

이번 조사로 **화면 구성과 제작 방법은 비교할 수 있게 됐습니다. 카드 배부·뒤집기와 룰렛 공의 연속 움직임 비교는 남아 있습니다.** 카메라·색·재질·엔진은 미정으로 유지했습니다.

실제로 확인한 화면을 나란히 보면 차이가 분명합니다.

| 카드와 숫자를 크게 | 주변 공간을 넓게 | 조작 영역을 따로 |
|---|---|---|
| ![Nintendo의 카드게임 화면](https://www.nintendo.com/sg/switch/as7t/img/play05_texas_hold_em.jpg) | ![Tabletop Club의 테이블 화면](https://docs.tabletopclub.net/en/stable/_images/screenshots.jpg) | ![Silverconcept의 바카라 UI](https://silverconcept.com/work/baccarat-game-ui/cover.webp) |
| [Nintendo Clubhouse Games](https://www.nintendo.com/sg/switch/as7t/index.html): 큰 카드와 강조 테두리, 별도 숫자 표시. 밝고 장난감 같은 방향을 참고할 수 있습니다. 원본은 주변 공간이 적습니다. | [Tabletop Club](https://docs.tabletopclub.net/en/stable/): 테이블 외곽과 풍경이 깊이를 만듭니다. 포커 장면의 먼 카드는 작아져, 공간감과 가독성의 균형을 살펴볼 사례입니다. | [Silverconcept Baccarat](https://silverconcept.com/work/baccarat-game-ui): 하단에 칩·Deal 버튼, 상단에 잔액을 둡니다. 테이블 글자는 대비가 약하게 보입니다. 작동 게임이 아닌 디자인 콘셉트입니다. |

[PlayMex 블랙잭 공개 데모](https://playmexstudios.com/title/blackjack/)에서는 가상 칩 선택 → 잔액·베팅액 변화 → 배부 후 카드 합계와 Hit·Stand 표시를 직접 확인했습니다. [룰렛 데모](https://playmexstudios.com/title/roulette/)에서는 번호 강조와 휠의 회전 위치 변화를 봤지만, 베팅 완료와 공 착지까지 한 판을 확인하지는 못했습니다. 이 자료들로 애니메이션이 얼마나 자연스럽거나 빠른지 단정할 수는 없습니다.

제작 방법은 다음처럼 비교할 수 있습니다. 아래 적합성 판단은 조사에 따른 **에이전트 제안**입니다.

| 방법 | 잘 맞는 조건 | 필요한 부담 |
|---|---|---|
| HTML/CSS 입체 표현 | 구도가 제한되고 카드 이동·뒤집기 중심일 때 | 곡면 휠·조명을 별도로 표현해야 합니다. CSS 효과에 따라 입체 계층이 평면화되는 제약도 있습니다. [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform-style) |
| 이미지 중심 2.5D | 정해진 시점의 입체감으로 충분할 때 | 새 각도와 가림에 맞는 이미지·합성 작업이 필요합니다. [PixiJS PerspectiveMesh](https://pixijs.com/8.x/guides/components/scene-objects/mesh#perspectivemesh) |
| 실시간 3D와 웹 UI 결합 | 테이블·휠·카메라·조명을 조정하고 싶을 때 | 모델·재질·클릭 판정과 UI 연결을 만듭니다. HTML 글자의 가림도 직접 처리해야 합니다. [Three.js 공식 예제](https://threejs.org/manual/en/align-html-elements-to-3d.html) |
| 엔진에서 제작 후 웹 내보내기 | 장면과 애니메이션을 편집 도구에서 만들고 싶을 때 | 웹 렌더러·언어·로딩 제약을 확인해야 합니다. [Godot 공식 문서](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html) |

**3D 애니메이션은 동작별로 나눠 생각하는 편이 좋겠습니다.** 카드 배부·뒤집기, 칩 이동, 휠 회전은 위치와 회전을 시간에 따라 바꾸는 방식이 후보입니다. 카드가 휘는 연출까지 원하면 별도 변형 작업이 늘어납니다. Blender에서 만든 동작을 가져올 수도 있지만 물리·조명·재질 애니메이션이 그대로 옮겨지는 것은 아닙니다. [Three.js 애니메이션](https://threejs.org/manual/en/animation-system.html), [Blender glTF 내보내기](https://docs.blender.org/manual/en/5.1/addons/import_export/scene_gltf2.html#animations).

현재 **비교 기준안으로는 테이블·카드·휠을 3D로, 잔액·베팅액·행동 버튼을 화면 정면에 두는 구성을 추천**합니다. 공간감과 글자 크기를 각각 조절할 수 있기 때문입니다. UI와 3D 상태를 연결하는 작업은 생깁니다. 더 작은 CSS·2.5D 방식과 테이블 직접 조작 방식도 후보로 유지하며, 특정 구도나 엔진의 채택을 뜻하지 않습니다.

남은 선택은 **테이블이 차지할 비중과 시점, 버튼·테이블 조작의 분담, 색·재질, 카드 휨 여부와 움직임의 길이·생략 여부**입니다. 실제 성능과 제작 기간도 아직 검증하지 않았습니다. 세칙·베팅 단위와 전체 Build 계획은 요청대로 다음 대화에 남겼습니다.

[조사 근거와 한계 전체 기록](<live-fixture>/.elenchus/research/R001-table-presentation.md)을 작성했습니다.

**화면·제작 접근의 비교 결론은 확정하고, 카드와 룰렛 공의 연속 움직임 비교는 미완료 후속 조사로 남길까요?**

[Elenchus 규칙](<live-fixture>/skill/SKILL.md)의 “생략한 조사나 후속 검증 계획을 수행 완료로 바꾸지 않는다”에 따라, 이번 확인에서도 미관찰 부분을 분리해 남기려는 질문입니다.
