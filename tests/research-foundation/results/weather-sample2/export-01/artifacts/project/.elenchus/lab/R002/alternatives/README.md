# 처리 대안 독립 실험

질문: Python 표준 라이브러리와 pandas에서 UTC/DST·결측·단위를 같은 의미로 유지할 수 있는가? SQLite 재수집은 입력 순서에 어떤 영향을 받는가? Polars/Arrow 및 기상 전용 client가 대신 해결하는 범위는 무엇인가?

실험 입력은 R001의 실제 Open-Meteo ERA5 JSON과 메타데이터를 읽기 전용으로 사용한다. 변경 시나리오는 메모리 사본으로 만든 뒤 이 디렉터리에만 쓴다. main module은 실행 시 사본·해시를 보존하고 사본만 import한다. 모든 실험 산출물은 `runs/<UTC 시각>/`에 남긴다. 재현되는 오류는 실제 제공자 오류가 아닌 명시적 주입/경계 실험이다.

예상 기준:
- 실제 응답 2개의 pandas 독립 단위 변환은 메인 정규화 결과와 부동소수점 허용오차 내 일치해야 한다.
- UTC에서 지역 시간대로 변환하면 DST 반복 시각의 UTC offset이 보존되어야 한다. naive 지역시각을 붙이는 경로는 모호하거나 존재하지 않는 시각을 명시적으로 다뤄야 한다.
- NULL과 강수 0은 구별되어야 한다. pandas 기본 합계와 SQLite 합계의 all-null 결과 차이를 실제로 확인한다.
- 같은 원본 재입력은 논리 행 수를 늘리지 않아야 한다. 과거/최신 응답 순서 교체는 정책 판단 자료로 남긴다.
- 원본 입력 바이트 해시는 실행 전후 동일해야 한다.

R002 디렉터리에서 재실행:

```powershell
.\.venv\Scripts\python.exe -B .\alternatives\probe_processing.py
```

pandas와 tzdata는 R002 기존 연구 venv에서만 사용한다. Polars, Arrow, 기상 client는 추가 설치하지 않고 공식 문서/저장소 범위의 비교로 한정한다. 대규모 성능이나 해당 client의 실제 수집 성공은 이 실험이 입증하지 않는다.
