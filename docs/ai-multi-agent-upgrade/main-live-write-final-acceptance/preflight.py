"""Read-only Main admission and duplicate check, no Gemini call or Native mutation."""
import hashlib,json,os,sqlite3,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from free_tier_staging import private_directory
from jira_sync_backup import database_state,inspect

def main():
    assert not (OUT/'preflight.json').exists(),'EXISTING_ATTEMPT_RECONCILE'
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/main-live-write-final-acceptance';private_directory(private)
    state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway'
    credentials=json.loads((state/'credentials.json').read_text());config=json.loads((state/'config.json').read_text())
    assert config['gateway_mode']=='native' and config['project_id']==5
    native=Native('http://localhost:8088',credentials['19'],5);who=native.identity(19);assert who['role']=='PM'
    qa=Native('http://localhost:8088',credentials['23'],5).identity(23);assert qa['role']=='QA'
    rows=native.packages();parent=next(p for p in rows if p['id']==50)
    children=[p for p in rows if p.get('_links',{}).get('parent',{}).get('href')=='/api/v3/work_packages/50']
    duplicates=[p for p in children if ' '.join(p['subject'].split()).casefold()=='test']
    (private/'native-before.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
    (private/'database-before.json').write_text(json.dumps(database_state('qldapm-openproject-db-1')))
    # WAL stays in Linux; opening the live bind-mounted WAL with Windows SQLite breaks cross-OS locking.
    snapshot_code="import sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);b=sqlite3.connect('/state/acceptance-before.sqlite');d.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok';b.close();d.close()"
    subprocess.run(['docker','exec','qldapm-ai-gateway-1','python','-c',snapshot_code],capture_output=True,check=True)
    subprocess.run(['docker','cp','qldapm-ai-gateway-1:/state/acceptance-before.sqlite',str(private/'gateway-before.sqlite')],capture_output=True,check=True)
    with sqlite3.connect('file:'+str(private/'gateway-before.sqlite')+'?immutable=1',uri=True) as db:
        proposal=db.execute('select state,expires,result from proposals where id=?',('5e651070-9dc0-42f8-90f9-5a3909c0925e',)).fetchone()
        pending=[{'actor':r[0],'key':r[1],'action':json.loads(r[2] or '{}').get('action')} for r in db.execute("select actor,key,payload from requests where state!='done'")]
        busy=db.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0]
        counters={'provider_receipts':db.execute('select count(*) from gemini_call_receipts').fetchone()[0],'usage':db.execute('select count(*) from gemini_usage').fetchone()[0]}
    db.close()
    code="from gateway.gemini import Gemini;from pathlib import Path;import json;g=Gemini(Path('/state'));p=g.settings();print(json.dumps({'model':p['model'],'tier':p['tier'],'billing_enabled':p['billing_enabled'],'data_scope':p['data_scope'],'project':p['project'],'limits':p['limits'],'readiness':g.readiness(p)}))"
    r=subprocess.run(['docker','exec','qldapm-ai-gateway-1','python','-c',code],capture_output=True,check=True);provider=json.loads(r.stdout)
    assert provider['billing_enabled'] is False and provider['tier']=='Free'
    containers={name:{'id':inspect(name)['Id'],'image':inspect(name)['Image'],'started':inspect(name)['State']['StartedAt']} for name in subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()}
    old=json.loads((OUT.parent/'main-write-403-recovery/qualification.json').read_text())
    assert containers['qldapm-ai-gateway-1']['image']==old['gateway_image'] and containers['qldapm-openproject-web-1']['image']==old['core_image']
    assert not busy,'MAIN_BUSY_DO_NOT_SUBMIT'
    result={'at':time.time(),'private':str(private),'pm':who['user_id'],'qa':qa['user_id'],'project':5,'project_count':len(rows),
        'child_count':len(children),'children':[{'id':p['id'],'subject':p['subject']} for p in children],
        'duplicates':[{'id':p['id'],'type':p['_links']['type'],'assignee':p['_links']['assignee']} for p in duplicates],
        'old_proposal':{'state':proposal[0],'expired':proposal[1]<=time.time(),'expires':proposal[1],'has_result':bool(proposal[2])},
        'pending_requests':pending,'busy':busy,'provider':provider,'counters':counters,'containers':containers,
        'protected_files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [state/'config.json',state/'credentials.json',state/'ui.key',state/'gemini.key',state/'gemini.json']}}
    (OUT/'preflight.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('containers','protected_files','children')},ensure_ascii=False))

if __name__=='__main__':main()
