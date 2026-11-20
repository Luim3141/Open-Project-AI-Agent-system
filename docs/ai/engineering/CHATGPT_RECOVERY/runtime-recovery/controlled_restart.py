"""Explicit MAIN-only stop/start fallback; never restart Docker Desktop or unrelated apps."""
import datetime,json,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).parent
targets=['qldapm-openproject-web-1','qldapm-ai-gateway-1','qldapm-n8n-main','qldapm-openproject-proxy-1','qldapm-openproject-worker-1','qldapm-openproject-cron-1','qldapm-openproject-hocuspocus-1','qldapm-qdrant','qldapm-openproject-cache-1','qldapm-openproject-db-1']
action=sys.argv[1];assert action in {'stop','start'}
baseline=json.loads((OUT/'baseline.json').read_text())
assert len(targets)==len(set(targets)) and all(n.startswith('qldapm-') for n in targets)
for name in targets:
    current=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    expected=baseline['containers'][name]
    assert current['Id']==expected['id'] and current['Image']==expected['image'],name
record={'action':action,'targets':targets,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'docker_desktop_restart':'NOT_EXECUTED_UNRELATED_BIRDSONG_WORKLOADS_RUNNING','volumes_removed':False}
if action=='stop':
    query="import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps([d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],d.execute(\"SELECT count(*) FROM ai_queue WHERE state!='finished'\").fetchone()[0],d.execute('SELECT enabled FROM delegated_control WHERE project=6').fetchone()[0]]))"
    assert json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',query]))==['PAUSED',0,0]
    js="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(d.prepare(\"SELECT count(*) AS n FROM execution_entity WHERE status IN ('new','running')\").get().n)"
    for attempt in range(10):
        if subprocess.check_output(['docker','exec','qldapm-n8n-main','node','-e',js]).strip()==b'0':break
        time.sleep(2)
    else:raise RuntimeError('N8N_ACTIVE_EXECUTION_STOP_DENIED')
    subprocess.run(['docker','stop','--time','45',*targets],check=True,timeout=180,capture_output=True)
    assert all(json.loads(subprocess.check_output(['docker','inspect',n]))[0]['State']['Status']=='exited' for n in targets)
else:
    # Start frontend/Gateway before DB deliberately: recovery must tolerate dependency ordering.
    subprocess.run(['docker','start',*targets],check=True,timeout=180,capture_output=True)
    import httpx
    endpoints={'gateway':('http://127.0.0.1:18089/health',{'Host':'qldapm-ai-gateway-1:8090'}),'core':('http://127.0.0.1:18088/health_check',{}),'n8n':('http://127.0.0.1:5679/healthz/readiness',{}),'qdrant':('http://127.0.0.1:6333/collections',{}),'ollama':('http://127.0.0.1:11434/api/tags',{})}
    deadline=time.monotonic()+300;status={}
    with httpx.Client(trust_env=False,timeout=4) as client:
        while time.monotonic()<deadline:
            for key,(url,headers) in endpoints.items():
                try:status[key]=client.get(url,headers=headers).status_code
                except httpx.HTTPError:status[key]='STARTING'
            if all(v==200 for v in status.values()):break
            time.sleep(3)
        else:raise RuntimeError('MAIN_STARTUP_NOT_READY:'+json.dumps(status))
    record['readiness']=status
record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/('coordinated-'+action+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
