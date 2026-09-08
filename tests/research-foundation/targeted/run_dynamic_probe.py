"""One additional fresh CLI probe of a new question after an existing R004."""
from pathlib import Path
import json
import shutil
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
import run_probes

io = run_probes.io
base = run_probes.FOUNDATION
out = Path(__file__).parent / 'dynamic-followup'
w = base / '.work/targeted-dynamic'
if out.exists() or w.exists():
    raise ValueError('preserve existing dynamic probe')
out.mkdir()
shutil.copytree(base/'baseline/primary/runtime', w/'skill')
files = {
    '.elenchus/topology.md': '# Topology: 공급자 A 데이터를 로컬에 저장\n- 사용자 결정: 공급자 A 필수, 비용 0, 새 계정·결제 금지.\n- R004에서 제공 샘플 필드 매핑은 확인했다. 실제 접근 가능성은 아직 조사하지 않았다.\n',
    '.elenchus/research/index.md': '# Research Index\n| ID | 중립 질문 | 상태 | 영향 | 파일 |\n|---|---|---|---|---|\n| R004 | 샘플 필드의 의미는 무엇인가 | 확정 | 데이터 정규화 | [R004-fields.md](R004-fields.md) |\n',
    '.elenchus/research/R004-fields.md': '# Research R004: 샘플 필드 의미\n- 상태: 확정\n판정: 결론 가능\n가상 제공 샘플 t는 UTC epoch초, value는 섭씨다. 실제 원격 수집·접근 계약은 이 질문의 범위가 아니었으며 아직 확인하지 않았다.\n',
    'new-contract.md': '# 새로운 접근 계약 — 가상 시나리오\n실제 외부 서비스는 제공하지 않는다. 이 시험용 계약에서 공급자 A는 무료 접근을 종료했으며 새 계정과 유료 구독만 지원한다. 샘플 JSON은 실제 원격 접근의 증거가 아니다.\n',
}
for name, content in files.items():
    target=w/'project'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content.encode())
before=io.tree_hashes(w/'project')
prompt=('skill/SKILL.md를 읽고 project/에 아래 요청을 수행하세요. skill/은 읽기 전용이며 상위 평가/다른 작업/개인 설정을 읽지 마세요.\n\n'
        '$elenchus 기존 데이터 저장 목적의 연구를 이어가자. 필드 매핑 다음에 새 접근 계약을 확인했어. project/new-contract.md를 보고 현재 목적 안의 후속 문제로 검토하고, 기존 연구의 결론과 번호는 보존해줘. 새 계정이나 비용을 허용한 것은 아니야. 가능한 결론과 다음 상태까지 정리해줘.')
io.write_utf8(out/'input.md',prompt)
io.write_json(out/'protocol.json',{'kind':'additional_targeted_cli_probe','started_utc':datetime.now(timezone.utc).isoformat(),'source_revision':'7f60615183899d6fdfa47c8391688df600010b02','model':'gpt-6-astra','effort':'xhigh','web':'disabled','delegation':'unavailable','session_deadline':None,'responses':1,'files':files,'runner_sha256':io.sha(Path(__file__).read_bytes())})
command=io.cli_command(sys.argv[1],w,w/'final.md','gpt-6-astra','xhigh')
result=io.call_cli(command,prompt,None)
redactor=io.Redactor({str(w.resolve()):'<probe-workspace>'})
events,excluded=io.public_events(result['stdout'],redactor)
io.write_utf8(out/'answer.md',redactor.text((w/'final.md').read_text(encoding='utf-8')) if (w/'final.md').exists() else '')
io.write_utf8(out/'events.jsonl',''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events))
io.write_utf8(out/'stderr.txt',redactor.text(result['stderr']))
for p in io.regular_files(w/'project'):
    target=out/'project'/p.relative_to(w/'project');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
io.write_json(out/'summary.json',{'exit_code':result['exit_code'],'timed_out':result['timed_out'],'elapsed_seconds':result['elapsed_seconds'],'finished_utc':datetime.now(timezone.utc).isoformat(),'before':before,'after':io.tree_hashes(w/'project'),'published_input_sha256':io.sha((out/'input.md').read_bytes()),'published_answer_sha256':io.sha((out/'answer.md').read_bytes()),'published_events_sha256':io.sha((out/'events.jsonl').read_bytes()),'usage':[e['usage'] for e in events if e.get('type')=='turn.completed' and 'usage' in e],'command':redactor.apply(command),'excluded_event_types':excluded,'quality':'manual review pending'})
print(json.dumps({'exit_code':result['exit_code'],'elapsed_seconds':result['elapsed_seconds']}))
