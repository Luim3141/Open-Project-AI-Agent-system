"""Apply only the Owner-approved acceptance of #397; existing Native workflow/RBAC remain authoritative."""
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
approval = json.loads((OUT / 'owner-approval.json').read_text(encoding='utf-8'))
assert approval['decision'] == 'APPROVED' and approval['task_id'] == 397 and approval['version'] == 10
assert approval['head_sha'] == '045c95a4f5b73b32b90d65966c19c97c873f8e8f'
assert approval['subject'] == 'Regression tests GET /healthz'
target = OUT / 'owner-acceptance-result.json'
assert not target.exists(), 'EXISTING_ACCEPTANCE_RECEIPT_PRESERVED'
gh = subprocess.run([r'C:\Program Files\GitHub CLI\gh.exe', 'pr', 'view', '14', '--repo',
    'Luim3141/mini-task-manager', '--json', 'headRefOid,state,url,files'], capture_output=True, text=True, timeout=60)
assert gh.returncode == 0, 'CURRENT_PR_READ_REQUIRED'
pr = json.loads(gh.stdout)
assert pr['headRefOid'] == approval['head_sha'] and pr['state'] == 'OPEN'
assert [f['path'] for f in pr['files']] == ['tests/test_health_regression.py'], 'EXACT_REVIEWED_DIFF_REQUIRED'
code = '''import json,sys
from pathlib import Path
from gateway.store import Store,canonical,digest
from gateway.service import Service
from gateway import engineering
p=json.load(sys.stdin);a=p['approval'];head=a['head_sha'];key='owner-native-397-'+head+'-v10'
store=Store('/state');s=engineering.scoped_service(Service(store,json.loads(Path('/state/config.json').read_text()),'/workspaces'),6)
snapshot=s.execute_actor(18,{'action':'observer_task_progress','arguments':{'task_id':397}})['result']
assert snapshot['version']==10 and snapshot['workflow_status']=='COMPLETED' and snapshot['acceptance_status']=='AWAITING_OWNER_APPROVAL'
assert not snapshot['source_conflicts'] and set(snapshot['acceptance']['missing_gates'])=={'native_final_gate','owner_approval'}
with store.connect() as db:
 result=json.loads(db.execute('SELECT result FROM ai_runs WHERE id=?',('a3f592fc-b91e-4f57-a812-a930bb20e079',)).fetchone()[0])
 assert result['status']=='succeeded' and result['head_sha']==head and result['review_evidence']['verdict']=='PASS'
 assert result['test_evidence']['exit_code']==0 and result['review_evidence']['qa']['exit_code']==0
 assert not db.execute("SELECT 1 FROM ai_queue WHERE state!='finished'").fetchone()
n,who=engineering.authorized(s,18)
assert who['user_id']==18 and who['role']=='AI_SYSTEM_OWNER'
item=n.package(397);assert item['lockVersion']==10 and item['_links']['project']['href']=='/api/v3/projects/6'
payload={'lockVersion':10,'subject':a['subject'],'_links':{'status':{'href':'/api/v3/statuses/35'}}}
form=n.call('/api/v3/work_packages/397/form','POST',payload)
assert not form.get('_embedded',{}).get('validationErrors'), 'NATIVE_FORM_REJECTED'
values=form['_embedded']['schema']['status']['_embedded']['allowedValues']
assert any(v['id']==35 and v['name']=='DONE' and v['isClosed'] for v in values), 'CURRENT_NATIVE_TRANSITION_REQUIRED'
request={'action':'owner_acceptance_native','project_id':6,'path':'/api/v3/work_packages/397','method':'PATCH','payload':payload,'owner_approval_sha256':digest(canonical(a)),'reviewed_head':head}
prior=store.begin(18,key,request)
assert prior is None, 'EXISTING_REQUEST_REQUIRES_READBACK'
# Native enforces the actual Owner identity, current version, status workflow and write hooks.
# A failed/unknown PATCH stays pending; this script never retries a Native write.
changed=n.call('/api/v3/work_packages/397','PATCH',payload)
assert changed['id']==397 and changed['subject']==a['subject'] and changed['_links']['status']['href']=='/api/v3/statuses/35'
store.finish(18,key,changed)
store.record(18,'owner_acceptance_native','397','EXPLICIT_OWNER_APPROVAL',version=digest(canonical(a)))
after=s.execute_actor(18,{'action':'observer_task_progress','arguments':{'task_id':397}})['result']
print(json.dumps({'status':'OWNER_NATIVE_TRANSITION_READBACK','route':'EXISTING_NATIVE_API_WITH_EXPLICIT_OWNER_APPROVAL','actor_id':18,'task_id':397,'before':{'version':10,'status':'READY FOR RELEASE'},'after':{k:after.get(k) for k in ['version','business_status','workflow_status','acceptance_status','acceptance','source_conflicts','notification_events']},'request_key':key,'pr':p['pr']},ensure_ascii=False))
'''
process = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-c', code],
    input=json.dumps({'approval': approval, 'pr': {k: pr[k] for k in ('headRefOid', 'state', 'url')}}),
    text=True, capture_output=True, timeout=150)
if process.returncode:
    # Never repeat this PATCH if there is no positive receipt.
    raise RuntimeError('OWNER_ACCEPTANCE_NEEDS_RECONCILIATION:' + process.stderr[-400:])
data = json.loads(process.stdout)
target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: data[k] for k in ('status', 'actor_id', 'task_id', 'after')}, ensure_ascii=False))
