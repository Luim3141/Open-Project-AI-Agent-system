"""Deploy qualified timeout/receipt fix only. Main Native data is never mutated here."""
import hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from free_tier_staging import private_directory
from jira_sync_backup import inspect,database_state
def run(*args):
    p=subprocess.run(args,capture_output=True,timeout=180);assert p.returncode==0,'RECOVERY_APPLY_FAILED_OUTPUT_WITHHELD'
    return p.stdout
def main():
    assert not (OUT/'deployment-recovery.json').exists(),'RECOVERY_DEPLOY_EXISTS_RECONCILE'
    q=json.loads((OUT/'qualification-recovery.json').read_text());initial=json.loads((OUT/'deployment.json').read_text())
    assert q['phase']=='RECOVERY_QUALIFIED_NO_NEW_CREATE' and json.loads((OUT/'native-source-proof.json').read_text())['matches_approval']
    assert json.loads((OUT/'native-duration-proof.json').read_text())['all_match']
    for rel,h in q['source'].items():assert hashlib.sha256((ROOT/'openproject/ai'/rel).read_bytes()).hexdigest()==h,'SOURCE_DRIFT'
    # The three owned qualification services are now idle; keep their data and containers.
    for name in ('qldapm-write403-20261021-browser','qldapm-write403-20261021-core','qldapm-write403-20261021-db'):
        c=inspect(name);assert c['Config']['Labels'].get('qldapm.qualification')=='main-write403-20261021'
        if c['State']['Running']:run('docker','stop','--time','20',name)
    ai=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai';state=ai/'gateway'
    directory=ai/'operator/main-live-write-final-acceptance'/datetime.now().strftime('post-create-pre-recovery-%Y%m%d-%H%M%S');private_directory(directory)
    assert not (state/'business-acceptance.json').exists(),'CONSENT_STILL_ARMED'
    assert inspect('qldapm-ai-gateway-1')['Image']==initial['gateway_image']
    names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
    containers={c['Name'].lstrip('/'):{'id':c['Id'],'image':c['Image'],'started':c['State']['StartedAt']} for c in json.loads(run('docker','inspect',*names))}
    before=database_state('qldapm-openproject-db-1');(directory/'database-state.json').write_text(json.dumps(before))
    with (directory/'database.dump').open('xb') as f:
        p=subprocess.run(['docker','exec','qldapm-openproject-db-1','pg_dump','-U','postgres','-Fc','openproject'],stdout=f,stderr=subprocess.PIPE,timeout=180)
    assert p.returncode==0,'PG_BACKUP_FAILED'
    code="""import sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert d.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0]==0
p=d.execute("select key from requests where state!='done'").fetchall();assert p==[('owner-create-e3626ae0-ce29-4e52-bcb8-98793eeefce5',)]
b=sqlite3.connect('/state/acceptance-recovery.sqlite');d.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok';b.close();d.close()"""
    run('docker','exec','qldapm-ai-gateway-1','python','-c',code)
    run('docker','cp','qldapm-ai-gateway-1:/state/acceptance-recovery.sqlite',str(directory/'gateway.sqlite'))
    for p in (ai/'.env',ai/'image-lock.json'):shutil.copy2(p,directory/p.name)
    protected=json.loads((OUT/'backup.json').read_text())['protected'];assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items())
    result={'phase':'BACKUP_VERIFIED','directory':str(directory),'gateway_image':q['gateway_image'],'core_image':initial['core_image'],
        'rollback_gateway':initial['gateway_image'],'google_calls':0,'native_mutations':0,
        'backup_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}}
    def save():(OUT/'deployment-recovery.json').write_text(json.dumps(result,indent=2))
    save()
    env=ai/'.env';env.write_text('\n'.join('AI_IMAGE='+q['gateway_image'] if l.startswith('AI_IMAGE=') else l for l in env.read_text(encoding='utf-8-sig').splitlines())+'\n',encoding='utf-8')
    lock=json.loads((ai/'image-lock.json').read_text());lock['AI_IMAGE']=q['gateway_image'];(ai/'image-lock.json').write_text(json.dumps(lock,indent=2))
    compose=['docker','compose','--project-name','qldapm-ai','--env-file',str(env),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml')]
    cfg=json.loads(run(*compose,'config','--format','json'))['services']['gateway'];assert cfg['image']==q['gateway_image']
    with (OUT/'recovery-apply.log').open('wb') as f:p=subprocess.run(compose+['up','-d','--no-deps','gateway'],stdout=f,stderr=subprocess.STDOUT,timeout=180)
    assert p.returncode==0,'RESTART_FAILED_RECONCILE'
    for _ in range(30):
        c=inspect('qldapm-ai-gateway-1');assert c['State']['Running']
        if c['State'].get('Health',{}).get('Status')=='healthy':break
        time.sleep(2)
    else:raise AssertionError('HEALTH_TIMEOUT')
    assert c['Image']==q['gateway_image']
    after=database_state('qldapm-openproject-db-1')
    protected_tables=('work_packages','relations','versions','sprints','users','roles','role_permissions','members','member_roles','tokens','two_factor_authentication_devices')
    assert all(before[t]==after[t] for t in protected_tables),'NATIVE_CHANGED_DURING_APP_APPLY'
    for n,b in containers.items():
        if n=='qldapm-ai-gateway-1':continue
        now=inspect(n);assert (now['Id'],now['Image'],now['State']['StartedAt'])==(b['id'],b['image'],b['started']),n
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items())
    current=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',"import hashlib,json;from pathlib import Path;print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/gateway').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))"))
    assert all(q['source'].get(p)==h for p,h in current.items())
    result.update(phase='RECOVERY_DEPLOYED_HEALTH_PARITY_PASS',packaged_files=len(current),unrelated_containers_preserved=len(containers)-1,protected_tables=list(protected_tables))
    save();print(json.dumps({k:v for k,v in result.items() if k!='backup_hashes'}))
if __name__=='__main__':main()
