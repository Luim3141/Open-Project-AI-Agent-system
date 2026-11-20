"""Read-only baseline timing; no inference, control changes or Native mutations."""
import datetime,json,os,statistics,subprocess,time,uuid
from pathlib import Path
import httpx
OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization'
data=json.loads((private/'baseline-native.json').read_text(encoding='utf-8'));token=data['token']
rows=[]
for index in range(5):
    begin=time.monotonic()
    r=httpx.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+token},
                 json={'action':'engineering_status','arguments':{},'project_id':6,'idempotency_key':str(uuid.uuid4())},trust_env=False,timeout=100)
    elapsed=time.monotonic()-begin;row={'index':index,'http':r.status_code,'seconds':round(elapsed,4),'bytes':len(r.content)};rows.append(row)
    if r.status_code==200:
        reply=r.json()['result'];row.update(mode=reply['mode'],active=reply['queue']['active'])
        (private/'status-before.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(row),flush=True)
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'route':'Actual MAIN Gateway HTTP; Core/browser measurements separate','rows':rows,
        'p50_seconds':statistics.median(r['seconds'] for r in rows),'p95_seconds':max(r['seconds'] for r in rows),'samples':5,'generation_calls':0}
(OUT/'performance-before.json').write_text(json.dumps(result,indent=2)+'\n')
code="""import json,time,collections
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service,status
from gateway.native import Native
from gateway import engineering_github_sync as gh
metrics=[];old=Native.call
def measured(self,path,*a,**kw):
 t=time.monotonic()
 try:return old(self,path,*a,**kw)
 finally:metrics.append({'kind':'Native','path':path.split('?')[0],'seconds':round(time.monotonic()-t,4)})
Native.call=measured
original=gh.fetch_pull_requests
def github(*a,**kw):
 t=time.monotonic()
 try:return original(*a,**kw)
 finally:metrics.append({'kind':'GitHub','seconds':round(time.monotonic()-t,4)})
gh.fetch_pull_requests=github
s=scoped_service(Service(Store('/state'),json.load(open('/state/config.json')),'/workspaces'),6)
t=time.monotonic();d=status(s,20)
print(json.dumps({'total_seconds':round(time.monotonic()-t,4),'calls':metrics,'mode':d['mode']}))"""
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=150)
if p.returncode:(private/'profile-before-error.log').write_bytes(p.stderr);raise RuntimeError('PROFILE_FAILED_PRIVATE_LOG')
profile=json.loads(p.stdout);(OUT/'profile-before.json').write_text(json.dumps(profile,indent=2)+'\n');print(json.dumps({'profile_total':profile['total_seconds'],'native_calls':sum(r['kind']=='Native' for r in profile['calls'])}))
