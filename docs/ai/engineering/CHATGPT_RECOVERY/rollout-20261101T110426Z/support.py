"""Exact approved rollout helpers; secret-bearing command output stays private."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,time
RUN=Path(__file__).parent
CONTEXT=json.loads((RUN/'context.json').read_text())
ROOT=Path(CONTEXT['root']);PHASE=Path(CONTEXT['phase2']);PRIVATE=Path(CONTEXT['private'])
sys.path.insert(0,str(ROOT/'openproject/ai'))
PROPOSAL=json.loads((PHASE/'rollout-proposal.json').read_text())
assert hashlib.sha256((PHASE/'rollout-proposal.json').read_bytes()).hexdigest()==CONTEXT['approved_hash']

def execute(args,*,data=None,timeout=240,name='command'):
    p=subprocess.run(args,input=data,capture_output=True,timeout=timeout,cwd=ROOT)
    if p.returncode:
        (PRIVATE/(name+'-failure.log')).write_bytes(p.stdout+p.stderr)
        raise RuntimeError(name.upper()+'_FAILED_PRIVATE_LOG')
    return p.stdout

def docker(*args,**kw):return execute(['docker',*args],**kw)
def inspect(name):return json.loads(docker('inspect',name))[0]
def write(name,value):
    (RUN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def stage(name,detail=''):
    CONTEXT['stage']=name;write('context.json',CONTEXT)
    with (RUN/'LEDGER.md').open('a',encoding='utf-8') as f:f.write(datetime.now(timezone.utc).isoformat()+' '+name+' '+detail+'\n')
    print(name,flush=True)

def queue():
    code="import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'mode':d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],'active':d.execute(\"SELECT count(*) FROM ai_queue WHERE state!=\\'finished\\'\").fetchone()[0],'provider_receipts':d.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0]}))"
    return json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',code))

def sql(query):
    return docker('exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-XAtc','BEGIN READ ONLY; '+query+'; COMMIT;').decode().strip()

def n8n_read(query,container='qldapm-n8n-main'):
    code="const {DatabaseSync}=require('node:sqlite');const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});let q=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(d.prepare(q).all()));d.close()"
    return json.loads(docker('exec','-i',container,'node','-e',code,data=json.dumps(query).encode()))

def health(name,timeout=180):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        row=inspect(name)
        if row['State']['Status']=='running' and row['State'].get('Health',{}).get('Status','healthy')=='healthy':return row
        time.sleep(1)
    raise RuntimeError('HEALTH_TIMEOUT_'+name)
