"""One guarded operator reconciliation of a proven pre-transport deadline, never a fake success."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).parent
before=json.loads((OUT/'before.json').read_text())
expected=before['pending']
assert len(expected)==1 and expected[0]['key']=='engineering-e2db6811-44fe-418c-b7dc-12fb9d52d330-plan-parent'
pin=hashlib.sha256(expected[0]['payload'].encode()).hexdigest()
native_pin=hashlib.sha256((OUT.resolve().parents[4]/'openproject/ai/gateway/native.py').read_bytes()).hexdigest()
code=r'''
import hashlib,json,sys,time
from pathlib import Path
from gateway.service import Service
from gateway.store import Store,canonical,digest
from gateway.engineering import scoped_service,authorized
import gateway.native as native_module
assert hashlib.sha256(Path(native_module.__file__).read_bytes()).hexdigest()==sys.argv[2]
root=Path('/state');service=scoped_service(Service(Store(root),json.loads((root/'config.json').read_text()),'/workspaces'),6)
run='e2db6811-44fe-418c-b7dc-12fb9d52d330';key='engineering-'+run+'-plan-parent';expected=sys.argv[1]
with service.store.connect() as db:
 q=db.execute('SELECT state,payload FROM ai_queue WHERE id=?',(run,)).fetchone();assert q['state']=='finished'
 contract=json.loads(q['payload']);failure=json.loads(db.execute('SELECT result FROM ai_runs WHERE id=?',(run,)).fetchone()[0]);assert failure['status']=='blocked' and failure['error']=='REQUEST_DEADLINE_EXCEEDED'
 cp=db.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run,)).fetchone();cpdoc=json.loads(cp['document']);assert cp['version']==2 and cpdoc['error']=='REQUEST_DEADLINE_EXCEEDED' and cpdoc['terminal_known'] and cpdoc['resumable']
 pending=db.execute('SELECT actor,state,payload FROM requests WHERE actor=20 AND key=?',(key,)).fetchone();assert pending['state']=='pending' and hashlib.sha256(pending['payload'].encode()).hexdigest()==expected
 request=json.loads(pending['payload']);assert request['path']=='/api/v3/work_packages/379/activities' and request['method']=='POST' and request['project_id']==6
 assert db.execute("SELECT COUNT(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]==0
 assert db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]=='PAUSED'
native,who=authorized(service,20);item=native.package(379)
assert item['lockVersion']==contract['source_version'] and digest(item.get('description',{}).get('raw',''))==contract['spec_sha256']
activities=native.collection('/api/v3/work_packages/379/activities')
raw=request['payload']['comment']['raw']
matches=[a for a in activities if a.get('comment',{}).get('raw')==raw and a.get('_links',{}).get('user',{}).get('href')=='/api/v3/users/20']
assert not matches,'Existing publication must be reconciled as an actual receipt separately'
# Exact NativeError text is raised only before httpx.stream; the original source hash is pinned in before/source-before.
proof={'run_id':run,'request_key':key,'payload_sha256':expected,'native_source_sha256':sys.argv[2],'failure_code':failure['error'],'checkpoint_version':cp['version'],'source_version':item['lockVersion'],'matching_native_parent_notes':0,'outcome':'REJECTED_NO_WRITE','reason':'PROVEN_PRE_TRANSPORT_DEADLINE','at':time.time()}
with service.store.connect() as db:
 db.execute('BEGIN IMMEDIATE')
 assert db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]=='PAUSED'
 assert db.execute("SELECT COUNT(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]==0
 row=db.execute('SELECT state,payload FROM requests WHERE actor=20 AND key=?',(key,)).fetchone();assert row['state']=='pending' and hashlib.sha256(row['payload'].encode()).hexdigest()==expected
 db.execute("UPDATE requests SET state='rejected',result=? WHERE actor=20 AND key=? AND state='pending'",(canonical(proof),key))
 service.store.record(20,'engineering_unsent_request_reconciled',run,'REJECTED_NO_WRITE',connection=db)
print(json.dumps(proof))
'''
assert not (OUT/'reconciliation.json').exists()
proof=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code,pin,native_pin],timeout=90))
(OUT/'reconciliation.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof))
