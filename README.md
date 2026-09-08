# Elenchus

Elenchus는 Codex에서 사용자 목적을 구체화하고, 기능적 재료를 설계·구현·검증하는 한국어 탐구 스킬이다. 필요한 코드·데이터·테스트와 환경 제약·실패 경험을 확보해 이후 제작자에게 전달한다.

```text
Topology ↔ Research
→ 재료와 결론 전달
→ 일반 Codex 작업
```

## 2.0.0의 방향

- **Topology — 탐구의 지형:** 목적·기능·입출력·환경 제약·연구 질문·달성 조건과 조사/실험 방향을 준비한다.
- **넓은 Research:** 비단순 조사에서는 실제 웹과 독립 질문을 맡은 탐색 agent 두 명을 기본으로 직접 해법·다른 방식/인접 분야·실패 경험을 찾는다. 좁은 사실 확인과 실제 도구 미지원은 구분한다.
- **실전적 재료:** 기능을 구현·연결하고 실제 실패를 재현·수정한다. 막힌 조건은 다시 웹에서 조사하며 같은 목적의 추가 Research를 열 수 있다.
- **제작자의 재량:** 기능의 입출력·동작·연결은 설계하지만 최종 화면·전체 동선·제품 중심 개념은 이후 제작자에게 남긴다. CLI·진단 화면·데모도 기능을 확인하는 데 자유롭게 쓴다.
- **선택적 handoff:** 요청 시 Pro 또는 다른 제작자에게 목적·코드·데이터·테스트·증거·열린 선택을 묶어 준다. Pro 사용이나 자동 업로드를 필수로 만들지 않는다.

## 설치

설치 대상은 저장소 루트가 아닌 **`skills/elenchus`**다. Codex의 skill-installer에 다음과 같이 요청한다.

```text
Gudals0320/elehchus-skill 저장소의 v2.0.0 태그에서
skills/elenchus 경로를 elenchus 스킬로 설치해 줘.
```

설치기 인자는 `--repo Gudals0320/elehchus-skill --path skills/elenchus --ref v2.0.0`다. 수동 설치도 해당 폴더만 Codex 스킬 경로의 `elenchus/`에 복사한다. 설치 후 새 작업에서 호출한다.

```text
skills/elenchus/     # 설치 대상
  SKILL.md
  agents/
  stages/
  LICENSE
docs/               # 설계 문서
tests/              # 개발 검사·평가 기록
```

`docs/`와 `tests/`는 설치 대상 폴더 밖에 있으므로 설치본에 포함되지 않는다. 설치기의 다운로드 단계에서는 저장소 전체를 임시로 받을 수 있지만 실제 설치 폴더에는 지정한 경로만 복사한다.

자동 업데이트는 제공하지 않는다. 버전 교체는 원하는 소스를 직접 설치한다. 기존 설치가 있으면 스킬 검색 경로 밖에 백업한 뒤 폴더를 교체한다.

[정식 릴리스](https://github.com/Gudals0320/elehchus-skill/releases/tag/v2.0.0)의 `elenchus-v2.0.0.zip`에는 설치 대상만 담는다. ZIP의 `elenchus/` 폴더를 스킬 경로에 복사해도 된다.

## 사용

```text
$elenchus 를 사용해 이 기능에 필요한 재료와 실제 제약을 조사·검증해 줘.
skill:Elenchus 로 기존 탐구를 재개해 줘.
```

명시적 호출의 대소문자·한국어 조사를 허용한다. 진행 중에는 호출을 반복하지 않아도 이어가며 `[Elenchus · 진행 중]`으로 표시한다. 결과 전달·종료 후에는 `[Elenchus · 완료]`로 끝내고 다음 일반 요청부터 표식 없이 작업한다. 과거 대화의 표식·파일 존재만으로 다시 진입하지 않는다.

연구 목표와 중요한 범위를 합의한 뒤 내부 호출·같은 목적의 후속 실험을 매번 승인받지 않는다. 사용자 목적·중요한 제약·큰 비용·접근 범위가 바뀌면 해당 쟁점만 확인한다. 추론과 탐색 깊이는 모델·effort·도구 환경에 영향을 받으며 이번 평가 기준은 Astra/xhigh다.

## 프로젝트 자료

```text
.elenchus/
├─ topology.md
├─ research/
│  ├─ index.md
│  └─ R001-neutral-topic.md
└─ lab/
   └─ R001/
```

- [Topology](skills/elenchus/stages/topology.md)는 현재 목적과 연구 계획의 기준이다. [Research](skills/elenchus/stages/research.md)는 독립 질문별 근거·판정을 기록하며 [Discovery](skills/elenchus/stages/discovery.md)와 [Web Evidence](skills/elenchus/stages/web-evidence-loop.md)를 필요한 조사에서 읽는다.
- [Lab](skills/elenchus/stages/lab.md)은 독립 실행할 코드·데이터·fixture·테스트와 재현 방법을 만드는 작업장이다. 기존 제품과 원본 데이터는 읽기 전용으로 두고 실제 연결은 독립 코드나 사본에서 검증한다.
- 작동한 부분·실제 실패·주입한 실패·모의 처리·미검증을 구분한다. 기능 구현 실패를 충분한 근거의 부정적 연구 결론과 혼동하지 않는다.

## 개발과 평가

[beta.2 아키텍처](docs/research-foundation-beta2.md)와 [평가 결과·수정·중단 범위](tests/research-foundation/RESULTS.md)를 참고한다. 네 실제 시도 중 세 세션을 종료했고, 외부 재현 두 번에서 발견한 재현 비교 문제를 별도 수정본으로 보완했다. 잔여 실제 평가·독립 검토는 사용자 요청으로 중단했다. 2.0.0은 이 한계를 공개한 상태로 배포한다. 전체 네 회차가 독립 검증을 통과했다고 주장하지 않는다.

기존 [beta.1 무제한 비교](tests/research-discovery/untimed/RESULTS.md) 및 [이전 전체 결과](tests/research-discovery/RESULTS.md)는 당시 소스·조건의 기록으로 보존한다. 고정 합성 자료 비교를 실제 웹 발견 능력이나 beta.2의 성공 근거로 대체하지 않는다.

```powershell
python -B -m unittest discover -s tests -p 'test_*.py'
python -B -m unittest discover -s tests/research-discovery -p 'test_*.py'
python -B -m unittest discover -s tests/research-foundation -p 'test_*.py'
```

## 라이선스

[MIT](LICENSE)
