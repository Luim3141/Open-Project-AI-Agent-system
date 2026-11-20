"""Non-generation CLI/RPC/container transport and worker read-back after restart."""
import datetime,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.openclaw_health import collect
OUT=Path(__file__).parent
label=sys.argv[1];assert label.replace('-','').isalnum()
observations=[]
for attempt in range(5):
    observations.append(collect())
    if observations[-1]['health']=='READY' and observations[-1].get('child_runtime_available') is True:break
    if attempt<4:time.sleep(min(2**attempt,8))
proof={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'openclaw':observations[-1],'startup_observations':observations}
assert proof['openclaw']['health']=='READY' and proof['openclaw']['gateway_rpc_ok'] and proof['openclaw']['child_runtime_available'] is True,proof['openclaw']
code=r'''
import httpx,json,time,sqlite3
urls={'openclaw':'http://host.docker.internal:18789/readyz','n8n':'http://qldapm-n8n-main:5678/healthz/readiness','native':'http://web:8080/health_check'}
result={}
with httpx.Client(trust_env=False,timeout=8) as client:
 for name,url in urls.items():
  r=client.get(url,headers={'Host':'localhost:8088','X-Forwarded-Proto':'https'} if name=='native' else {})
  result[name]={'http_status':r.status_code}
  if name=='openclaw':result[name].update({k:r.json().get(k) for k in ['ready','coreReady']})
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
w=dict(d.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone());w['age_seconds']=time.time()-w['seen']
result['worker']=w
print(json.dumps(result))
'''
proof['container_transport']=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=35))
for name in ['openclaw','native','n8n']:assert proof['container_transport'][name]['http_status']==200,name
assert proof['container_transport']['openclaw']['ready'] is True and proof['container_transport']['openclaw']['coreReady'] is True
assert 0<=proof['container_transport']['worker']['age_seconds']<30
assert proof['container_transport']['worker']['run_id'] is None
gate="import json;from pathlib import Path;v=json.loads(Path('/root/.qldapm-openclaw/active.json').read_text());print(json.dumps({'active':v.get('active')}))"
proof['provider_gate']=json.loads(subprocess.check_output(['wsl','-d','OpenClawGateway','-u','root','--exec','/usr/bin/python3','-c',gate],timeout=15));assert proof['provider_gate']['active'] is False
proof['observer_snapshot']=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/openclaw-health.json').read_text())
proof['status']='CLI_RPC_DOCKER_TRANSPORT_WORKER_PASS_NO_GENERATION'
(OUT/('runtime-'+label+'.json')).write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps({'label':label,'status':proof['status'],'pid':proof['openclaw']['pid'],'worker':proof['container_transport']['worker']}))
