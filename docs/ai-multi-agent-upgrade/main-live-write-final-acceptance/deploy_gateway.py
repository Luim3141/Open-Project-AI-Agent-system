"""Owner-authorized minimal budget/audit fix. Gateway only; no business request or Google call."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from jira_sync_backup import inspect,database_state

def run(*args):
    p=subprocess.run(args,capture_output=True,timeout=180);assert p.returncode==0,'APPLY_COMMAND_FAILED_OUTPUT_WITHHELD'
    return p.stdout

def main():
    assert not (OUT/'deployment.json').exists(),'DEPLOYMENT_EXISTS_RECONCILE'
    q=json.loads((OUT/'qualification.json').read_text());b=json.loads((OUT/'backup.json').read_text())
    assert q['linux_exit']==0 and b['passed'] and json.loads((OUT/'clone-result.json').read_text())['passed']
    for rel,sha in q['source'].items():assert hashlib.sha256((ROOT/'openproject/ai'/rel).read_bytes()).hexdigest()==sha,'SOURCE_DRIFT'
    for name,sha in b['hashes'].items():assert hashlib.sha256((Path(b['directory'])/name).read_bytes()).hexdigest()==sha,'BACKUP_DRIFT'
    assert inspect('qldapm-ai-gateway-1')['Image']==q['rollback_gateway']
    assert inspect('qldapm-openproject-web-1')['Image']==q['core_image']
    before=database_state('qldapm-openproject-db-1')
    assert before['work_packages']==json.loads((Path(b['directory'])/'database-before.json').read_text())['work_packages'],'MAIN_WP_DRIFT'
    ai=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
    assert not (ai/'gateway/business-acceptance.json').exists(),'UNEXPECTED_ARMED_CONSENT'
    env=ai/'.env';lines=env.read_text(encoding='utf-8-sig').splitlines();assert sum(l.startswith('AI_IMAGE=') for l in lines)==1
    env.write_text('\n'.join('AI_IMAGE='+q['gateway_image'] if l.startswith('AI_IMAGE=') else l for l in lines)+'\n',encoding='utf-8')
    lock=json.loads((ai/'image-lock.json').read_text());lock['AI_IMAGE']=q['gateway_image'];(ai/'image-lock.json').write_text(json.dumps(lock,indent=2))
    compose=['docker','compose','--project-name','qldapm-ai','--env-file',str(env),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml')]
    cfg=json.loads(run(*compose,'config','--format','json'))['services']['gateway']
    assert cfg['image']==q['gateway_image'] and cfg['environment']['QLDAPM_AI_ENVIRONMENT']=='production'
    assert 'QLDAPM_OFFLINE_WRITE_UAT' not in cfg.get('environment',{}) and all(p.get('host_ip')=='127.0.0.1' for p in cfg['ports'])
    result={'phase':'CONFIG_VALIDATED','gateway_image':q['gateway_image'],'core_image':q['core_image'],'rollback_gateway':q['rollback_gateway'],
        'backup':b['directory'],'google_calls':0,'native_writes':0}
    def save():(OUT/'deployment.json').write_text(json.dumps(result,indent=2))
    save()
    with (OUT/'gateway-apply.log').open('wb') as f:
        p=subprocess.run(compose+['up','-d','--no-deps','gateway'],stdout=f,stderr=subprocess.STDOUT,timeout=180)
    assert p.returncode==0,'APPLY_FAILED_RECONCILE'
    for _ in range(30):
        c=inspect('qldapm-ai-gateway-1');assert c['State']['Running']
        if c['State'].get('Health',{}).get('Status')=='healthy':break
        time.sleep(2)
    else:raise AssertionError('HEALTH_NOT_READY')
    assert c['Image']==q['gateway_image']
    for name,before_container in b['containers'].items():
        if name=='qldapm-ai-gateway-1':continue
        now=inspect(name);assert now['Id']==before_container['id'] and now['Image']==before_container['image'] and now['State']['StartedAt']==before_container['started'],'OTHER_CONTAINER_DRIFT:'+name
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in b['protected'].items()),'PROTECTED_CONFIG_DRIFT'
    current=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',
        "import hashlib,json;from pathlib import Path;print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/gateway').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))"))
    assert all(q['source'].get(p)==h for p,h in current.items()),'PACKAGED_SOURCE_DRIFT'
    assert all('gateway/'+name in current for name in ('business_acceptance.py','ai_worker.py','gemini.py'))
    result.update(phase='MAIN_GATEWAY_DEPLOYED_HEALTH_PARITY_PASS',packaged_files=len(current),other_containers_preserved=len(b['containers'])-1,protected_files_preserved=True)
    save();print(json.dumps(result))

if __name__=='__main__':main()
