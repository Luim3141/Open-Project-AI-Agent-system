"""Actual candidate worker and Native clone; Google SDK uses synthetic MockTransport only."""
import io,json,sys,time,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from gateway.ai_worker import main
from gateway.gemini import Gemini
from gateway.native import Native
from gateway.store import Store,digest

root=Path('/state');config=json.loads((root/'config.json').read_text())
assert config['openproject_url']=='http://web:8080' and config['project_id']==5
credentials=json.loads((root/'credentials.json').read_text())
native=Native('http://web:8080',credentials['25'],5)
assert native.identity(25)['role']=='PM'
subject='owner-budget-fixture-20261021'
before=native.packages();assert not any(p['subject']==subject for p in before),'EXISTING_CLONE_RESULT_RECONCILE'
store=Store(root);identifier=store.create_run(25)
prompt='Tạo đúng một Subtask '+subject+' cho task 50, giao QA user 23.'
fields={'subject':subject,'type_id':10,'parent_id':50,'assignee_id':23}
approval={'id':str(uuid.uuid4()),'actor':25,'project':5,'prompt_sha256':digest(prompt),'scope':[50],
          'create':fields,'expires':time.time()+600}
(root/'business-acceptance.json').write_text(json.dumps(approval))
(root/'gemini.key').write_text('synthetic-only-no-google-key')
payload={'root':str(root),'workspaces':'/tmp/workspaces','actor':25,'prompt':prompt,'id':identifier,
         'allow_routine_writes':True,'write_scope_ids':[50]}
policy={'model':'gemini-3.5-flash-lite','data_scope':'project-business-content','project':'offline-clone',
        'limits':{'rpm':100,'rpd':100,'tpm':1000000}}
turns=iter([[{'functionCall':{'name':'get_work_package','args':{'id':50}}},
             {'functionCall':{'name':'get_project_options','args':{}}}],
            [{'functionCall':{'name':'create_work_package','args':fields}}],
            [{'text':'{"claims":[],"explanation":"Đã tạo Subtask từ fixture SDK offline."}'}]])
seen=[]
def wire(request):
    seen.append(request.url.path)
    if request.url.path.endswith(':countTokens'):return httpx.Response(200,json={'totalTokens':123})
    assert json.loads(request.content)['generationConfig']['maxOutputTokens']==1500
    return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':next(turns)}}],
        'usageMetadata':{'promptTokenCount':123,'candidatesTokenCount':20,'totalTokenCount':143}})
original=Gemini.sdk_client
def offline(self,transport=None,timeout=120):return original(self,httpx.MockTransport(wire),timeout)
output=io.BytesIO()
with patch.object(Gemini,'settings',return_value=policy),patch.object(Gemini,'sdk_client',offline), \
     patch('sys.stdin',SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode()))), \
     patch('sys.stdout',SimpleNamespace(buffer=output)):
    main()
document=json.loads(output.getvalue());(root/'worker-output.json').write_text(json.dumps(document,ensure_ascii=False))
assert 'result' in document,document
result=document['result'];assert result['status']=='succeeded',result
assert result['business_acceptance']['http_attempts']==6 and result['business_acceptance']['generations']==3
assert result['model_used'] is False
native.deadline=time.monotonic()+90;after=native.packages();new=[p for p in after if p['subject']==subject]
assert len(after)==len(before)+1 and len(new)==1
p=new[0]
for link,expected in (('project','/api/v3/projects/5'),('parent','/api/v3/work_packages/50'),('type','/api/v3/types/10'),('assignee','/api/v3/users/23')):
    assert p['_links'][link]['href']==expected
with store.connect() as db:
    receipts=[json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts where run_id=?',(identifier,))]
    commands=[dict(r) for r in db.execute('select action,actor,run_id,outcome from audit where run_id=?',(identifier,))]
assert len(receipts)==6 and all(r['state']=='MOCK_SUCCESS' for r in receipts)
summary={'passed':True,'provider':'SDK_MOCK_ONLY_NO_GOOGLE','worker':'ACTUAL_CANDIDATE','native':'REAL_ISOLATED_CLONE',
         'run':identifier,'new_id':p['id'],'before':len(before),'after':len(after),'http_mock':len(seen),
         'metadata':result['business_acceptance'],'commands':commands,'receipts':receipts}
(root/'clone-result.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
print(json.dumps(summary,ensure_ascii=False))
