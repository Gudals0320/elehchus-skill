[Elenchus · 완료]

현재 `normalize`는 `unit`이 정확히 `"celsius"`가 아니면 **`ValueError("unsupported unit")` 예외를 발생시킵니다.**

근거: [project/contract.py 2–3행](/<probe-workspace>/project/contract.py:2).