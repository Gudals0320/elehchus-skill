"""Render existing scanner JSON as a local, non-executing review document."""
import argparse
from collections import defaultdict
import html
import json
from pathlib import Path

ORIENTATION = {
    1:'정방향 (변환 없음)', 2:'좌우 반전', 3:'180도 회전', 4:'상하 반전',
    5:'주대각선 전치 (반전 포함)', 6:'시계 방향 90도 회전',
    7:'반대각선 전치 (반전 포함)', 8:'반시계 방향 90도 회전',
}
REASONS = {
    'exact_byte_duplicate':'다른 경로의 파일과 내용이 정확히 같음',
    'capture_date_missing':'촬영 날짜 태그 없음',
    'capture_timezone_unknown':'촬영 시각의 시간대 미상; UTC 추정 안 함',
    'capture_invalid_date':'촬영 날짜 값 해석 실패',
    'capture_invalid_offset':'촬영 시각 오프셋 값 해석 실패',
    'capture_conflict':'촬영 날짜 태그 간 상충',
    'orientation_missing':'회전 태그 없음; 방향을 촬영 사실로 확정하지 않음',
    'orientation_invalid':'회전 태그 값 해석 불가',
    'orientation_transform_for_display':'표시를 위한 회전/반전 해석 있음',
    'invalid_image':'이미지 식별·구조 검사 또는 디코딩 실패',
    'non_image_or_unsupported':'비이미지 또는 현재 파서 미지원',
    'unrecognized_image':'이미지 확장자이나 식별 실패; 손상/미지원 구분 미확정',
    'extension_format_mismatch':'확장자와 파서가 식별한 형식이 다름',
}


def cell(value):
    """Render untrusted filenames/metadata as text, not Markdown or HTML."""
    text='—' if value is None or value=='' else str(value)
    text=html.escape(text,quote=True).replace('\r',' ').replace('\n',' ')
    for char in ('|','`','[',']','*','_','\\'):
        text=text.replace(char,f'&#{ord(char)};')
    return text


def dimensions(value):
    return '×'.join(map(str,value)) if value else '미확인'


def orientation_interpretation(row):
    if row.get('metadata_status')!='ok':
        return '메타데이터 읽기 미완료'
    value=row.get('orientation')
    return ORIENTATION.get(value,'태그 없음' if value is None else '유효한 1~8 값이 아님')


def date_evidence(row):
    evidence=[]
    for date in row.get('dates',[]):
        meaning={'capture':'촬영', 'modified':'수정', 'digitized':'디지털화'}.get(date['meaning'],date['meaning'])
        subsecond=f"; subsec={date['subsecond_raw']}" if date.get('subsecond_raw') is not None else ''
        evidence.append(f"{date['source']} [{meaning}] = {date['raw']}{subsecond}; offset={date['offset_raw'] or '없음'}; 상태={date['status']}")
    return '; '.join(evidence) or ('날짜 태그 없음' if row.get('metadata_status')=='ok' else '날짜 메타데이터 미확인')


def render_review(report):
    if report.get('schema_version')!=1:
        raise ValueError('unsupported report schema')
    rows={row['path']:row for row in report['records']}
    candidates=report['candidates']
    if len(rows)!=len(report['records']) or set(rows)!={row['path'] for row in candidates} or len(candidates)!=len(rows):
        raise ValueError('each record needs exactly one matching review candidate')
    if any(row.get('action')!='review_only' for row in candidates):
        raise ValueError('only review_only candidates can be rendered')
    groups=defaultdict(list)
    for candidate in candidates:
        groups[candidate['date_bucket']].append(candidate)
    lines=['# 로컬 사진 검토 결과', '',
           f"입력 항목 {len(rows)}개 · 동일 내용 그룹 {len(report['exact_groups'])}개 · 분석기 {cell(report['engine']['name'])} {cell(report['engine']['version'])}", '',
           '이 문서는 검토용 결과다. 파일 삭제·이동·병합 명령이나 보존할 대표 파일 선택은 포함하지 않는다. 원본 바이트가 같다는 판정과 비슷한 사진이라는 판단은 별개다.', '',
           '## 날짜별 정리 후보', '',
           '날짜는 유효한 DateTimeOriginal의 현지 날짜를 사용했다. 파일명·파일 시스템 시각·수정일을 촬영일로 대체하지 않았다. 시간대가 없으면 UTC를 추정하지 않으며, 충돌/해석 실패는 날짜 미지정으로 남긴다.', '']
    for bucket in sorted(groups,key=lambda day:(day is None,day or '')):
        lines += [f"### {cell(bucket) if bucket else '날짜 미지정'}", '',
                  '| 파일 | 날짜 근거 | 검토 이유 | 동일 그룹 |', '|---|---|---|---|']
        for candidate in sorted(groups[bucket],key=lambda row:row['path']):
            row=rows[candidate['path']]
            reasons='; '.join(REASONS.get(reason,reason) for reason in candidate['review_reasons']) or '추가 경고 없음'
            lines += [f"| {cell(row['path'])} | {cell(date_evidence(row))} | {cell(reasons)} | {cell(candidate['exact_group'])} |"]
        lines.append('')
    lines += ['## 동일 파일 그룹', '', '파일 크기·SHA-256 후보를 실제 바이트 비교로 확인했다. 그룹 안에서 어느 파일을 보존할지는 선택하지 않았다.', '']
    if not report['exact_groups']:
        lines += ['확인된 동일 파일 그룹 없음.', '']
    for group in report['exact_groups']:
        lines += [f"### {cell(group['id'])}", '',f"각 {group['size']} bytes · 근거: {cell(group['evidence'])}", '',f"SHA-256: {cell(group['sha256'])}", '']
        lines += [f"- {cell(member)}" for member in group['members']]
        lines.append('')
    lines += ['## 회전 원시값과 해석·실행 결과', '',
              '원시값은 최초 메타데이터 조회에서 얻은 값이다. 표준 해석은 그 값이 지시하는 변환이며 실제 표시 치수는 디코딩 후 EXIF 정규화를 실행해 얻었다. PNG의 메타데이터 조회는 내부 디코딩을 유발할 수 있고, TIFF는 파서가 이미 회전할 수 있어 변환을 수동으로 중복 적용하지 않았다. 치수만으로 화상 내용이나 촬영 당시 방향의 진실을 증명하지 않는다.', '',
              '| 파일 | 형식 | 읽은 Orientation | 표준 해석 | 저장 치수 | 최초 파서 치수 | 실제 표시 치수 | 디코딩 |',
              '|---|---|---|---|---|---|---|---|']
    for row in report['records']:
        if row.get('format'):
            values=[row['path'],row['format'],row['orientation'],orientation_interpretation(row),
                    dimensions(row['encoded_size']),dimensions(row['reported_size']),dimensions(row['display_size']),row['decode_status']]
            lines += ['| '+' | '.join(cell(value) for value in values)+' |']
    lines += ['', '## 오류·미검증', '', '| 파일 | 확인 상태 | 오류 단계/내용 |', '|---|---|---|']
    for row in report['records']:
        if row['status']!='ok':
            detail='; '.join(f"{err['stage']}: {err['type']} — {err['message']}" for err in row['errors']) or row['status']
            lines += [f"| {cell(row['path'])} | {cell(row['status'])} | {cell(detail)} |"]
    lines += ['', '검증 범위는 제공된 작은 합성 JPEG·PNG·TIFF와 손상 입력, 연구 작업장의 명시적 합성 변형이다. HEIC·RAW·실제 카메라 원본·대량 사진 정확도/성능은 검증하지 않았다. 설치된 의존성을 사용한 분석과 이 문서 생성은 로컬에서 실행된다. 최종 화면·동선·저장소 설계는 이후 제작자의 선택이다.', '']
    return '\n'.join(lines)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=json.loads(args.report.read_text(encoding='utf-8'))
    output=render_review(report)
    with args.output.open('x',encoding='utf-8') as stream:
        stream.write(output)
    print(f'Review written: {args.output.name}')
