# beta.2 아키텍처·평가 준비 검토

## 실제 평가 전

- 기준 beta.1: `73a7ddf`; 아키텍처 구현: `6ca00ad`; 평가 준비와 최초 freeze 소스: `7f60615`.
- Topology·Research·Discovery·Web Evidence·Lab의 책임을 분리하고 Execution을 호환 안내 파일로 축소했다. 독립 읽기 전용 검토자가 실제 구현·진단 UI 허용, 독립 탐색, 추가 연구·종료·기존 문서 호환을 대조했다.
- 검토 발견: 재현 프롬프트가 현재 파일에서 로드돼 freeze 이후 달라질 수 있었다. 실제 평가 전에 prepare→export→reproduce에 고정 바이트·해시를 연결하고 드리프트·누락·변조 검사를 추가했다. 현재 안내로 자동 대체하지 않는다.
- 일반/패키지 검사 39개 통과, 기존 연구 평가 도구 34개 통과, 새 native 평가 도우미 21개 중 20개 통과·실제 symlink 생성 1개는 Windows 권한 때문에 skip. 모의 link 거부는 별도로 통과했다.
- 스킬 validator와 runtime 앵커 링크 8개 검사 통과. 기존 `tests/research-discovery/`의 기록 bytes는 수정하지 않았다.

이 검토는 지침·도구의 일관성과 테스트 결과다. 네 실제 Research의 수행·탐색 폭·재료 재현 통과를 대신하지 않는다. 해당 결과와 배포 가능 여부는 실제 기록이 수집된 뒤 별도로 판정한다.
