# 독립 재현에 제공할 재료 선택

첫 표본의 export를 준비한 뒤, 기존 `reproduce-prepare`가 `project/` 전체를 복사하면서 Lab 안의 actor 활동 로그와 내부 재실행 기록도 함께 전달할 수 있음을 발견했다. **그 최초 복사 작업장은 어떤 재현 모델에도 제공하지 않았다.** 원래 workspace와 export는 보존한다.

실제 독립 재현 네 회차에는 `prepare_reproduction.py`를 사용한다. operator가 export 안에서 코드·데이터·테스트·설명을 선택하고, actor 활동 및 기존 replay 로그는 제외한다. 제공자가 만든 HANDOFF·Research에는 이미 관찰한 결과 설명이 있을 수 있다. 이것은 재료의 맥락이며 검토자가 자체 실행을 대신해 믿을 판정이 아니다.

새 도우미는 완전 수집·원본 불변·export 해시를 확인하고, 준비 때 고정된 재현 입력을 그대로 복사한다. 선택한 파일·제외한 파일·입력·도우미 해시를 별도로 기록한다. actor에게 준 입력·소스와 고정 사용자 답변, 기존 export의 bytes는 바꾸지 않는다. 이 수집 후 보완은 최초 독립 재현 전에 수행했으며 네 회차에 동일하게 적용한다.

```powershell
python -B tests/research-foundation/prepare_reproduction.py --export EXPORT --workspace NEW_WORKSPACE --materials REVIEWED_PROJECT_FILE_LIST.json --record PREPARATION_RECORD.json
```

처음 선택 도우미의 단위 검사에서는 시험용 export fixture에 필수 `copied_fixed_input` 상태를 빠뜨려 정상 복사 검사 1개가 실패했다. fixture를 실제 export 계약에 맞춘 뒤 4개 검사가 통과했다. 이 오류는 실제 데이터 수집·재현 실행 전에 발생했다.

최종 마무리에서는 원래 harness의 reproduce-prepare도 선택 도우미를 호출하도록 수정했다. actor 로그가 포함됐는데 제공하지 않았다고 반환하는 경로를 없앴다. clean-reproduction/final-reproduction 폴더 및 ZIP 안의 제외 대상도 검사한다. 이 수정은 사용자 중단 뒤의 도구 보완이며 과거 모델 입력이나 결과를 소급 변경하지 않는다.
