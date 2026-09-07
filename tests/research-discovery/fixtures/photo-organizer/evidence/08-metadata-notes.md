# Chronofile 0.6 — 날짜 읽기 모듈

원천: https://chronofile.example/docs/0.6/dates
작성: Chronofile 유지보수자, 2026-05-17

읽기 함수는 원문 문자열, 파싱한 값, 출처 태그, 시간대 유무를 반환한다. EXIF DateTimeOriginal은 시간대가 없을 수 있고 여러 기기의 시계가 일치한다는 보장은 없다. 파일 수정일은 복사·편집·내보내기로 달라질 수 있다. 아래 구조는 앱이 날짜 출처를 사용자에게 설명할 수 있게 한다.

```python
def date_record(raw, parsed, source, offset=None):
    return {"raw": raw, "parsed": parsed,
            "source": source, "offset": offset}
```

0.6의 읽기 전용 API는 사진 파일에 쓰지 않는다. 사용자 보정값을 기록하려면 별도 저장소나 sidecar를 앱에서 선택해야 한다. JPEG·PNG의 fixture만 포함됐고 HEIC·깨진 메타데이터의 지원 범위는 여기서 확인되지 않는다. 이 문서는 특정 날짜 정렬 정책을 모든 사용자에게 권장하지 않는다.
