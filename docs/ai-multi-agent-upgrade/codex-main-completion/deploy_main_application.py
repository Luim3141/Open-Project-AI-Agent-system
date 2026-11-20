"""Owner-authorized app/config-only apply. No migrations, business writes or provider calls."""
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

OUT=Path(__file__).parent
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from free_tier_staging import private_directory,save
from gateway.gemini import Gemini
from gateway.native import Native
from jira_sync_backup import command,inspect,verify_archive,database_state
from rehearse_rollback import verify_image_source

OLD='sha256:bfda82ceec573e5104a797b517e497ec6d6b68a25e3f29a322c3879e1320754c'
CORE='sha256:dde3c32ee69af450a6316450ac076d502953610932627ee33ce948f20dfbe459'
GATEWAY='sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b'

def main():
    result_path=OUT/'main-application-deployment.json'
    assert not result_path.exists(),'DEPLOYMENT_EXISTS_RECONCILE_BEFORE_RETRY'
    for name in ('fresh-backup-restore.json','rollback-rehearsal.json','clone-monitor-results.json','clone-browser-ba-be-fe-qa-results.json'):
        assert json.loads((OUT/name).read_text())['passed'],f'QUALIFICATION_NOT_PASSED:{name}'
    assert verify_image_source(CORE)==47
    backup=json.loads((OUT/'backup-receipt.json').read_text());verify_archive(backup['directory'],backup['hashes'])
    assert json.loads((OUT/'fresh-backup-restore.json').read_text())['backup_directory']==backup['directory']
    assert inspect('qldapm-openproject-web-1')['Image']==OLD and inspect('qldapm-ai-gateway-1')['Image']==GATEWAY
    assert inspect('qldapm-openproject-web-1')['Config']['Labels']['com.docker.compose.project']=='qldapm-openproject'
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
    ai=runtime/'openproject-ai';native=runtime/'openproject';state=ai/'gateway'
    private=ai/'operator/codex-main-completion/deployment-20261021'
    assert not private.exists(),'PRIVATE_DEPLOYMENT_EXISTS_RECONCILE'
    private_directory(private)
    config=json.loads((state/'config.json').read_text())
    assert config['project_id']==5 and config['users']=={'19':'PM','20':'BA','21':'BE','22':'FE','23':'QA'}
    assert not config.get('gateway_mode') or config['gateway_mode']=='strict'
    credentials=json.loads((state/'credentials.json').read_text())
    assert set(credentials)=={'19','20','21','22','23'}
    for name in ('gemini.key','gemini.json'):
        assert not (state/name).exists(),'PROVIDER_ALREADY_CONFIGURED_RECONCILE'
    protected=[state/'credentials.json',state/'ui.key',ai/'stage-ai/ui.key',ai/'stage-ai/gemini.key',ai/'stage-ai/gemini.json',ai/'operator/gemini-free/free-tier-proof.json']
    protected_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    before_containers={c:inspect(c) for c in ['qldapm-openproject-web-1','qldapm-openproject-worker-1','qldapm-openproject-cron-1','qldapm-ai-gateway-1']}
    all_names=command(['docker','ps','--format','{{.Names}}']).decode().splitlines()
    untouched={c:{k:inspect(c)[k] for k in ('Id','Image')} for c in all_names if c not in before_containers and not c.startswith('qldapm-codex-main-')}
    before_db=database_state('qldapm-openproject-db-1')
    archived={native/'.env':'core.env',state/'config.json':'gateway-config.json',ai/'image-lock.json':'image-lock.json'}
    for path,name in archived.items():shutil.copy2(path,private/name)
    core_args=['docker','compose','--project-name','qldapm-openproject','--env-file',str(native/'.env'),'-f',str(REPO/'openproject/compose.yml')]
    for name in ('active-volumes.yml','ui-bridge.yml'):
        if (native/name).is_file():core_args+=['-f',str(native/name)]
    ai_args=['docker','compose','--project-name','qldapm-ai','--env-file',str(ai/'.env'),'-f',str(REPO/'openproject/ai/compose.yml'),'-f',str(REPO/'openproject/ai/gemini-free.main.yml')]
    result={'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'phase':'PREPARED','private_directory':str(private),'backup':backup['directory'],'provider_calls_requested':0,'native_business_writes_requested':0}
    def checkpoint(phase):
        result['phase']=phase;result_path.write_text(json.dumps(result,indent=2))
    checkpoint('PREPARED')
    candidate=Path(json.loads((OUT/'provider-candidate.json').read_text())['private_directory'])
    provider=ai/'operator/gemini-main'
    assert not provider.exists(),'MAIN_PROVIDER_POLICY_EXISTS'
    private_directory(provider)
    for name in ('gemini.key','gemini.json'):shutil.copy2(candidate/name,state/name)
    shutil.copy2(candidate/'free-tier-proof.json',provider/'free-tier-proof.json')
    os.environ['QLDAPM_AI_ENVIRONMENT']='production';os.environ['QLDAPM_GEMINI_FREE_PROOF']=str(provider/'free-tier-proof.json')
    policy=Gemini(state).settings(require_enabled=False)
    assert policy['model']=='gemini-3.5-flash-lite' and policy['billing_enabled'] is False
    save(state/'config.json',json.dumps({**config,'gateway_mode':'native'},sort_keys=True))
    lines=(native/'.env').read_text().splitlines();assert sum(line.startswith('OP_IMAGE=') for line in lines)==1
    save(native/'.env','\n'.join('OP_IMAGE='+CORE if line.startswith('OP_IMAGE=') else line for line in lines)+'\n')
    lock=json.loads((ai/'image-lock.json').read_text());lock.update(CORE_IMAGE=CORE,AI_IMAGE=GATEWAY)
    save(ai/'image-lock.json',json.dumps(lock,indent=2))
    core_doc=json.loads(command(core_args+['config','--format','json']))
    ai_doc=json.loads(command(ai_args+['config','--format','json']))
    assert all(core_doc['services'][name]['image']==CORE for name in ('web','worker','cron'))
    gateway=ai_doc['services']['gateway']
    assert gateway['image']==GATEWAY and gateway['environment']['QLDAPM_AI_ENVIRONMENT']=='production'
    assert any(v['target']=='/qldapm-policy/free-tier-proof.json' and v['read_only'] for v in gateway['volumes'])
    assert all(p.get('host_ip')=='127.0.0.1' for p in gateway['ports'])
    checkpoint('CONFIG_VALIDATED_NO_RESTART_YET')
    try:
        command(ai_args+['up','-d','--no-deps','gateway'],timeout=180)
        checkpoint('GATEWAY_APPLIED')
        command(core_args+['up','-d','--no-deps','web','worker','cron'],timeout=180)
        checkpoint('CORE_APPLIED_WAITING_HEALTH')
        for _ in range(90):
            web=inspect('qldapm-openproject-web-1');gw=inspect('qldapm-ai-gateway-1')
            if web['State'].get('Health',{}).get('Status')=='healthy' and gw['State'].get('Health',{}).get('Status')=='healthy':break
            time.sleep(2)
        else:raise RuntimeError('MAIN_HEALTH_TIMEOUT')
        assert inspect('qldapm-openproject-web-1')['Image']==CORE and inspect('qldapm-ai-gateway-1')['Image']==GATEWAY
        identities=[]
        for actor,role in [(19,'PM'),(20,'BA'),(21,'BE'),(22,'FE'),(23,'QA')]:
            who=Native('http://127.0.0.1:8088',credentials[str(actor)],5).identity(actor)
            assert who['role']==role
            identities.append({k:who[k] for k in ('user_id','role','project_id')})
        after_db=database_state('qldapm-openproject-db-1')
        for table in ('work_packages','members','member_roles','roles','role_permissions','two_factor_authentication_devices','users'):
            assert after_db[table]==before_db[table],f'PROTECTED_NATIVE_TABLE_CHANGED:{table}'
        for name,previous in untouched.items():
            current=inspect(name);assert current['Id']==previous['Id'] and current['Image']==previous['Image'], 'UNRELATED_CONTAINER_CHANGED'
        assert all(hashlib.sha256(p.read_bytes()).hexdigest()==protected_hashes[str(p)] for p in protected),'PROTECTED_FILE_CHANGED'
        assert verify_image_source(CORE)==47
        result.update(passed=True,core_image=CORE,gateway_image=GATEWAY,native_identities=identities,protected_tables_unchanged=True,
                      protected_files_unchanged=True,unrelated_container_ids_images_preserved=len(untouched),gemini_live='NOT_RUN_AWAITING_SEPARATE_SMOKE_APPROVAL')
        checkpoint('HEALTH_AND_NATIVE_READBACK_PASS_BROWSER_UAT_PENDING')
        print(json.dumps(result,indent=2))
    except Exception as error:
        result.update(passed=False,error_type=type(error).__name__,reconcile_required=True)
        checkpoint('APPLY_OR_VERIFICATION_FAILED_DO_NOT_RETRY_BLINDLY')
        raise

if __name__=='__main__':main()
