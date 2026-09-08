# 공개 파일 해시와 텍스트 해시

`input_sha256`는 harness의 UTF-8 프롬프트 텍스트를 subprocess에 전달하기 전에 계산한 값이다. 파일을 읽을 때 Python의 universal-newline 처리가 적용된다. Windows의 text-mode stdin은 전송 중 LF를 CRLF로 바꿀 수 있으므로 이 값은 관찰된 wire bytes의 해시가 아니다.

`answer_sha256`는 비식별화·공개 전 harness가 사용한 응답 텍스트의 UTF-8 digest다. 최종 응답 파일은 universal-newline 방식으로 읽고, 파일이 없으면 디코딩된 마지막 공개 메시지 텍스트를 사용했다. 이를 원래 응답 전송 bytes나 모델 내부 정규화 관찰로 해석하지 않는다. 기존 두 종류의 텍스트 digest 값은 변경하지 않는다.

`published_input_sha256`·`published_answer_sha256`·`published_events_sha256` 및 별도 실행의 `events_sha256`은 현재 공개 파일의 정확한 bytes를 가리킨다. 초기 Windows writer가 LF 텍스트 digest를 계산한 뒤 text-mode 파일 쓰기로 CRLF를 저장한 경우, 공개 해시 metadata만 실제 파일 bytes에 맞춰 보정한다. 기존 입력·응답·이벤트·고정 fixture/source 파일의 bytes는 변경하지 않는다. metadata 파일의 변경 전/후 hash와 필드 변경은 `publication-digest-audit-*.json`에 보존한다.

후속 writer는 공개 텍스트를 명시적인 UTF-8 bytes로 저장하고 저장된 파일 bytes의 hash를 계산한다. 실제 실행에 사용한 이전 writer 코드는 `runner-before-published-digest-fix.py.txt`, `targeted-before-published-digest-fix.py.txt`, `phase-before-published-digest-fix.py.txt`와 기존 역사적 archive에 보존한다. 각 frozen 기록의 기존 script/shared-runner hash는 덮어쓰지 않는다.
