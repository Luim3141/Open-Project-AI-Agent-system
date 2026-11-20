"""Read only projection; no resume, provider call or Native mutation."""
import datetime,json,subprocess
from pathlib import Path

out=Path(__file__).parent
code=r'''
import json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
r='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
row=d.execute('select version,document from engineering_checkpoints where run_id=?',(r,)).fetchone();c=json.loads(row[1])
queue=d.execute('select state,payload from ai_queue where id=?',(r,)).fetchone();payload=json.loads(queue[1])
print(json.dumps({'run_id':r,'queue_state':queue[0],'native_id':payload['native_id'],'unit':payload['unit'],
 'source_version':payload['source_version'],'recovery_count':payload.get('recovery_count'),
 'checkpoint_version':row[0],'checkpoint_fields':sorted(c),
 'checkpoint':{k:v for k,v in c.items() if k in ['stage','completed_steps','terminal_known','resumable','head_sha','branch','workspace','error']},
 'unsafe_native_receipts':d.execute("select count(*) from requests where key like ? and state not in ('done','rejected')",('engineering-'+r+'-%',)).fetchone()[0],
 'generations':d.execute("select count(*) from gemini_call_receipts where run_id=? and json_extract(document,'$.phase')='generateContent'",(r,)).fetchone()[0]}))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,check=True,timeout=30)
result=json.loads(p.stdout);result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'wp391-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
