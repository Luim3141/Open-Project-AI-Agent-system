"""Read recorded runs/observations only; no claim, replay or provider calls."""
import json,subprocess,datetime
from pathlib import Path

out=Path(__file__).parent
ids=[json.loads((out/'planning-response.json').read_text())['run_id']]
if (out/'development-response.json').exists():ids.append(json.loads((out/'development-response.json').read_text())['run_id'])
code="""
import sqlite3,json,time
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
r={'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],'active':d.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0],'runs':[]}
for rid in IDS:
 row=d.execute('select q.state,q.payload,q.lease_until,r.result from ai_queue q join ai_runs r on r.id=q.id where q.id=?',(rid,)).fetchone()
 p=json.loads(row['payload']);v=json.loads(row['result'] or '{}')
 checkpoint=d.execute('select version,document from engineering_checkpoints where run_id=?',(rid,)).fetchone()
 r['runs'].append({'id':rid,'state':row['state'],'unit':p['unit'],'native_id':p['native_id'],'claim_generation':p.get('claim_generation'),'lease_valid':row['state']=='executing' and row['lease_until'] is not None and row['lease_until']>time.time(),'result':v,'checkpoint':{'version':checkpoint[0],**json.loads(checkpoint[1])} if checkpoint else None,'provider_receipts':d.execute('select count(*) from gemini_call_receipts where run_id=?',(rid,)).fetchone()[0]})
print(json.dumps(r))
"""
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=('IDS='+repr(ids)+'\n'+code).encode(),capture_output=True,timeout=40)
if p.returncode:raise RuntimeError('READ_ONLY_MONITOR_FAILED')
data=json.loads(p.stdout);data['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'latest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
brief={'utc':data['utc'],'mode':data['mode'],'active':data['active'],'runs':[{k:v for k,v in r.items() if k not in ('result','checkpoint')}|{'status':r['result'].get('status'),'stage':r['result'].get('stage'),'error':r['result'].get('error'),'checkpoint_stage':(r.get('checkpoint') or {}).get('stage')} for r in data['runs']]}
with (out/'timeline.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(brief,ensure_ascii=False)+'\n')
print(json.dumps(brief))
