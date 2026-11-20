"""One-shot exact read-back reconciliation of this E2E's lost relation ACK; no Native write."""
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
target = OUT / 'planning-relation-readback.json'
assert not target.exists(), 'EXISTING_RECONCILIATION_PRESERVED'
code = '''import json,sqlite3,time
from pathlib import Path
from gateway.store import Store,canonical,digest
from gateway.service import Service
from gateway import engineering
run_id='8f93d0a1-8115-49b5-bc73-2487e778a7cd'
key='engineering-'+run_id+'-plan-dep-v2-feedback-d8b7006b5cff1bc4'
store=Store('/state');service=engineering.scoped_service(Service(store,json.loads(Path('/state/config.json').read_text()),'/workspaces'),6)
native,who=engineering.authorized(service,18)
with store.connect() as db:
 row=db.execute('SELECT payload,state FROM requests WHERE actor=20 AND key=?',(key,)).fetchone()
 assert row and row['state']=='pending', 'EXACT_PENDING_RECEIPT_REQUIRED'
 payload=row['payload'];request=json.loads(payload)
 assert request=={'action':'engineering_native_plan-dep-v2-feedback-d8b7006b5cff1bc4','method':'POST','path':'/api/v3/work_packages/396/relations','payload':{'type':'precedes','_links':{'from':{'href':'/api/v3/work_packages/396'},'to':{'href':'/api/v3/work_packages/397'}}},'project_id':6}, 'EXACT_AUTHORIZED_POST_REQUIRED'
 plan=json.loads(db.execute('SELECT document FROM engineering_plans WHERE id=?',(run_id,)).fetchone()[0])
 assert plan['state']=='PLANNING' and plan['native_units']['feedback-d8b7006b5cff1bc4']['id']==397
 assert not db.execute("SELECT 1 FROM ai_queue WHERE state!='finished'").fetchone(), 'IDLE_REQUIRED'
 contract=json.loads(db.execute('SELECT payload FROM ai_queue WHERE id=?',(run_id,)).fetchone()[0])
item=native.package(379)
assert item['lockVersion']==contract['source_version'] and digest(item.get('description',{}).get('raw',''))==contract['spec_sha256'], 'CURRENT_SOURCE_REQUIRED'
packages=[native.package(i) for i in (396,397)]
assert all(p['_links']['project']['href']=='/api/v3/projects/6' for p in packages)
def edge(r):
 a=r.get('_links',{}).get('from',{}).get('href');b=r.get('_links',{}).get('to',{}).get('href')
 if r.get('type')=='follows':a,b=b,a
 return (a,b) if r.get('type') in ('follows','precedes') and r.get('lag') is None else None
expected=('/api/v3/work_packages/396','/api/v3/work_packages/397')
matches=[r for r in native.relations(packages) if edge(r)==expected]
assert len(matches)==1 and matches[0]['id']==366, 'ONE_EXACT_EXISTING_RELATION_REQUIRED'
found=native.call('/api/v3/relations/366')
assert edge(found)==expected and found['id']==366
# Preserve the pre-reconciliation state outside the repository before changing only this ledger row.
backup=Path('/state/e2e-reconciliation-before.sqlite')
assert not backup.exists(), 'EXISTING_BACKUP_PRESERVED'
with sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True) as source,sqlite3.connect(backup) as destination:source.backup(destination)
with store.connect() as db:
 db.execute('BEGIN IMMEDIATE')
 assert not db.execute("SELECT 1 FROM ai_queue WHERE state!='finished'").fetchone()
 count=db.execute("UPDATE requests SET state='done',result=? WHERE actor=20 AND key=? AND state='pending' AND payload=?",(canonical(found),key,payload)).rowcount
 assert count==1, 'PENDING_RECEIPT_CHANGED'
 store.record(18,'engineering_native_readback',key,'VERIFIED_EXISTING_RELATION',version=digest(payload),connection=db)
print(json.dumps({'status':'VERIFIED_EXISTING_RELATION','run_id':run_id,'request_key':key,'request_sha256':digest(payload),'relation_id':366,'from_id':396,'to_id':397,'native_writes':0,'runtime_completion_changed':False,'before_backup':'PRIVATE_RUNTIME_SQLITE_SNAPSHOT'}))
'''
result = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=code, text=True, capture_output=True, timeout=150)
if result.returncode:
    # Assertions contain fixed codes only; no secrets or Native response bodies.
    print(result.stderr[-1200:])
    raise RuntimeError('EXACT_RELATION_RECONCILIATION_FAILED')
data = json.loads(result.stdout)
target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
print(json.dumps(data))
