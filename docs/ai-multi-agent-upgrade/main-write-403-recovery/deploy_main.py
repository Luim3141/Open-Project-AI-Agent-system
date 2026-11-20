"""Owner-authorized Main Gateway/web apply and sole approved permission grant; never creates a WP."""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from inspect_runtime import ROOT,OUT,run
from qualify import inspect
from jira_sync_backup import database_state

def update_image(path,key,value):
    lines=path.read_text(encoding='utf-8-sig').splitlines();assert sum(s.startswith(key+'=') for s in lines)==1
    path.write_text('\n'.join(key+'='+value if s.startswith(key+'=') else s for s in lines)+'\n',encoding='utf-8')

def main():
    output=OUT/'deployment.json';assert not output.exists(),'DEPLOYMENT_EXISTS_RECONCILE_BEFORE_RETRY'
    q=json.loads((OUT/'qualification.json').read_text());backup=json.loads((OUT/'backup.json').read_text())
    release=json.loads((OUT/'release-preparation.json').read_text());before=json.loads((OUT/'runtime-before.json').read_text())
    assert json.loads((OUT/'clone-browser-results.json').read_text())['passed'] and backup['passed']
    approval=json.loads((OUT/'owner-approval.json').read_text(encoding='utf-8-sig'))
    assert hashlib.sha256((OUT/'ROOT_CAUSE.md').read_bytes()).hexdigest()==approval['preview_sha256']
    assert approval['no_main_subtask_creation'] and approval['approved_scope']['permission_added']=='manage_subtasks'
    for rel,expected in q['source'].items():
        assert hashlib.sha256((ROOT/'openproject/ai'/rel).read_bytes()).hexdigest()==expected,'CANDIDATE_SOURCE_DRIFT'
    for filename,digest in backup['hashes'].items():
        assert hashlib.sha256((Path(backup['directory'])/filename).read_bytes()).hexdigest()==digest,'BACKUP_DRIFT'
    assert inspect('qldapm-ai-gateway-1')['Image']==release['rollback_gateway']
    assert inspect('qldapm-openproject-web-1')['Image']==before['containers']['qldapm-openproject-web-1']['Image']
    idle="import sqlite3;s=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);assert s.execute(\"select count(*) from ai_runs where state in ('running','queued')\").fetchone()[0]==0;print('IDLE')"
    assert run('docker','exec','qldapm-ai-gateway-1','python','-c',idle).strip()=='IDLE'
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM';ai=runtime/'openproject-ai';native=runtime/'openproject'
    private=Path(q['private']);archive=private/'deployment-config';archive.mkdir(exist_ok=True)
    for path,name in ((ai/'.env','ai.env'),(native/'.env','core.env'),(ai/'image-lock.json','image-lock.json')):
        if (archive/name).exists():assert (archive/name).read_bytes()==path.read_bytes(),'PRE_APPLY_CONFIG_DRIFT'
        else:shutil.copy2(path,archive/name)
    protected=[ai/'gateway'/name for name in ('config.json','credentials.json','ui.key','gemini.key','gemini.json')]
    protected += [ai/'operator/gemini-main/free-tier-proof.json',ai/'stage-image-lock.json']
    file_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
    # Snapshot before app restart and RBAC change, excluding the owned qualification resources.
    untouched={n:c for n,c in before['containers'].items() if n not in ('qldapm-ai-gateway-1','qldapm-openproject-web-1') and not n.startswith('qldapm-rd-')}
    db_before=database_state('qldapm-openproject-db-1')
    assert db_before['work_packages']==before['database']['work_packages']
    count=run('docker','exec','qldapm-openproject-db-1','psql','-X','-U','postgres','-d','openproject','-qAtc','SELECT count(*) FROM work_packages WHERE project_id=5').strip()
    assert count=='329','MAIN_PROJECT_COUNT_CHANGED'
    result={'phase':'PREPARED','core_image':q['core_image'],'gateway_image':q['gateway_image'],'backup':backup['directory'],
            'rollback_core':release['rollback_core'],'rollback_gateway':release['rollback_gateway'],
            'google_calls_requested':0,'main_wp_writes_requested':0,'approved_permission':'role22/manage_subtasks'}
    def save(phase):result['phase']=phase;output.write_text(json.dumps(result,indent=2))
    save('PREPARED')
    update_image(ai/'.env','AI_IMAGE',q['gateway_image']);update_image(native/'.env','OP_IMAGE',q['core_image'])
    lock=json.loads((ai/'image-lock.json').read_text());lock.update(CORE_IMAGE=q['core_image'],AI_IMAGE=q['gateway_image'])
    (ai/'image-lock.json').write_text(json.dumps(lock,indent=2))
    gateway=['docker','compose','--project-name','qldapm-ai','--env-file',str(ai/'.env'),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml')]
    core=['docker','compose','--project-name','qldapm-openproject','--env-file',str(native/'.env'),'-f',str(ROOT/'openproject/compose.yml')]
    for name in ('active-volumes.yml','ui-bridge.yml'):
        if (native/name).exists():core+=['-f',str(native/name)]
    cfg=json.loads(run(*gateway,'config','--format','json'))['services']['gateway']
    assert cfg['image']==q['gateway_image'] and cfg['environment']['QLDAPM_AI_ENVIRONMENT']=='production'
    assert 'QLDAPM_OFFLINE_WRITE_UAT' not in cfg.get('environment',{})
    assert not any(m['target']=='/qualification' for m in cfg['volumes'])
    assert all(p.get('host_ip')=='127.0.0.1' for p in cfg['ports'])
    assert json.loads(run(*core,'config','--format','json'))['services']['web']['image']==q['core_image']
    save('CONFIG_VALIDATED')
    for command,log in ((gateway+['up','-d','--no-deps','gateway'],'gateway-apply.log'),(core+['up','-d','--no-deps','web'],'core-apply.log')):
        with (OUT/log).open('wb') as stream:
            p=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
        assert p.returncode==0,'APPLY_FAILED_RECONCILE:'+log
        save('APPLIED_'+log)
    for _ in range(90):
        states={n:inspect(n)['State'] for n in ('qldapm-ai-gateway-1','qldapm-openproject-web-1')}
        if all(s.get('Health',{}).get('Status')=='healthy' for s in states.values()):break
        assert all(s['Running'] for s in states.values()),'MAIN_CONTAINER_STOPPED'
        time.sleep(2)
    else:raise AssertionError('MAIN_HEALTH_TIMEOUT_RECONCILE')
    save('APPLICATION_HEALTH_PASS')
    code='''require 'json'
raise 'WRONG_MAIN_HOST' unless ENV['OPENPROJECT_HOST__NAME']=='localhost:8088'
r=Role.find(22);raise 'WRONG_ROLE' unless r.name=='QLDAPM PM'
members=MemberRole.where(role_id:22).joins(:member).pluck('members.user_id','members.project_id')
raise 'MEMBERSHIP_DRIFT' unless members==[[19,5]]
before=r.permissions.map(&:to_s);raise 'ALREADY_GRANTED_RECONCILE' if before.include?('manage_subtasks')
r.with_lock { r.permissions=(before+['manage_subtasks']).map(&:to_sym);r.save! }
after=r.reload.permissions.map(&:to_s)
raise 'PERMISSION_DIFF_FAILED' unless after-before==['manage_subtasks'] && before-after==[]
puts JSON.generate({role_id:22,members:members,before:before,after:after,added:['manage_subtasks'],removed:[],passed:true})
'''
    p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-'],input=code.encode(),capture_output=True,timeout=120)
    assert p.returncode==0,'MAIN_PERMISSION_APPLY_FAILED_OUTPUT_WITHHELD_RECONCILE'
    lines=[s for s in p.stdout.decode().splitlines() if s.startswith('{')]
    permission=json.loads(lines[-1]);(private/'main-permission-receipt.json').write_text(json.dumps(permission,indent=2))
    result['permission']={k:permission[k] for k in ('role_id','members','added','removed','passed')};save('APPROVED_PERMISSION_APPLIED')
    after=database_state('qldapm-openproject-db-1')
    preserved=('work_packages','relations','sprints','versions','members','member_roles','users','two_factor_authentication_devices')
    assert all(after[t]==db_before[t] for t in preserved),'MAIN_PROTECTED_STATE_CHANGED'
    for name,c in untouched.items():
        actual=inspect(name)
        assert all(actual[k]==c[k] for k in ('Id','Image')) and actual['State']['StartedAt']==c['started'],'UNRELATED_RUNTIME_CHANGED:'+name
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in file_hashes.items()),'PROTECTED_CONFIG_CHANGED'
    result.update(passed=True,preserved_tables=list(preserved),untouched_containers=len(untouched),protected_files_unchanged=True,
                  main_work_packages=329,total_database_work_packages=after['work_packages']['rows'],staging_untouched=True)
    save('DEPLOYED_PERMISSION_AND_PROTECTED_STATE_PASS_BROWSER_PENDING')
    print(json.dumps(result))

if __name__=='__main__':main()
