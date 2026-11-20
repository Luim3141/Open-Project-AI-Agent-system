"""Owner-authorized Gateway + web replacement only, fresh backups, immutable rollback."""
import hashlib,json,os,re,shutil,subprocess,sys,time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from jira_sync_backup import database_state,inspect
from free_tier_staging import private_directory
from gateway.native import Native
def run(*args,timeout=180):
    p=subprocess.run(args,capture_output=True,timeout=timeout);assert p.returncode==0,'DEPLOY_COMMAND_FAILED_OUTPUT_WITHHELD';return p.stdout
def host_path(value):
    match=re.fullmatch(r'/run/desktop/mnt/host/([a-z])/(.+)',value)
    return Path(match[1].upper()+':/'+match[2] if match else value).resolve()
def main():
    citation='--citation-fix' in sys.argv
    followup='--read-fix' in sys.argv or citation
    record=OUT/('deployment-citation-fix.json' if citation else 'deployment-read-fix.json' if followup else 'deployment.json')
    assert not record.exists(),'DEPLOYMENT_STARTED_RECONCILE_BEFORE_RETRY'
    q=json.loads((OUT/'qualification.json').read_text());b=json.loads((OUT/'baseline.json').read_text())
    if followup:
        old=json.loads((OUT/('deployment-read-fix.json' if citation else 'deployment.json')).read_text());assert old['phase']=='MAIN_DEPLOYED_HEALTH_PASS'
        assert len(json.loads((OUT/'live-initial-failure.json').read_text())['receipts'])==4
        for name,key in (('qldapm-ai-gateway-1','gateway_image'),('qldapm-openproject-web-1','core_image')):
            current=inspect(name);assert current['Image']==old[key]
            b['containers'][name]={'id':current['Id'],'image':current['Image'],'started':current['State']['StartedAt']}
    assert q['linux_exit']==q['windows_exit']==0 and json.loads((OUT/'clone-browser.json').read_text())['passed']
    assert json.loads((OUT/'clone-native-proof.json').read_text())['passed']
    for rel,h in q['source'].items():assert hashlib.sha256((ROOT/'openproject/ai'/rel).read_bytes()).hexdigest()==h,'SOURCE_DRIFT'
    for path,h in b['protected_files'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,'PROTECTED_CONFIG_CHANGED'
    for name in ('qldapm-closeout-20261022-browser','qldapm-closeout-20261022-gateway','qldapm-closeout-20261022-core'):
        assert inspect(name)['Config']['Labels'].get('qldapm.qualification')=='main-closeout-20261022'
        run('docker','stop','--time','20',name)
    assert inspect('qldapm-write403-20261021-db')['Config']['Labels'].get('qldapm.qualification')=='main-write403-20261021'
    run('docker','stop','--time','20','qldapm-write403-20261021-db')
    names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert len(names)==18
    current={n:inspect(n) for n in names}
    for n,v in b['containers'].items():assert (current[n]['Id'],current[n]['Image'],current[n]['State']['StartedAt'])==(v['id'],v['image'],v['started']),n
    ai=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai';native_root=ai.parent/'openproject';state=ai/'gateway'
    directory=Path(b['private'])/datetime.now().strftime('backup-%Y%m%d-%H%M%S');private_directory(directory)
    pg=database_state('qldapm-openproject-db-1');(directory/'database-before.json').write_text(json.dumps(pg))
    credentials=json.loads((state/'credentials.json').read_text());n=Native('http://localhost:8088',credentials['19'],5)
    assert n.identity(19)['role']=='PM';rows=n.packages();assert len(rows)==330
    assert next(r for r in rows if r['id']==367)['_links']['assignee']['href']=='/api/v3/users/23'
    (directory/'native-before.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
    with (directory/'database.dump').open('xb') as f:p=subprocess.run(['docker','exec','qldapm-openproject-db-1','pg_dump','-U','postgres','-Fc','openproject'],stdout=f,stderr=subprocess.PIPE,timeout=180)
    assert p.returncode==0,'PG_BACKUP_FAILED'
    with (directory/'database.dump').open('rb') as f:
        verified=subprocess.run(['docker','exec','-i','qldapm-openproject-db-1','pg_restore','--list'],stdin=f,capture_output=True,timeout=60)
    assert verified.returncode==0,'PG_DUMP_LIST_FAILED'
    code="""import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert d.execute("select count(*) from ai_runs where state='running'").fetchone()[0]==0
assert d.execute("select count(*) from requests where state!='done'").fetchone()[0]==0
r={'runs':d.execute('select count(*) from ai_runs').fetchone()[0],'receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0],'usage':d.execute('select count(*) from gemini_usage').fetchone()[0]}
b=sqlite3.connect('/state/closeout-backup.sqlite');d.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok';b.close();d.close();print(json.dumps(r))"""
    counters=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',code))
    run('docker','cp','qldapm-ai-gateway-1:/state/closeout-backup.sqlite',str(directory/'gateway.sqlite'))
    for path in b['protected_files']:shutil.copy2(path,directory/('state-'+Path(path).name))
    shutil.copy2(ai/'.env',directory/'ai.env');shutil.copy2(ai/'image-lock.json',directory/'ai-image-lock.json')
    shutil.copy2(native_root/'.env',directory/'core.env')
    if (native_root/'image-lock.json').exists():shutil.copy2(native_root/'image-lock.json',directory/'core-image-lock.json')
    run('docker','cp','qldapm-ai-gateway-1:/app/gateway',str(directory/'gateway-source'))
    run('docker','cp','qldapm-openproject-web-1:/app/app/views/qldapm_ai',str(directory/'core-views'))
    (directory/'git-status.txt').write_bytes(run('git','status','--short'))
    commands=[['docker','compose','--project-name','qldapm-ai','--env-file',str(ai/'.env'),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml')],
        ['docker','compose','--project-name','qldapm-openproject','--env-file',str(native_root/'.env'),'-f',str(ROOT/'openproject/compose.yml'),'-f',str(native_root/'ui-bridge.yml')]]
    for c,name,service in ((commands[0],'qldapm-ai-gateway-1','gateway'),(commands[1],'qldapm-openproject-web-1','web')):
        cfg=json.loads(run(*c,'config','--format','json'))
        desired=cfg['services'][service]['volumes'];actual=inspect(name)['Mounts']
        for mount in desired:
            dst=mount['target'];existing=next(m for m in actual if m['Destination']==dst)
            if mount['type']=='volume':assert existing['Name']==cfg['volumes'][mount['source']]['name'],'VOLUME_DRIFT'
            else:assert host_path(existing['Source'])==host_path(mount['source']),'BIND_MOUNT_DRIFT'
    for i,c in enumerate(commands):(directory/f'compose-before-{i}.json').write_bytes(run(*c,'config','--format','json'))
    result={'phase':'BACKUP_VERIFIED','directory':str(directory),'gateway_image':q['gateway_image'],'core_image':q['core_image'],
        'rollback_gateway':b['containers']['qldapm-ai-gateway-1']['image'],'rollback_core':b['containers']['qldapm-openproject-web-1']['image'],
        'counters':counters,'google_calls':0,'native_mutations':0,'backup_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}}
    def save():record.write_text(json.dumps(result,indent=2))
    def update_env(path,key,image):path.write_text('\n'.join(key+'='+image if l.startswith(key+'=') else l for l in path.read_text(encoding='utf-8-sig').splitlines())+'\n',encoding='utf-8')
    save()
    update_env(ai/'.env','AI_IMAGE',q['gateway_image']);update_env(native_root/'.env','OP_IMAGE',q['core_image'])
    for path,key,image in ((ai/'image-lock.json','AI_IMAGE',q['gateway_image']),(native_root/'image-lock.json','OP_IMAGE',q['core_image'])):
        if path.exists():
            lock=json.loads(path.read_text());lock[key]=image;path.write_text(json.dumps(lock,indent=2))
    try:
        if not citation:run(*commands[1],'up','-d','--no-deps','web')
        for _ in range(40):
            if inspect('qldapm-openproject-web-1')['State'].get('Health',{}).get('Status')=='healthy':break
            time.sleep(2)
        else:raise AssertionError('CORE_HEALTH_TIMEOUT')
        run(*commands[0],'up','-d','--no-deps','gateway')
        for _ in range(40):
            if all(inspect(n)['State'].get('Health',{}).get('Status')=='healthy' for n in ('qldapm-ai-gateway-1','qldapm-openproject-web-1')):break
            time.sleep(2)
        else:raise AssertionError('MAIN_HEALTH_TIMEOUT')
    except Exception:
        shutil.copy2(directory/'ai.env',ai/'.env');shutil.copy2(directory/'core.env',native_root/'.env')
        shutil.copy2(directory/'ai-image-lock.json',ai/'image-lock.json')
        if (directory/'core-image-lock.json').exists():shutil.copy2(directory/'core-image-lock.json',native_root/'image-lock.json')
        for c,service in zip(commands[:1] if citation else commands,('gateway',) if citation else ('gateway','web')):run(*c,'up','-d','--no-deps',service)
        result['phase']='ROLLED_BACK_IMAGES_ONLY';save();raise
    after=database_state('qldapm-openproject-db-1');protected=('work_packages','relations','sprints','versions','users','user_passwords','roles','role_permissions','members','member_roles','tokens','two_factor_authentication_devices','custom_values')
    assert all(pg[t]==after[t] for t in protected),'NATIVE_PROTECTED_DATA_CHANGED'
    for name,old in b['containers'].items():
        if name in ({'qldapm-ai-gateway-1'} if citation else {'qldapm-ai-gateway-1','qldapm-openproject-web-1'}):continue
        now=inspect(name);assert (now['Id'],now['Image'],now['State']['StartedAt'])==(old['id'],old['image'],old['started']),name
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in b['protected_files'].items())
    result.update(phase='MAIN_DEPLOYED_HEALTH_PASS',unrelated_serving_containers_preserved=17 if citation else 16,protected_tables=list(protected));save()
    print(json.dumps({k:v for k,v in result.items() if k!='backup_hashes'}))
if __name__=='__main__':main()
