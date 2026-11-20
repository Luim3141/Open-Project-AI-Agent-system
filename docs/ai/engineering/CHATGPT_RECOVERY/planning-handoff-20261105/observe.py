"""Safe incident state and immutable rows; no provider call or control mutation."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
OUT=Path(__file__).parent
RUN='e2db6811-44fe-418c-b7dc-12fb9d52d330'
code=r'''
import sqlite3,json,hashlib
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
run='e2db6811-44fe-418c-b7dc-12fb9d52d330';pins={}
for table in ['ai_queue','ai_runs','engineering_unit_definitions','engineering_plans','delegated_control','gemini_call_receipts']:
 rows=[dict(r) for r in d.execute('SELECT * FROM '+table)];pins[table]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(sorted(json.dumps(r,sort_keys=True) for r in rows)).encode()).hexdigest()}
q=dict(d.execute('SELECT state,payload FROM ai_queue WHERE id=?',(run,)).fetchone());q['payload']=json.loads(q['payload'])
result=json.loads(d.execute('SELECT result FROM ai_runs WHERE id=?',(run,)).fetchone()[0]);plan=json.loads(d.execute('SELECT document FROM engineering_plans WHERE id=?',(run,)).fetchone()[0]);checkpoint=dict(d.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run,)).fetchone());checkpoint['document']=json.loads(checkpoint['document'])
pending=[dict(r) for r in d.execute("SELECT actor,key,state,payload,result FROM requests WHERE key LIKE ? AND state NOT IN ('done','rejected')",('engineering-'+run+'-%',))]
unknown=[dict(r) for r in d.execute("SELECT * FROM requests WHERE state NOT IN ('done','rejected') ORDER BY rowid")]
commands=[json.loads(r[0]) for r in d.execute('SELECT document FROM engineering_owner_commands ORDER BY sequence DESC LIMIT 12')]
print(json.dumps({'pins':pins,'run':q,'result':result,'plan':plan,'checkpoint':checkpoint,'pending':pending,'unknown_requests':{'count':len(unknown),'sha256':hashlib.sha256(json.dumps(sorted(json.dumps(r,sort_keys=True) for r in unknown)).encode()).hexdigest()},'commands':commands,'control':dict(d.execute('SELECT * FROM engineering_control WHERE project=6').fetchone()),'revision':d.execute('SELECT revision FROM engineering_owner_revision WHERE project=6').fetchone()[0]}))
'''
label=sys.argv[1];assert label.replace('-','').isalnum()
value=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=30))
value['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
for role,name in [('gateway','qldapm-ai-gateway-1'),('core','qldapm-openproject-web-1'),('n8n','qldapm-n8n-main')]:
 row=json.loads(subprocess.check_output(['docker','inspect',name]))[0];value.setdefault('images',{})[role]=row['Image']
path=OUT/(label+'.json');assert not path.exists(),path
path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'label':label,'state':value['result']['status'],'plan':value['plan']['state'],'pending':len(value['pending']),'provider_receipts':value['pins']['gemini_call_receipts']['count'],'revision':value['revision']}))
