"""Reuse the one existing clone fixture: simulate only lost local receipt, never another create."""
import json,time
from pathlib import Path
from unittest.mock import patch
from gateway.gemini import Gemini
from gateway.native import Native
from gateway.service import Service
from gateway.store import Store
root=Path('/state');old=json.loads((root/'clone-result.json').read_text());identifier=old['run'];key=old['metadata']['native_create_request_key']
store=Store(root);report=json.loads((root/'worker-output.json').read_text())['result']
assert old['new_id']==369
before_receipts=None
with store.connect() as db:
    original=dict(db.execute('select * from requests where actor=25 and key=?',(key,)).fetchone())
    assert original['state']=='done' and json.loads(original['result'])['result']['id']==369
    before_receipts=db.execute('select count(*) from gemini_call_receipts').fetchone()[0]
    db.execute("update requests set state='pending',result=null where actor=25 and key=?",(key,))
for c in report['tools']:
    if c['action']=='create_work_package':c['result']={'error':'NativeError','outcome_unknown':True,'status':503}
report['error']='GEMINI_REQUEST_BUDGET_EXHAUSTED'
store.finish_run(25,identifier,report,'failed_or_unknown')
service=Service(store,json.loads((root/'config.json').read_text()),'/tmp/workspaces')
methods=[];actual=Native.call
def read_only(self,path,method='GET',payload=None):
    assert method=='GET','RECOVERY_MUST_NEVER_MUTATE_NATIVE'
    methods.append([method,path.split('?')[0]])
    return actual(self,path,method,payload)
with patch.object(Native,'call',read_only),patch.object(Gemini,'sdk_client',side_effect=AssertionError('NO_GOOGLE')):
    receipt=service.execute_actor(25,{'action':'reconcile_request','arguments':{'key':key}})
    view=service.execute_actor(25,{'action':'get_ai_run','arguments':{'id':identifier}})['result']
assert receipt['result']['reconciled'] is True and receipt['result']['result']['id']==369
assert view['state']=='failed_or_unknown' and view['result']['native_reconciled'] is True and view['result']['status']=='partial'
assert view['result']['provider_report_completed'] is False
assert store.run(25,identifier)['result']['error']=='GEMINI_REQUEST_BUDGET_EXHAUSTED'
with store.connect() as db:assert db.execute('select count(*) from gemini_call_receipts').fetchone()[0]==before_receipts
result={'passed':True,'native_mutations':0,'google_calls':0,'id':369,'calls':methods,'receipt_correlation':receipt['result']['correlation_id'],
        'display_heading':view['result']['heading'],'original_worker_state':view['state'],'display_status':view['result']['status']}
(root/'clone-recovery-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print(json.dumps(result,ensure_ascii=False))
