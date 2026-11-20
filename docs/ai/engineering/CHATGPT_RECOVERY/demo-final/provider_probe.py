"""One durable, fixed public Gemini readiness probe; never resumes a task."""
import json,subprocess
from pathlib import Path

out=Path(__file__).parent
target=out/'provider-recovery-probe.json'
intent=out/'provider-recovery-probe.intent'
assert not target.exists() and not intent.exists(),'Probe already attempted; inspect evidence before any further outbound'
with intent.open('x') as stream:stream.write('ONE_FIXED_PUBLIC_GENERATION_NO_TOOL_EFFECTS\n')
code=r'''
import json,time,uuid,re
from pathlib import Path
from gateway.gemini import Gemini,SMOKE_PROMPT,ProviderError
from gateway.store import Store,canonical,digest
from gateway.service import Service
from gateway.engineering_provider import effective_policy
root=Path('/state');store=Store(root);config=json.loads((root/'config.json').read_text())
service=Service(store,config,'/workspaces');g=service.gemini;policy=g.settings();limited=effective_policy(service)
with store.connect() as db:
 assert db.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0]==0
 assert db.execute('select mode from engineering_control where project=6').fetchone()[0]=='OFF'
payload={'contents':[{'role':'user','parts':[{'text':SMOKE_PROMPT}]}],
 'generationConfig':{'maxOutputTokens':128,'thinkingConfig':{'thinkingLevel':'minimal'}}}
rid=str(uuid.uuid4());started=time.time();reservation=store.reserve_gemini(policy['project'],limited['limits'],len(canonical(payload).encode())+128)
receipt={'id':rid,'project':policy['project'],'actor':18,'run_id':None,'agent':'provider-readiness','phase':'generateContent',
 'source':'OWNER_AUTHORIZED_FIXED_PUBLIC_RECOVERY_PROBE','model':policy['model'],'at':started,'state':'ATTEMPTING','http_status':None}
store.provider_receipt(receipt)
try:
 with g.sdk_client(timeout=40) as client:
  document=g.sdk_post(client,policy,'generateContent',payload)
 candidate=document['candidates'][0]
 text=''.join(p.get('text','') for p in candidate['content']['parts'] if not p.get('thought')).strip()
 assert candidate.get('finishReason')=='STOP' and text=='QLDAPM_OK'
 assert g.settings()==policy
 usage={k:v for k,v in document.get('usageMetadata',{}).items() if k in {'promptTokenCount','candidatesTokenCount','totalTokenCount'} and type(v) is int and v>=0}
 if 'totalTokenCount' in usage:store.settle_gemini_input(reservation,policy['project'],usage['totalTokenCount'])
 checked=time.time();readiness={'passed':True,'checked_at':checked,'policy_sha256':digest(canonical(policy)),
  'key_sha256':policy['key_sha256'],'model':policy['model'],'source':'ONE_FIXED_PUBLIC_GENERATION','receipt_id':rid}
 path=root/'gemini-readiness.json';temp=path.with_suffix('.tmp');temp.write_text(canonical(readiness));temp.replace(path)
 receipt.update(state='LIVE_SUCCESS',http_status=200,usage=usage,completed_at=checked)
 result={'state':'AVAILABLE','checked_at':checked,'http_status':200,'model':policy['model'],'usage':usage,'receipt_id':rid,
  'policy_limits':limited['limits'],'task_resumed':False,'readiness_lifetime_seconds':300}
except Exception as error:
 status=getattr(error,'provider_http_status',getattr(error,'status',None))
 if isinstance(error,ProviderError):
  match=re.search(r'HTTP=(\d{3})(?:;|$)',str(error))
  if match:status=int(match[1])
 code=str(error).split(';')[0] if isinstance(error,ProviderError) else type(error).__name__
 receipt.update(state='PROVIDER_ERROR',http_status=status,error=code,completed_at=time.time())
 result={'state':'NOT_AVAILABLE','http_status':status,'reason':code,'receipt_id':rid,'task_resumed':False}
finally:store.provider_receipt(receipt)
print(json.dumps(result))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=65)
if p.returncode:raise RuntimeError('PROBE_FAILED_NO_REPLAY; inspect private runtime without printing credentials')
result=json.loads(p.stdout.decode().splitlines()[-1]);target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
