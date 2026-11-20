"""Guarded Telegram-only patch release; exact existing Compose config, no DB restore."""
import hashlib,json,os,subprocess,time,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
NAME='qldapm-ai-telegram-ai-1';BASE=json.loads((OUT/'baseline.json').read_text())['containers'][NAME]['image']
def cmd(args,**kwargs):return subprocess.check_output(args,text=True,**kwargs).strip()
def inspect(name):return json.loads(cmd(['docker','inspect',name]))[0]
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def semantic(d):return {'env_sha256':hashlib.sha256(json.dumps(sorted(d['Config']['Env'])).encode()).hexdigest(),'mounts':sorted([m['Source'],m['Destination'],m['RW']] for m in d['Mounts']),'networks':sorted(d['NetworkSettings']['Networks']),'restart':d['HostConfig']['RestartPolicy']}
action=sys.argv[1];work=PRIVATE/'operator/functional-telegram-acceptance-20261112';work.mkdir(exist_ok=True,parents=True)
proof=OUT/'bot-candidate.json'
if action=='build':
    before=inspect(NAME);known=json.loads(proof.read_text())['image'] if proof.exists() else BASE
    assert before['Image'] in {BASE,known};BASE=before['Image']
    sources=['engine.py','tools.py','system_instructions.py']
    for name in sources:(work/name).write_bytes((ROOT/'openproject/ai/telegram-ai/app'/name).read_bytes())
    tag='qldapm-functional-telegram-base:'+BASE.split(':')[1][:12];subprocess.run(['docker','tag',BASE,tag],check=True)
    (work/'Dockerfile').write_text('FROM '+tag+'\n'+''.join(f'COPY {name} /app/app/{name}\n' for name in sources))
    image=cmd(['docker','build','--network','none','--pull=false','-q',str(work)])
    assert image.startswith('sha256:')
    tests=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=64m,mode=1777','--mount',f'type=bind,source={ROOT / "openproject/ai/telegram-ai/tests"},target=/qa,readonly','--entrypoint','python',image,'-m','unittest','discover','-s','/qa']
    p=subprocess.run(tests,capture_output=True,text=True);(OUT/'bot-candidate-tests.log').write_text(p.stdout+p.stderr);assert p.returncode==0
    sha=hashlib.sha256((work/'engine.py').read_bytes()).hexdigest()
    actual=cmd(['docker','run','--rm','--network','none','--entrypoint','python',image,'-c',"import hashlib;print(hashlib.sha256(open('/app/app/engine.py','rb').read()).hexdigest())"]);assert actual==sha
    hashes={name:hashlib.sha256((work/name).read_bytes()).hexdigest() for name in sources}
    save(proof.name,{'image':image,'base':BASE,'engine_sha256':sha,'sources':hashes,'tests_pass':True,'before_semantic':semantic(before),'before_id':before['Id'],'scope':'Telegram acceptance wording guard, typed checkpoint counts, resolved model receipt; no dependency/config changes'})
    print(json.dumps({'image':image,'tests':'PASS','source_parity':True}))
elif action=='rollout':
    idle=json.loads(cmd(['docker','exec','qldapm-ai-gateway-1','python','-c',"import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps([d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],d.execute(\"SELECT count(*) FROM ai_queue WHERE state!='finished'\").fetchone()[0]]))"]))
    assert idle==['OFF',0],'IDLE_OFF_REQUIRED'
    p=json.loads(proof.read_text());before=inspect(NAME);assert before['Image']==p['base'] and semantic(before)==p['before_semantic']
    assert hashlib.sha256((ROOT/'openproject/ai/telegram-ai/app/engine.py').read_bytes()).hexdigest()==p['engine_sha256']
    for name,sha in p['sources'].items():assert hashlib.sha256((ROOT/'openproject/ai/telegram-ai/app'/name).read_bytes()).hexdigest()==sha
    labels=before['Config']['Labels'];files=labels['com.docker.compose.project.config_files'].split(',')
    compose=['docker','compose','-p',labels['com.docker.compose.project'],'--env-file',str(PRIVATE/'.env')]
    for file in files:assert Path(file).is_file();compose+=['-f',file]
    override=work/'telegram-patch.json';override.write_text(json.dumps({'services':{'telegram-ai':{'image':p['image']}}}))
    candidate=compose+['-f',str(override)]
    old=json.loads(cmd(compose+['config','--format','json']));new=json.loads(cmd(candidate+['config','--format','json']))
    old['services']['telegram-ai']['image']=p['image'];assert old==new,'COMPOSE_CHANGE_BEYOND_BOT_IMAGE'
    gateway_before=inspect('qldapm-ai-gateway-1')['Id'];core_before=inspect('qldapm-openproject-web-1')['Id'];n8n_before=inspect('qldapm-n8n-main')['Id']
    try:
        subprocess.run(candidate+['up','-d','--no-deps','--no-build','--pull','never','telegram-ai'],check=True,capture_output=True)
        for _ in range(30):
            after=inspect(NAME)
            if after['State'].get('Health',{}).get('Status')=='healthy':break
            time.sleep(2)
        assert after['State'].get('Health',{}).get('Status')=='healthy'
        assert after['Image']==p['image'] and semantic(after)==p['before_semantic']
        assert inspect('qldapm-ai-gateway-1')['Id']==gateway_before and inspect('qldapm-openproject-web-1')['Id']==core_before and inspect('qldapm-n8n-main')['Id']==n8n_before
        actual=cmd(['docker','exec',NAME,'python','-c',"import hashlib;print(hashlib.sha256(open('/app/app/engine.py','rb').read()).hexdigest())"]);assert actual==p['engine_sha256']
        for name,sha in p['sources'].items():assert cmd(['docker','exec',NAME,'python','-c',f"import hashlib;print(hashlib.sha256(open('/app/app/{name}','rb').read()).hexdigest())"])==sha
        save('bot-deployment.json',{'at':time.time(),'state':'DEPLOYED_HEALTHY_PARITY','image':p['image'],'rollback_image':p['base'],'container_id':after['Id'],'same_env_mounts_networks_restart':True,'unrelated_containers_unchanged':True,'engine_sha256':actual,'database_restore':False})
        print(json.dumps({'state':'DEPLOYED_HEALTHY_PARITY','image':p['image']}))
    except Exception:
        override.write_text(json.dumps({'services':{'telegram-ai':{'image':p['base']}}}))
        subprocess.run(candidate+['up','-d','--no-deps','--no-build','--pull','never','telegram-ai'],check=True,capture_output=True)
        save('bot-deployment-failure.json',{'state':'ROLLED_BACK','image':inspect(NAME)['Image'],'database_restore':False});raise
else:raise ValueError(action)
