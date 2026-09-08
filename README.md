# Elenchus

Elenchus는 Codex에서 사용자 목적을 구체화하고, 기능적 재료를 설계·구현·검증하는 한국어 탐구 스킬이다. 필요한 코드·데이터·테스트와 환경 제약·실패 경험을 확보해 이후 제작자에게 전달한다.

```text
Topology ↔ Research
→ 재료와 결론 전달
→ 일반 Codex 작업
```

## 1.1.0-beta.2의 방향

- **Topology — 탐구의 지형:** 목적·기능·입출력·환경 제약·연구 질문·달성 조건과 조사/실험 방향을 준비한다.
- **넓은 Research:** 비단순 조사에서는 실제 웹과 독립 질문을 맡은 탐색 agent 두 명을 기본으로 직접 해법·다른 방식/인접 분야·실패 경험을 찾는다. 좁은 사실 확인과 실제 도구 미지원은 구분한다.
- **실전적 재료:** 기능을 구현·연결하고 실제 실패를 재현·수정한다. 막힌 조건은 다시 웹에서 조사하며 같은 목적의 추가 Research를 열 수 있다.
- **제작자의 재량:** 기능의 입출력·동작·연결은 설계하지만 최종 화면·전체 동선·제품 중심 개념은 이후 제작자에게 남긴다. CLI·진단 화면·데모도 기능을 확인하는 데 자유롭게 쓴다.
- **Execution 제거:** 전체 Phase·Build와 종합 UX를 미리 확정하지 않는다. 새 프로젝트에 `execution.md`를 만들지 않는다.
- **선택적 handoff:** 요청 시 Pro 또는 다른 제작자에게 목적·코드·데이터·테스트·증거·열린 선택을 묶어 준다. Pro 사용이나 자동 업로드를 필수로 만들지 않는다.

## 설치와 업데이트

[Releases](https://github.com/Gudals0320/elehchus-skill/releases)에서 원하는 버전의 소스를 사용한다. 현재 정식 버전은 `1.0.0`이며 Research 개선은 main에 병합하지 않은 베타 브랜치에서 배포한다.

Codex의 skill-installer로 저장소 `Gudals0320/elehchus-skill`, path `.`, name `elenchus`를 지정해 설치할 수 있다. 특정 버전은 설치 명령에 `--ref v1.1.0-beta.2`처럼 태그를 지정한다. 기존 설치 폴더가 있으면 스킬 검색 경로 밖에 백업하고 명시적으로 교체한 뒤 새 작업에서 호출한다.

스킬 최초 진입의 `scripts/release_update.py --check`와 명시적으로 승인한 `--install TAG`는 **정식 릴리스만** 대상으로 한다. beta.2를 자동 안내·설치하지 않으며 베타 설치본도 자신보다 새로운 정식 버전만 안내한다. 예를 들어 베타에서 정식 `1.0.0`으로 내려가지 않고 정식 `1.1.0`이 나오면 안내한다.

과거 `3.0.0`은 번호 오타로 정정됐다. 해당 설치본은 낮은 번호를 업데이트로 인식하지 않으므로 백업 후 수동 재설치한다. 구판 updater의 호환용 Idea·Execution 경로는 남아 있지만 현재 흐름의 단계가 아니다.

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

- [Topology](stages/topology.md)는 현재 목적과 연구 계획의 기준이다. [Research](stages/research.md)는 독립 질문별 근거·판정을 기록하며 [Discovery](stages/discovery.md)와 [Web Evidence](stages/web-evidence-loop.md)를 필요한 조사에서 읽는다.
- [Lab](stages/lab.md)은 독립 실행할 코드·데이터·fixture·테스트와 재현 방법을 만드는 작업장이다. 기존 제품과 원본 데이터는 읽기 전용으로 두고 실제 연결은 독립 코드나 사본에서 검증한다.
- 작동한 부분·실제 실패·주입한 실패·모의 처리·미검증을 구분한다. 기능 구현 실패를 충분한 근거의 부정적 연구 결론과 혼동하지 않는다.
- 기존 Idea·Execution·Research·Lab은 자동 삭제·일괄 변환하지 않는다. 명시적으로 재개해 현재 Topology를 작성할 때 필요한 의도·제약을 출처와 함께 추출한다.

## 개발과 평가

[beta.2 아키텍처](docs/research-foundation-beta2.md)와 [실제 평가 준비·기록](tests/research-foundation/README.md)을 따른다. 독립 컨텍스트의 두 분야 각 2회에서 실제 웹·복수 agent·기능 실험과 재료 재현을 평가한다. 준비된 평가와 실제 완료한 실행은 구분한다.

기존 [beta.1 무제한 비교](tests/research-discovery/untimed/RESULTS.md) 및 [이전 전체 결과](tests/research-discovery/RESULTS.md)는 당시 소스·조건의 기록으로 보존한다. 고정 합성 자료 비교를 실제 웹 발견 능력이나 beta.2의 성공 근거로 대체하지 않는다.

```powershell
python -B -m unittest discover -s tests -p 'test_*.py'
python -B -m unittest discover -s tests/research-discovery -p 'test_*.py'
```

## 라이선스

[MIT](LICENSE)
