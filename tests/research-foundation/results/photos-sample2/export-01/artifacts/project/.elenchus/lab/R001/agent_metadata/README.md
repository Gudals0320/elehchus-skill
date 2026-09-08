# 메타데이터 후보 실험

질문: 합성 JPEG·PNG·TIFF 및 손상 입력에서 날짜·방향·형식 메타데이터를 읽을 라이브러리/도구와 실제 실패 조건은 무엇인가?

원본 `project/inputs/`는 읽기 전용이다. 이 작업장은 역할상 쓰기 경계이며 기술적 격리를 보장하지 않는다. 해시 전후 비교는 변경 탐지다. Venv·캐시·임시 파일·주입한 fixture·결과는 이 작업장에 둔다. 제품 코드와 전체 UX는 변경하지 않는다.

실험은 Pillow와 ExifRead의 날짜/방향 읽기 결과, IFD0와 ExifIFD 차이, 확장자와 실제 포맷 차이, 메타데이터 읽기/verify/load의 손상 판정 차이를 기록한다. ExifRead 기본과 strict를 모두 실행한다. 픽셀 디코딩 성공은 이 작은 합성 입력에 대한 결과이며 모든 손상 탐지나 안전성을 보장하지 않는다. 원본에서 관찰된 현상과 새로 주입한 fixture를 결과의 origin으로 구분한다. 날짜 파싱의 달력 유효성은 별도 조건이며 라이브러리의 태그 반환만으로 촬영일 신뢰성을 주장하지 않는다.

재현(이 폴더에서 PowerShell):

```powershell
python -m venv .venv
$env:PIP_CACHE_DIR = "$PWD/.cache/pip"
$env:TEMP = "$PWD/.tmp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pip install -r requirements.txt
$env:PYTHONDONTWRITEBYTECODE = '1'
.venv/Scripts/python.exe probe_metadata.py --inputs ../../../../inputs
```

기대 출력: `probe_results.json`에 원본·주입 fixture별 메타데이터 및 오류, Python/라이브러리 버전, 원본 SHA256 전후 비교. 각 실패는 파일 단위로 반환하여 후속 파일을 계속 처리한다. 원본 해시 차이는 실행 실패로 취급한다.
