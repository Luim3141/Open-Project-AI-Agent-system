"""Final non-inference controls, preservation and deployed-source qualification."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

from automation.engineering_worker import operator,command,python,wsl,save,ROOT,DEMO


def collect():
    before=operator('status')
    if before['mode']!='OFF' or len(before['runs'])!=2 or any(r['queue_state']!='finished' or r['result']['status']!='succeeded' for r in before['runs']):
        raise ValueError('EXPECTED_COMPLETED_DEMO_REQUIRED')
    count=sum(r['usage']['requests_recorded'] for r in before['runs'])
    source=operator('source');duplicates=[]
    for run in before['runs']:
        response=operator('admit',arguments={'native_id':379,'lock_version':source['lock_version'],'unit':run['unit']},key='final-dedup-'+run['unit'])
        if response['id']!=run['id'] or not response['deduplicated']:raise ValueError('DUPLICATE_RUN')
        duplicates.append(response)
    operator('control',mode='PAUSED')
    if operator('claim') is not None or operator('status')['mode']!='PAUSED':raise ValueError('PAUSE_FAILED')
    operator('control',mode='OFF')
    time.sleep(12) # Allow several real delivery polls; never request inference.
    after=operator('status')
    if after['mode']!='OFF' or sum(r['usage']['requests_recorded'] for r in after['runs'])!=count:raise ValueError('IDLE_CHANGED')
    gate=json.loads(python('from pathlib import Path\nc=json.loads(Path("/root/.qldapm-openclaw/active.json").read_text());print(json.dumps({"active":c["active"],"remaining":c["remaining"]}))',root=True).stdout)
    if gate['active']:raise ValueError('PROVIDER_GATE_NOT_OFF')
    installed_gate=python('from pathlib import Path\nimport hashlib\nprint(json.dumps(hashlib.sha256(Path("/root/.qldapm-openclaw/provider_gate.py").read_bytes()).hexdigest()))',root=True).stdout
    if json.loads(installed_gate)!=hashlib.sha256((ROOT/'openproject/ai/automation/openclaw_provider_gate.py').read_bytes()).hexdigest():raise ValueError('PROVIDER_GATE_SOURCE_DRIFT')
    gateway_files=['engineering.py','engineering_units.py','engineering_operator.py','agent_registry.py','native.py','store.py','service.py','permissions.py','catalog.py','bridge.py','app.py','openproject_loader.py']
    code='import json,hashlib;from pathlib import Path;print(json.dumps({name:hashlib.sha256((Path("/app/gateway")/name).read_bytes()).hexdigest() for name in '+repr(gateway_files)+'}))'
    deployed=json.loads(command(['docker','exec','qldapm-ai-gateway-1','python','-c',code]).stdout)
    expected={name:hashlib.sha256((ROOT/'openproject/ai/gateway'/name).read_bytes()).hexdigest() for name in gateway_files}
    if deployed!=expected:raise ValueError('GATEWAY_SOURCE_DRIFT')
    core_files=['app/controllers/qldapm_ai_controller.rb','app/views/qldapm_ai/engineering.html.erb']
    ruby="require 'json';require 'digest';puts JSON.generate("+json.dumps(core_files)+".to_h{|name|[name,Digest::SHA256.file('/app/'+name).hexdigest]})"
    core=json.loads(command(['docker','exec','qldapm-openproject-web-1','ruby','-e',ruby]).stdout)
    if core!={name:hashlib.sha256((ROOT/'openproject/ai/core/overlay'/name).read_bytes()).hexdigest() for name in core_files}:
        raise ValueError('CORE_SOURCE_DRIFT')
    deployment=json.loads((ROOT/'docs/ai/engineering/deployment.json').read_text())
    baseline=json.loads((Path(deployment['backup'])/'gateway-config.json').read_text())
    old_hash=hashlib.sha256(json.dumps({k:v for k,v in baseline.items() if k!='engineering'},sort_keys=True).encode()).hexdigest()
    code="import json,hashlib;from pathlib import Path;c=json.loads(Path('/state/config.json').read_text());print(json.dumps({'digest':hashlib.sha256(json.dumps({k:v for k,v in c.items() if k!='engineering'},sort_keys=True).encode()).hexdigest(),'project':c['project_id'],'actor20role':c['users']['20']}))"
    config=json.loads(command(['docker','exec','qldapm-ai-gateway-1','python','-c',code]).stdout)
    if config['digest']!=old_hash or config['project']!=5 or config['actor20role']!='BA':raise ValueError('MAIN_CONFIG_CHANGED')
    native_code="import json;from pathlib import Path;from gateway.store import Store;from gateway.service import Service;r=Path('/state');s=Service(Store(r),json.loads((r/'config.json').read_text()),'/workspaces');_,who=s.native_actor(20);print(json.dumps({'role':who['role'],'project_id':who['project_id']}))"
    main_identity=json.loads(command(['docker','exec','qldapm-ai-gateway-1','python','-c',native_code]).stdout)
    if main_identity!={'role':'BA','project_id':5}:raise ValueError('MAIN_NATIVE_ROLE_CHANGED')
    n8n=json.loads((ROOT/'docs/ai/engineering/n8n-preservation.json').read_text())
    if len(n8n['workflows'])!=16 or not all(w['active'] and w['activeVersionId'] for w in n8n['workflows']):raise ValueError('N8N_PRESERVATION_FAILED')
    node="const {DatabaseSync}=require('node:sqlite');const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT count(*) AS total,sum(active) AS active,sum(activeVersionId IS NOT NULL) AS published FROM workflow_entity').get()));d.close();"
    live_n8n=json.loads(command(['docker','exec','qldapm-n8n-main','node','-e',node]).stdout)
    if live_n8n!={'total':16,'active':16,'published':16}:raise ValueError('N8N_CURRENT_STATE_CHANGED')
    release=json.loads((ROOT/'docs/ai/engineering/demo-service.json').read_text())
    with urllib.request.urlopen(release['url'],timeout=10) as response:
        if response.status!=200:raise ValueError('DEMO_HTTP_FAILED')
    head=command(['git','-c','core.hooksPath=NUL','-C',str(DEMO),'rev-parse','HEAD']).stdout.decode().strip()
    if head!=release['head_sha']:raise ValueError('WINDOWS_DEMO_HEAD_DRIFT')
    task=json.loads(command(['powershell.exe','-NoProfile','-NonInteractive','-Command',
        "Get-ScheduledTask -TaskName QLDAPMEngineeringDelivery | Select-Object TaskName,State | ConvertTo-Json -Compress"]).stdout)
    if task['State']!=4 and task['State']!='Running':raise ValueError('DELIVERY_TASK_NOT_RUNNING')
    import os
    log=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/engineering-delivery.log'
    if log.exists() and 'adapter_error' in log.read_text(encoding='utf-8-sig',errors='replace')[-4000:]:raise ValueError('DELIVERY_TASK_ERROR_LOG')
    evidence={'status':'PASS','controls':{'completed_unit_dedupe':duplicates,'pause_claim_blocked':True,'final_mode':'OFF'},
        'openclaw_model_requests_before':count,'openclaw_model_requests_after':count,'provider_gate':gate,
        'gateway_source_sha256':deployed,'core_source_sha256':core,'project5_config_unchanged_except_engineering_opt_in':True,
        'project5_actor20_role':config['actor20role'],'n8n_workflows_active_published':16,
        'project5_fresh_native_identity':main_identity,
        'demo_http':200,'windows_demo_head':head,'delivery_task':task,
        'windows_node':command(['node','--version']).stdout.decode().strip(),
        'manual_browser_uat':'NOT_RUN_USER_REQUESTED_SELF_TEST','real_windows_logon_reboot_test':'NOT_RUN',
        'framework_warning':'httpx/Starlette deprecation; tests pass; no dependency migration in this change'}
    save(ROOT/'docs/ai/engineering','FINAL_QUALIFICATION.json',evidence)
    print(json.dumps({k:v for k,v in evidence.items() if not k.endswith('sha256')},ensure_ascii=False))


if __name__=='__main__':collect()
