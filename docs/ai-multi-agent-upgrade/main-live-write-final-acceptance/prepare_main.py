"""Fresh online backups and Native validation only; never applies Native business mutations."""
import hashlib,json,os,shutil,sqlite3,subprocess,sys,time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from jira_sync_backup import database_state,inspect
from free_tier_staging import private_directory

def run(*args,data=None):
    p=subprocess.run(args,input=data,capture_output=True,timeout=180)
    assert p.returncode==0,'PREPARE_FAILED_OUTPUT_WITHHELD:'+str(args[:3])
    return p.stdout

def main():
    assert not (OUT/'backup.json').exists(),'EXISTING_BACKUP_RECONCILE'
    assert json.loads((OUT/'clone-result.json').read_text())['passed']
    q=json.loads((OUT/'qualification.json').read_text());assert q['linux_exit']==0
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai';state=runtime/'gateway'
    private=runtime/'operator/main-live-write-final-acceptance';directory=private/datetime.now().strftime('backup-%Y%m%d-%H%M%S');private_directory(directory)
    credentials=json.loads((state/'credentials.json').read_text());config=json.loads((state/'config.json').read_text())
    n=Native('http://localhost:8088',credentials['19'],5);assert n.identity(19)['role']=='PM'
    assert Native('http://localhost:8088',credentials['23'],5).identity(23)['role']=='QA'
    rows=n.packages();parent=next(p for p in rows if p['id']==50)
    children=[p for p in rows if p.get('_links',{}).get('parent',{}).get('href')=='/api/v3/work_packages/50']
    assert not any(' '.join(p['subject'].split()).casefold()=='test' for p in children),'ALREADY_EXISTS_STOP'
    assert 10 in config['type_ids']
    types=n.call('/api/v3/types/10');assert types['name']=='Subtask'
    form=n.call('/api/v3/projects/5/work_packages/form','POST',{'subject':'test',config['source_field']:'owner-preflight-only',
        'description':{'format':'markdown','raw':''},'_links':{'project':{'href':'/api/v3/projects/5'},
        'type':{'href':'/api/v3/types/10'},'parent':{'href':'/api/v3/work_packages/50'},'assignee':{'href':'/api/v3/users/23'}}})
    assert not form.get('_embedded',{}).get('validationErrors'),'NATIVE_FORM_REJECTED'
    (directory/'native-before.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
    (directory/'native-form.json').write_text(json.dumps(form,ensure_ascii=False),encoding='utf-8')
    before=database_state('qldapm-openproject-db-1');(directory/'database-before.json').write_text(json.dumps(before))
    sql='BEGIN READ ONLY; SELECT json_agg(to_jsonb(w) ORDER BY id) FROM work_packages w; COMMIT;'
    pg=run('docker','exec','-i','qldapm-openproject-db-1','psql','-X','-qAt','-U','postgres','-d','openproject',data=sql.encode())
    (directory/'work-packages-before.json').write_bytes(pg)
    with (directory/'database.dump').open('xb') as f:
        p=subprocess.run(['docker','exec','qldapm-openproject-db-1','pg_dump','-U','postgres','-Fc','openproject'],stdout=f,stderr=subprocess.PIPE,timeout=180)
    assert p.returncode==0,'PG_BACKUP_FAILED'
    code="""import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert d.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0]==0
assert d.execute("select count(*) from requests where state!='done'").fetchone()[0]==0
assert d.execute("select count(*) from jobs where state in ('queued','running','failed_or_unknown')").fetchone()[0]==0
p=d.execute("select state,expires,result from proposals where id='5e651070-9dc0-42f8-90f9-5a3909c0925e'").fetchone()
print(json.dumps({'old_proposal':list(p),'receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0],'usage':d.execute('select count(*) from gemini_usage').fetchone()[0]}))
b=sqlite3.connect('/state/acceptance-fresh.sqlite');d.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok';b.close();d.close()"""
    gateway=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',code));assert gateway['old_proposal'][0]=='pending' and gateway['old_proposal'][1]<time.time() and not gateway['old_proposal'][2]
    run('docker','cp','qldapm-ai-gateway-1:/state/acceptance-fresh.sqlite',str(directory/'gateway.sqlite'))
    for p in [runtime/'.env',runtime/'image-lock.json',*[state/name for name in ('config.json','credentials.json','gemini.key','gemini.json','ui.key')],runtime/'operator/gemini-main/free-tier-proof.json']:
        shutil.copy2(p,directory/('state-'+p.name if p.parent==state else p.name))
    before_images=json.loads(run('docker','inspect',*subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()))
    containers={p['Name'].lstrip('/'):{'id':p['Id'],'image':p['Image'],'started':p['State']['StartedAt']} for p in before_images}
    assert containers['qldapm-ai-gateway-1']['image']==q['rollback_gateway'] and containers['qldapm-openproject-web-1']['image']==q['core_image']
    compose=['docker','compose','--project-name','qldapm-ai','--env-file',str(runtime/'.env'),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml')]
    (directory/'compose-before.json').write_bytes(run(*compose,'config','--format','json'))
    (directory/'containers.json').write_text(json.dumps(containers))
    protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [state/name for name in ('config.json','credentials.json','gemini.key','gemini.json','ui.key')]}
    receipt={'passed':True,'directory':str(directory),'project_count':len(rows),'global_count':before['work_packages']['rows'],'child_count':len(children),
        'native_type':types['name'],'native_form':'VALID_NO_WRITES','parent_dates':{k:parent.get(k) for k in ('startDate','dueDate','lockVersion')},
        'gateway_before':gateway,'protected':protected,'containers':containers,
        'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}}
    (OUT/'backup.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k not in ('hashes','protected','containers')}))

if __name__=='__main__':main()
