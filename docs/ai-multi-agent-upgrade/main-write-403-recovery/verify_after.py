"""Final Main Native preflight/readback + image parity; never create a WP or call Gemini."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from inspect_runtime import ROOT,OUT,run
from qualify import inspect
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from jira_sync_backup import database_state

def main():
    before=json.loads((OUT/'runtime-before.json').read_text());q=json.loads((OUT/'qualification.json').read_text())
    state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway'
    credentials=json.loads((state/'credentials.json').read_text());config=json.loads((state/'config.json').read_text())
    identities=[]
    for actor,role in ((19,'PM'),(20,'BA'),(21,'BE'),(22,'FE'),(23,'QA')):
        n=Native('http://localhost:8088',credentials[str(actor)],5);who=n.identity(actor)
        assert who['role']==role;identities.append({k:who[k] for k in ('user_id','project_id','role')})
    n=Native('http://localhost:8088',credentials['19'],5)
    form=n.call('/api/v3/projects/5/work_packages/form','POST',{'subject':'test',config['source_field']:'write403-preflight-not-created',
        'description':{'format':'markdown','raw':''},'_links':{k:{'href':v} for k,v in {
        'project':'/api/v3/projects/5','type':'/api/v3/types/10','parent':'/api/v3/work_packages/50','assignee':'/api/v3/users/23'}.items()}})
    errors=form.get('_embedded',{}).get('validationErrors',{});assert not errors,'MAIN_NATIVE_FORM_STILL_REJECTED'
    rows=n.packages();assert len(rows)==329
    duplicate=[p['id'] for p in rows if p['subject'].casefold()=='test' and p.get('_links',{}).get('parent',{}).get('href')=='/api/v3/work_packages/50']
    assert duplicate==[],'UNAPPROVED_MAIN_CHILD_APPEARED'
    sprints=n.sprints();versions=n.collection('/api/v3/projects/5/versions');assert len(sprints)==len(versions)==7
    db=database_state('qldapm-openproject-db-1')
    tables=('work_packages','relations','sprints','versions','members','member_roles','users','two_factor_authentication_devices')
    assert all(db[t]==before['database'][t] for t in tables),'MAIN_PROTECTED_DATA_CHANGED'
    code="import hashlib,json,pathlib,sqlite3;s=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app/gateway').glob('*') if p.is_file()},'provider_receipts':s.execute('select count(*) from gemini_call_receipts').fetchone()[0],'usage':s.execute('select count(*) from gemini_usage').fetchone()[0],'sqlite':s.execute('pragma quick_check').fetchone()[0]}))"
    gateway=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',code))
    assert gateway['provider_receipts']==before['gateway']['provider_receipts'] and gateway['usage']==before['gateway']['usage']
    assert set(gateway['hashes'])==set(before['gateway']['hashes'])
    assert all(v==q['source']['gateway/'+name] for name,v in gateway['hashes'].items())
    paths=[k.removeprefix('core/overlay/') for k in q['source'] if k.startswith('core/overlay/')]
    ruby="require 'json';require 'digest';puts JSON.generate(JSON.parse(ARGV[0]).to_h{|p|[p,Digest::SHA256.file('/app/'+p).hexdigest]})"
    core=json.loads(run('docker','exec','qldapm-openproject-web-1','ruby','-e',ruby,json.dumps(paths)))
    assert all(v==q['source']['core/overlay/'+name] for name,v in core.items())
    stage=inspect('qldapm-ai-stage-staging-web-1')
    stage_runtime=json.loads(run('docker','exec','qldapm-ai-stage-staging-web-1','ruby','-e',ruby,json.dumps(paths)))
    stage_image=json.loads(run('docker','run','--rm','--network','none','--read-only','--entrypoint','ruby',stage['Image'],'-e',ruby,json.dumps(paths)))
    stage_drift={k:v for k,v in stage_runtime.items() if v!=stage_image[k]}
    known=json.loads((OUT/'stage-preexisting-code-drift.json').read_text())
    assert stage_drift=={k:v['runtime']['sha'] for k,v in known['drift'].items()}
    assert all(v['runtime']['mtime']<known['incident_start'] for v in known['drift'].values()),'NEW_STAGING_DRIFT'
    untouched=0
    for name,c in before['containers'].items():
        if name.startswith('qldapm-rd-') or name in ('qldapm-ai-gateway-1','qldapm-openproject-web-1'):continue
        actual=inspect(name);assert actual['Id']==c['Id'] and actual['Image']==c['Image'] and actual['State']['StartedAt']==c['started']
        untouched+=1
    result={'passed':True,'native_form_errors':errors,'native_create_preflight':'PASS_NO_CREATE',
        'identities':identities,'project_wp_count':len(rows),'database_wp_count':db['work_packages']['rows'],
        'sprints':len(sprints),'versions':len(versions),'existing_test_child_ids':duplicate,'preserved_tables':list(tables),
        'gateway_files_matched':len(gateway['hashes']),'core_files_matched':len(core),'stage_app_files_examined':len(stage_runtime),
        'stage_preexisting_drift':list(stage_drift),'stage_runtime_image_matches':len(stage_runtime)-len(stage_drift),
        'untouched_serving_containers':untouched,'provider_receipts':gateway['provider_receipts'],'usage':gateway['usage'],
        'google_calls':0,'main_business_mutations':0,'sqlite':gateway['sqlite']}
    (OUT/'final-runtime-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
