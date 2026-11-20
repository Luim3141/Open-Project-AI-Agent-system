"""Combine preserved harness output with actual bounded corrective read-back evidence."""
import hashlib,json
from pathlib import Path

out=Path(__file__).parent
raw=json.loads((out/'business-clone-result.json').read_text())
assert raw['total']==16 and raw['provider_ledger']=={'gemini_usage':0,'receipts':0} and raw['actor19_denied'] is True
checks={r['workflow']:r for r in raw['checks']}
correction=json.loads((out/'wf11-qa-readback.json').read_text())
assert correction['status']=='BUSINESS_PASS_IN_CLONE' and correction['verdict']=='PASSED' and correction['retry_same_evidence_id'] is True
assert checks['WF11']['status']=='FAILED' and checks['WF11']['error_type']=='AssertionError'
checks['WF11']={**checks['WF11'],'status':'BUSINESS_PASS_IN_CLONE','evidence':correction,'raw_harness_result_preserved':True,
 'correction_evidence':'wf11-qa-readback.json','correction_reason':'Harness expected PASS rather than actual enum PASSED; no production logic changed'}
orchestration=json.loads((out/'wf03-native-orchestration.json').read_text());assert orchestration['retry_same_run'] and orchestration['model_used'] is False
checks['WF03']={**checks['WF03'],'expected':'Published start/status/replay Native deterministic query','evidence':orchestration,'supplemental_evidence':'wf03-native-orchestration.json'}
assert all(r['status']=='BUSINESS_PASS_IN_CLONE' for r in checks.values())
result={'status':'16_BOUNDED_BUSINESS_SCENARIOS_PASS_IN_CLONE','passed':16,'total':16,'main_native_writes':0,'provider_calls':0,
 'checks':list(checks.values()),'artifacts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'business-clone-result.json',out/'wf11-qa-readback.json',out/'wf03-native-orchestration.json',out/'history-clone-result.json']},
 'scope':'Real published n8n paths + Gateway business code + actual restored Native + isolated Qdrant/local BGE-M3; candidate WF04 replaces duplicated full-trace branch.',
 'limitations':['One explicitly listed valid scenario per workflow; not every generation/approval/write/error branch.',
 'WF03 actual start question used the Native deterministic count route. Gemini generation is not claimed by this suite.',
 'WF05/06 exact preview/reject only in isolated clone, no Owner approval or Native execution was fabricated.',
 'WF12 scheduler branch was reached through a clone-only bounded webhook; actual production cron definition is retained.',
 'Shared auth/error/signed-contract tests and Store idempotency tests complement these scenarios; branch-complete live retries for every workflow are not claimed.',
 'Raw harness 15/16 retained. WF11 was re-run through actual webhook with documented PASSED enum and repeated request identity.']}
(out/'business-qualified.json').write_text(json.dumps(result,indent=2)+'\n')
purposes={'WF01':'Native ingestion → SQLite/Qdrant','WF02':'Native incremental event synchronization','WF03':'Native deterministic natural-language intake/status','WF04':'Canonical lifecycle history/correlation','WF05':'Exact human proposal preview','WF06':'Exact human decision/rejection','WF07':'Scheduled daily brief for valid readers','WF08':'Sprint risk report','WF09':'Explicit Native bug target/context','WF10':'WBS draft and exact-hash read-back','WF11':'QA automated Native assertions/signed evidence','WF12':'Scheduled weekly report for valid readers','WF13':'Source-bound RAG feedback','WF14':'Durable ingestion job status','WF15':'SQLite/Qdrant reconciliation/integrity','WF16':'Dependency/resources/backlog monitoring'}
lines=['# 16 workflow business scenarios — clone qualification','',
 '16/16 kịch bản nghiệp vụ có bằng chứng thực tế. Không đồng nghĩa mọi nhánh của 16 workflow đã được nghiệm thu toàn diện. MAIN deployment/read-back được ghi riêng trong `deployment.json` và `main-history-readback.json`.','',
 '| WF ID | Purpose | Trigger | MAIN/CLONE | Expected | Actual | Evidence | Status |','|---|---|---|---|---|---|---|---|']
for code,row in sorted(checks.items()):
 trigger='Signed scheduled branch, bounded webhook' if code in {'WF07','WF12'} else 'Authenticated webhook'
 evidence=row.get('correction_evidence') or row.get('supplemental_evidence') or 'business-clone-result.json'
 actual='PASSED, exact evidence replay stable' if code=='WF11' else 'READY 4/4, actor19 remains denied' if code in {'WF07','WF12'} else 'Expected business result/read-back observed'
 lines.append(f"|{code}|{purposes[code]}|{trigger}|CLONE|{row['expected']}|{actual}|{evidence}|BUSINESS PASS (bounded scenario)|")
lines+=['','## Giới hạn nghiệm thu','',*['- '+s for s in result['limitations']]]
(out/'BUSINESS_MATRIX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(result['status'])
