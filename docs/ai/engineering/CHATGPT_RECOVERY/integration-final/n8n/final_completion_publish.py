"""Publish exactly five clone-qualified graph deltas after root's paired runtime deployment."""
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.n8n_integration_adapter import attach

OUT=Path(__file__).parent
TARGETS={'WF01','WF03','WF08','WF09','WF10'}
SOURCE_NAMES=['service.py','integration_events.py','workflow_commands.py','bug_lifecycle.py','native_wbs.py']
READ="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT w.id,w.name,w.active,w.activeVersionId,h.nodes,h.connections,w.settings FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId ORDER BY w.name').all()));d.close()"
STATE="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true}),h=t=>require('crypto').createHash('sha256').update(JSON.stringify(d.prepare('select * from \"'+t+'\" order by id').all())).digest('hex');console.log(JSON.stringify({credentials:h('credentials_entity'),users:h('user'),executions:d.prepare('select count(*) n from execution_entity').get().n,unfinished:d.prepare(\"select count(*) n from execution_entity where status in ('new','running','waiting')\").get().n}));d.close()"


def main(*,output=OUT,proof_file=None,targets=TARGETS,source_names=SOURCE_NAMES,
         case_names=frozenset({'FINAL_P6_BUSINESS','FINAL_PLANNING_OBSERVERS'}),output_prefix='final-completion'):
    OUT=output;TARGETS=targets;SOURCE_NAMES=source_names
    assert len(sys.argv)==3,'REQUIRED_EXACT_DEPLOYED_GATEWAY_AND_CORE_IMAGE_IDS'
    expected_gateway,expected_core=sys.argv[1:]
    proof=json.loads((proof_file or OUT/'final-completion-clone-result.json').read_text())
    assert proof['status']=='PASS' and proof['passed']==proof['total']==len(case_names),'CHANGED_GRAPH_CLONE_QUALIFICATION_REQUIRED'
    assert {r['workflow'] for r in proof['checks'] if r['status']=='BUSINESS_PASS_IN_CLONE'}==set(case_names)
    assert proof['adapter_sha256']==hashlib.sha256((ROOT/'openproject/ai/automation/n8n_integration_adapter.py').read_bytes()).hexdigest(),'QUALIFIED_ADAPTER_CHANGED'
    for name in SOURCE_NAMES:
        assert proof['gateway_sources'][name]==hashlib.sha256((ROOT/'openproject/ai/gateway'/name).read_bytes()).hexdigest(),'QUALIFIED_SOURCE_CHANGED: '+name
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/(output_prefix+'-publish-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
    private.mkdir(exist_ok=False)
    def docker(*args,data=None,timeout=240):
        p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
        if p.returncode:
            (private/'failure.log').write_bytes(p.stdout+p.stderr)
            raise RuntimeError('PUBLISH_COMMAND_FAILED_PRIVATE_LOG: '+args[0])
        return p.stdout
    def image(container):return json.loads(docker('inspect',container))[0]['Image']
    assert image('qldapm-ai-gateway-1')==expected_gateway and image('qldapm-openproject-web-1')==expected_core,'EXACT_ROOT_DEPLOYED_PAIR_REQUIRED'
    runtime=json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',
        "import hashlib,json;from pathlib import Path;names="+repr(SOURCE_NAMES)+";print(json.dumps({n:hashlib.sha256((Path('/app/gateway')/n).read_bytes()).hexdigest() for n in names}))"))
    assert runtime=={name:proof['gateway_sources'][name] for name in SOURCE_NAMES},'DEPLOYED_SOURCE_DIFFERS_FROM_CLONE'
    idle="import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'mode':d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],'active':d.execute(\"SELECT count(*) FROM ai_queue WHERE state IN ('queued','executing')\").fetchone()[0]}))"
    assert json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',idle))=={'mode':'OFF','active':0},'ENGINEERING_OFF_IDLE_REQUIRED'
    before=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ))
    state=json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE))
    assert len(before)==16 and all(r['active'] for r in before) and state['unfinished']==0
    fingerprint=hashlib.sha256(json.dumps([{k:r[k] for k in ['id','name','nodes','connections','settings']} for r in before],sort_keys=True).encode()).hexdigest()
    assert fingerprint==proof['published_source_sha256'],'PUBLISHED_SOURCE_CHANGED_SINCE_CLONE'
    original=[{'id':r['id'],'name':r['name'],'nodes':json.loads(r['nodes']),'connections':json.loads(r['connections']),'settings':json.loads(r['settings'])} for r in before if r['name'][:4] in TARGETS]
    assert len(original)==len(TARGETS)
    candidate=[attach(s) for s in original]
    assert all(a!=b for a,b in zip(original,candidate)),'EXACT_TARGET_GRAPH_DELTAS_EXPECTED'
    old=json.loads(docker('inspect','qldapm-n8n-main'))[0];n8n_image=old['Image']
    assert n8n_image==proof['n8n_image'],'N8N_RUNTIME_CHANGED_SINCE_CLONE'
    (private/'old.json').write_text(json.dumps(original),encoding='utf8')
    (private/'candidate.json').write_text(json.dumps(candidate),encoding='utf8')
    env=old['Config']['Env'];assert all('\r' not in e and '\n' not in e for e in env)
    (private/'preserved.env').write_text('\n'.join(env)+'\n',encoding='utf8')
    def cli(filename):
        base=['run','--rm','--network','none','--env-file',str(private/'preserved.env'),
            '--volume','qldapm-n8n-main-data:/home/node/.n8n','--mount',f'type=bind,source={private},target=/fixture,readonly','--entrypoint','n8n',n8n_image]
        docker(*base,'import:workflow','--input=/fixture/'+filename)
        for spec in original:docker(*base,'publish:workflow','--id='+spec['id'])
    def ready():
        for _ in range(90):
            try:
                if urllib.request.urlopen('http://127.0.0.1:5679/healthz/readiness',timeout=2).status==200:return
            except Exception:time.sleep(1)
        raise RuntimeError('N8N_READINESS_TIMEOUT')
    stopped=False;attempted=False
    try:
        assert json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE))['unfinished']==0
        docker('stop','--time','45','qldapm-n8n-main');stopped=True
        frozen=json.loads(docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/home/node/.n8n,readonly','--entrypoint','node',n8n_image,'-e',STATE))
        assert frozen['unfinished']==0
        backup=docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/data,readonly','--entrypoint','tar',n8n_image,'-C','/data','-cf','-','.')
        (private/'cold-volume.tar').write_bytes(backup)
        attempted=True;cli('candidate.json');docker('start','qldapm-n8n-main');stopped=False;ready()
        after=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ));newstate=json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE))
        assert len(after)==16 and all(r['active'] for r in after)
        for a,b in zip(before,after):
            assert a['id']==b['id']
            if a['name'][:4] not in TARGETS:assert a==b,'UNRELATED_WORKFLOW_CHANGED'
            else:
                expected=next(s for s in candidate if s['id']==b['id'])
                assert json.loads(b['nodes'])==expected['nodes'] and json.loads(b['connections'])==expected['connections']
                assert json.loads(a['settings'])==json.loads(b['settings']),'SCHEDULE_OR_SETTINGS_CHANGED'
        assert state['credentials']==newstate['credentials'] and state['users']==newstate['users'] and newstate['executions']>=state['executions']
        assert json.loads(docker('inspect','qldapm-n8n-main'))[0]['Id']==old['Id']
        safe=[{k:r[k] for k in ['id','name','active','activeVersionId']}|{'nodes_sha256':hashlib.sha256(r['nodes'].encode()).hexdigest(),'connections_sha256':hashlib.sha256(r['connections'].encode()).hexdigest(),'settings_sha256':hashlib.sha256(r['settings'].encode()).hexdigest()} for r in after]
        (OUT/(output_prefix+'-published-after.json')).write_text(json.dumps(safe,indent=2)+'\n',encoding='utf8')
        result={'status':'GRAPHS_PUBLISHED_PENDING_MAIN_BUSINESS_READBACK','gateway_image':expected_gateway,'core_image':expected_core,
            'n8n_image':n8n_image,'changed_workflows':sorted(TARGETS),'unchanged_other_workflows':16-len(TARGETS),'credentials_users_preserved':True,
            'execution_count_before':state['executions'],'execution_count_after':newstate['executions'],'container_preserved':True,
            'cron_settings_preserved':True,'private_backup':str(private),'cold_backup_sha256':hashlib.sha256(backup).hexdigest(),
            'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        (OUT/(output_prefix+'-publish-result.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
    except BaseException:
        if attempted:
            if not stopped:docker('stop','--time','45','qldapm-n8n-main');stopped=True
            cli('old.json')
        if stopped:docker('start','qldapm-n8n-main');ready()
        (OUT/'final-completion-publish-error.json').write_text(json.dumps({'state':'RESTORED_FIVE_PREVIOUS_GRAPHS' if attempted else 'ABORTED_BEFORE_IMPORT','private_backup':str(private)}),encoding='utf8')
        raise


if __name__=='__main__':main()
