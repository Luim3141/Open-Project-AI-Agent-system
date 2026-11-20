"""Final protected-state, no-provider and secret-evidence checks; no business mutation."""
import json
import os
import sqlite3
from datetime import datetime,timezone
from pathlib import Path
from inspect_runtime import OUT,run
from jira_sync_backup import database_state

before=json.loads((OUT/'runtime-before.json').read_text());current=database_state('qldapm-openproject-db-1')
tables=('work_packages','relations','sprints','versions','members','member_roles','users','two_factor_authentication_devices')
assert all(current[t]==before['database'][t] for t in tables)
obs=json.loads((OUT/'main-browser-observations.json').read_text());state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway'
db=sqlite3.connect('file:'+str(state/'gateway.sqlite')+'?mode=ro',uri=True)
runs=[]
for kind,identifier in (('checked_native_read_run',obs['checked_native_read_run']),('local_supervisor_run',obs['local_supervisor_run'])):
    row=db.execute('select actor,state,result from ai_runs where id=?',(identifier,)).fetchone();assert row[0]==19 and row[1]=='done'
    result=json.loads(row[2]);assert result['model_used'] is False
    runs.append({'kind':kind,'id':identifier,'actor':row[0],'state':row[1],'model_used':False,
                 'agents':[s['agent'] for s in result.get('plan',{}).get('steps',[])],
                 'events':db.execute('select count(*) from execution_events where run_id=?',(identifier,)).fetchone()[0]})
proposal=db.execute('select actor,state,expires from proposals where id=?',(obs['proposal_id'],)).fetchone()
assert proposal[0]==19 and proposal[1]=='pending'
assert db.execute('select count(*) from gemini_call_receipts').fetchone()[0]==before['gateway']['provider_receipts']
assert db.execute('select count(*) from gemini_usage').fetchone()[0]==before['gateway']['usage']
assert db.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0]==0
credentials=json.loads((state/'credentials.json').read_text());secrets=[str(v).encode() for v in credentials.values()]
secrets += [(state/name).read_bytes().strip() for name in ('gemini.key','ui.key')]
matches=[];scanned=0
for p in OUT.rglob('*'):
    if p.is_file() and p.suffix not in ('.png','.pyc'):
        scanned+=1;content=p.read_bytes()
        if any(len(s)>8 and s in content for s in secrets):matches.append(p.relative_to(OUT).as_posix())
assert not matches,'SECRET_EVIDENCE_MATCH_FILES_ONLY:'+','.join(matches)
result={'at':datetime.now(timezone.utc).isoformat(),'passed':True,'protected_main_tables_unchanged':list(tables),
        'main_project_wp_count':329,'global_db_wp_count':current['work_packages']['rows'],
        'runs':runs,'proposal':{'id':obs['proposal_id'],'state':proposal[1],'expires':proposal[2]},
        'google_calls':0,'provider_receipts':before['gateway']['provider_receipts'],'usage':before['gateway']['usage'],
        'main_business_mutations':0,'secret_scan_files':scanned,'secret_matches':0}
(OUT/'final-evidence.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
