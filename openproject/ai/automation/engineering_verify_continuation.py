"""Bounded non-inference deployment/read-back checks; no UAT or full regression."""
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET

from automation.engineering_worker import ROOT,operator,command,python,wsl,save


def collect():
    root=ROOT/'docs/ai/engineering'
    state=operator('status')
    if state['mode']!='OFF' or any(r['queue_state']!='finished' for r in state['runs']):raise ValueError('IDLE_COMPLETED_RUNS_REQUIRED')
    selected=next(r for r in state['runs'] if (r['result'] or {}).get('status')=='succeeded' and (r['result'] or {}).get('head_sha'))
    run_id=selected['id'];head=selected['result']['head_sha'];plan_id=state['plans'][0]['id']
    count=sum(r['usage']['requests_recorded'] for r in state['runs'])
    code="import json;from pathlib import Path;from gateway.store import Store;from gateway.service import Service;p=Path('/state');base=Service(Store(p),json.loads((p/'config.json').read_text()),'/workspaces');s=__import__('gateway.engineering',fromlist=['scoped_service']).scoped_service(base,6);who=base.native_actor(20)[1];out={'project5_role':who['role'],'monitor':s.execute_actor(20,{'action':'get_execution_monitor','arguments':{'id':'"+run_id+"'}})['result'],'planning_monitor':s.execute_actor(20,{'action':'get_execution_monitor','arguments':{'id':'"+plan_id+"'}})['result']};print(json.dumps(out,ensure_ascii=False))"
    live=json.loads(command(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=90).stdout)
    assert live['project5_role']=='BA' and live['monitor']['state']=='COMPLETED'
    assert [n['agent'] for n in live['planning_monitor']['nodes']]==['supervisor','ba','pm','final']
    save(root,'continuation-monitor-live.json',live)
    files=['engineering.py','engineering_lifecycle.py','engineering_planning.py','engineering_personas.py','engineering_monitor.py','engineering_units.py','engineering_operator.py','store.py','service.py','agent_registry.py','permissions.py','catalog.py','engineering_state_sync.py','engineering_github_sync.py','engineering_auto.py']
    code="import hashlib,json;from pathlib import Path;print(json.dumps({n:hashlib.sha256((Path('/app/gateway')/n).read_bytes()).hexdigest() for n in "+repr(files)+"}))"
    serving=json.loads(command(['docker','exec','qldapm-ai-gateway-1','python','-c',code]).stdout)
    assert serving=={n:hashlib.sha256((ROOT/'openproject/ai/gateway'/n).read_bytes()).hexdigest() for n in files}
    core_files=['app/controllers/qldapm_ai_controller.rb','app/views/qldapm_ai/engineering.html.erb']
    ruby="require 'json';require 'digest';puts JSON.generate("+json.dumps(core_files)+".to_h{|n|[n,Digest::SHA256.file('/app/'+n).hexdigest]})"
    core=json.loads(command(['docker','exec','qldapm-openproject-web-1','ruby','-e',ruby]).stdout)
    assert core=={n:hashlib.sha256((ROOT/'openproject/ai/core/overlay'/n).read_bytes()).hexdigest() for n in core_files}
    folder=root/'runs'/run_id
    activations={role:json.loads((folder/(step+'-skill-activation.json')).read_text(encoding='utf-8')) for role,step in [('dev','dev-0'),('reviewer','review-0'),('qa','qa-0')]}
    for value in activations.values():assert {'AGENTS.md','SOUL.md'}<=set(value['persona_injected'])
    with urllib.request.urlopen('http://127.0.0.1:18791',timeout=10) as response:
        assert response.status==200 and response.headers['X-QLDAPM-Revision']==head
        html=response.read().decode()
    assert 'requestJson' in html and 'retry-btn' in html
    actual=wsl(['/usr/bin/cat','/home/openclaw/engineering/releases/'+head+'/task_manager/app.py']).stdout
    blob=wsl(['/usr/bin/git','-C','/home/openclaw/engineering/'+selected['unit'],'show',head+':task_manager/app.py']).stdout
    # Git archive used the repository's existing CRLF export conversion. Python
    # normalizes these line endings; compare all source text under that rule.
    assert actual.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
    node="const {DatabaseSync}=require('node:sqlite');const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT count(*) total,sum(active) active,sum(activeVersionId IS NOT NULL) published FROM workflow_entity').get()));d.close();"
    n8n=json.loads(command(['docker','exec','qldapm-n8n-main','node','-e',node]).stdout);assert n8n=={'total':16,'active':16,'published':16}
    gate=json.loads(python('from pathlib import Path\nc=json.loads(Path("/root/.qldapm-openclaw/active.json").read_text());print(json.dumps({"active":c["active"]}))',root=True).stdout);assert not gate['active']
    report=ET.parse(folder/'acceptance-0.xml').getroot().find('testsuite')
    assert int(report.attrib['tests'])>=19 and all(report.attrib[k]=='0' for k in ['failures','errors','skipped'])
    evidence={'status':'TARGETED_TECHNICAL_VERIFICATION_PASS','project5_role':'BA','gateway_source_sha256':serving,'core_source_sha256':core,
        'actual_persona_skills':activations,'n8n':n8n,'gate':gate,'app_head':head,'release_matches_git':'LF_NORMALIZED_SOURCE_MATCH',
        'release_file_sha256':hashlib.sha256(actual).hexdigest(),'git_blob_sha256':hashlib.sha256(blob).hexdigest(),
        'app_tests':int(report.attrib['tests']),'run_id':run_id,'plan_id':plan_id,'new_targeted_lifecycle_checks':13,'manual_uat':'DEFERRED_BY_USER','full_regression':'NOT_RERUN',
        'idle_requests_before':count,'worker_before':state['delivery_worker']}
    save(root,'CONTINUATION_VERIFICATION.json',evidence)
    print(json.dumps({'technical_verification':'PASS','monitor_roles':[n['agent'] for n in live['monitor']['nodes']],'requests_before_idle':count,'application_tests':int(report.attrib['tests']),'no_UAT':True}))


if __name__=='__main__':collect()
