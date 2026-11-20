"""Owner-authorized single continuation of the existing run, fail closed on any drift."""
import hashlib,json,subprocess
from pathlib import Path

out=Path(__file__).parent
run_id='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
probe=json.loads((out/'provider-recovery-probe.json').read_text())
assert probe['state']=='AVAILABLE' and probe['http_status']==200
journal=json.loads((out.parents[1]/'runs'/run_id/'delivery-steps.json').read_text(encoding='utf-8'))
assert journal['run_id']==run_id and set(journal['steps'])=={'context','prepare','dev-0'}
tree=subprocess.run(['wsl','-d','OpenClawGateway','-u','openclaw','--exec','/usr/bin/git','-C',
 '/home/openclaw/engineering/feedback-2ec52f6742aa972f','diff','--no-ext-diff',journal['base_sha'],'--','.',
 ':(exclude)skills',':(exclude)AGENTS.md',':(exclude)SOUL.md'],capture_output=True,check=True,timeout=30)
assert hashlib.sha256(tree.stdout).hexdigest()==journal['revision']
code=r'''
import json,time
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service,authorized
from gateway.engineering_lifecycle import load,resume,source_matches
from gateway.engineering_observability import describe_run
root=Path('/state');store=Store(root);service=scoped_service(Service(store,json.loads((root/'config.json').read_text()),'/workspaces'),6)
rid='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
native,_=authorized(service,18)
with store.connect() as db:
 row=db.execute('select q.state,q.payload,r.result from ai_queue q join ai_runs r on r.id=q.id where q.id=?',(rid,)).fetchone()
 payload=json.loads(row['payload']);result=json.loads(row['result']);cp=load(store,rid)
 assert row['state']=='finished' and payload['recovery_count']==2 and cp['version']==16
 assert db.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0]==0
 assert db.execute('select mode from engineering_control where project=6').fetchone()[0]=='OFF'
 assert not db.execute("select 1 from requests where key like ? and state not in ('done','rejected')",('engineering-'+rid+'-%',)).fetchone()
item=native.package(391);assert item['_links']['project']['href']=='/api/v3/projects/6'
assert source_matches(store,20,rid,payload,item)
summary=describe_run(service,{'id':rid,'native_id':391,'unit':payload['unit'],'created_at':0,'queue_state':'finished','result':result,'checkpoint':cp})
assert summary['budget']['cumulative_calls']==36 and summary['resume']['eligible'] is True
assert summary['resume']['provider_recovery']['verified'] is True
print(json.dumps({'preflight':'PASS','native_version':item['lockVersion'],'summary':summary['resume'],'result':resume(service,18,rid,16)}))
'''
# Exclusive durable intent prevents an accidental second command after an unknown CLI outcome.
with (out/'wp391-continuation.intent').open('x') as stream:stream.write('MAX_ONE_REAL_CONTINUATION; INSPECT_QUEUE_ON_UNKNOWN; NEVER_REPLAY\n')
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=60)
if p.returncode:raise RuntimeError('RESUME_NOT_CONFIRMED_DO_NOT_REPLAY; inspect scoped state')
result=json.loads(p.stdout);(out/'wp391-continuation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
