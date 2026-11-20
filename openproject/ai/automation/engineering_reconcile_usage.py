"""Recover session-level telemetry from retained transport artifacts, with before archive.

Does not change quota counters, business data, publication or run completion.
"""
import hashlib
import json
from pathlib import Path

from automation.engineering_worker import command,operator,ROOT
from gateway.engineering_operator import usage_receipt_id
from gateway.store import canonical,digest

RUNS=['5c43e11d-43b7-48b9-a4f8-b5a5e28dbf03','54edcb3a-51c4-4bd0-b7e8-ea797ab51ccb']


def docker_python(source,payload=None):
    prelude='import json\npayload=json.loads('+repr(json.dumps(payload))+')\n'
    return json.loads(command(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],data=(prelude+source).encode()).stdout)


def reconcile():
    state=operator('status')
    if state['mode']!='OFF' or any(r['queue_state']!='finished' for r in state['runs']):raise RuntimeError('ACTIVE_RUN_HOLD')
    documents=[]
    for run_id in RUNS:
        for path in sorted((ROOT/'docs/ai/engineering/runs'/run_id).rglob('*-transport.json')):
            step=path.name.removesuffix('-transport.json')
            dispatch=json.loads(path.with_name(step+'-dispatch.json').read_text())
            transport=json.loads(path.read_text())
            if dispatch['run_id']!=run_id or transport.get('active') is not False:raise ValueError('TRANSPORT_NOT_FENCED')
            receipts=transport.get('receipts',[]);reservation=dispatch['reservation'];session=dispatch['session_id']
            if len(receipts)>reservation['calls']:raise ValueError('ALLOWANCE_MISMATCH')
            for i,receipt in enumerate(receipts):
                documents.append({'id':usage_receipt_id(run_id,step,i,session),'project':reservation['project'],
                    'actor':20,'run_id':run_id,'provider':'google','model':reservation['model'],'source':'openclaw-gate',
                    **receipt,'session_id':session,'step':step,'agent':dispatch['role'],
                    'phase':'countTokens' if receipt['phase']=='countTokens' else 'generateContent',
                    'state':'LIVE_SUCCESS' if receipt['http_status']==200 else 'PROVIDER_ERROR',
                    'at':receipt['started'],'completed_at':receipt['finished'],
                    'duration_seconds':round(receipt['finished']-receipt['started'],3),'attempt':0})
    if len({d['id'] for d in documents})!=len(documents):raise ValueError('RECEIPT_ID_COLLISION')
    before=docker_python("""from gateway.store import Store
from pathlib import Path
s=Store(Path('/state'))
with s.connect() as db:
 rows=[dict(r) for r in db.execute("SELECT * FROM gemini_call_receipts WHERE run_id IN (?,?) AND json_extract(document,'$.source')='openclaw-gate' ORDER BY id",payload)]
print(json.dumps(rows))""",RUNS)
    archive=ROOT/'docs/ai/engineering/provider-receipts-before-session-fix.json'
    if archive.exists():raise ValueError('RECOVERY_ALREADY_ARCHIVED_REVIEW_BEFORE_REPEAT')
    archive.write_text(json.dumps(before,indent=2)+'\n')
    result=docker_python("""from gateway.store import Store,canonical,digest
from gateway.agent_trace import current_run
from pathlib import Path
s=Store(Path('/state'))
with s.connect() as db:
 db.execute('BEGIN IMMEDIATE')
 rows=[dict(r) for r in db.execute("SELECT * FROM gemini_call_receipts WHERE run_id IN (?,?) AND json_extract(document,'$.source')='openclaw-gate' ORDER BY id",payload['runs'])]
 if digest(canonical(rows))!=payload['before_sha256']:raise ValueError('RECEIPTS_CHANGED')
 db.execute("DELETE FROM gemini_call_receipts WHERE run_id IN (?,?) AND json_extract(document,'$.source')='openclaw-gate'",payload['runs'])
 for d in payload['documents']:db.execute('INSERT INTO gemini_call_receipts VALUES(?,?,?,?,?)',(d['id'],d['project'],20,d['run_id'],canonical(d)))
for identifier in payload['runs']:
 token=current_run.set((s,s.agent_run(20,6,identifier)))
 try:s.record(20,'engineering_usage_reconciled',identifier,'SESSION_SCOPED_FROM_TRANSPORT',version=payload['before_sha256'])
 finally:current_run.reset(token)
print(json.dumps({'before':len(rows),'after':len(payload['documents']),'quota_counters_changed':False,'business_writes':0}))""",
        {'runs':RUNS,'before_sha256':digest(canonical(before)),'documents':documents})
    result['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    result['by_run']={run:{'requests':sum(d['run_id']==run for d in documents),
        'tokens_reported':sum((d.get('usage') or {}).get('totalTokenCount',0) for d in documents if d['run_id']==run)} for run in RUNS}
    (ROOT/'docs/ai/engineering/provider-receipts-session-fix.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':reconcile()
