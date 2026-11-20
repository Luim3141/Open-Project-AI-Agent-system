"""One bounded read-only execution snapshot, safe to call while the worker runs."""
import datetime,json,subprocess
from pathlib import Path
out=Path(__file__).parent
code=r'''
import sqlite3,json,time
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);r='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
q=d.execute('select q.state,q.payload,a.state,a.result from ai_queue q join ai_runs a on a.id=q.id where q.id=?',(r,)).fetchone()
cp=d.execute('select version,document from engineering_checkpoints where run_id=?',(r,)).fetchone();c=json.loads(cp[1]);payload=json.loads(q[1]);result=json.loads(q[3] or '{}')
receipts=[json.loads(row[0]) for row in d.execute('select document from gemini_call_receipts where run_id=?',(r,))]
generations=[row for row in receipts if row.get('phase')=='generateContent']
print(json.dumps({'at':time.time(),'queue_state':q[0],'run_state':q[2],'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],
 'recovery_count':payload.get('recovery_count'),'checkpoint_version':cp[0],'checkpoint':{k:c.get(k) for k in ['stage','completed_steps','resumable','terminal_known','error']},
 'result':{k:result.get(k) for k in ['status','stage','error','pr_url','head_sha']},'generation_calls':len(generations),
 'last_receipts':[{k:item.get(k) for k in ['id','session_id','step','agent','http_status','state','at','completed_at','usage','call_cap']} for item in sorted(generations,key=lambda x:x.get('at',0))[-6:]]}))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,check=True,timeout=30)
result=json.loads(p.stdout);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
folder=out/'wp391-observations';folder.mkdir(exist_ok=True);(folder/(stamp+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
