"""Read actual Owner Rails bridge status; persist only bounded public evidence."""
import datetime
import json
from pathlib import Path
from fresh_e2e import bridge,py

OUT=Path(__file__).parent
response=bridge('engineering_status',{},'functional-status-readback')
status=response['result']
assert status['project_id']==6 and len(status['workflow_status'])==16
assert any(row['source_key']=='project6-integration-qualification' for row in status['knowledge_sources'])
rows=[]
for row in status['workflow_status']:
    rows.append({k:row.get(k) for k in ('code','workflow_id','metadata_state','active','current_state','execution_url','business_side_effect','retry_eligibility')})
risk=json.loads((OUT.parent/'n8n/final-completion-main-business-readback.json').read_text())
report_id=risk['business_readback']['report_id']
notification=py("import sqlite3,json;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);rows=c.execute(\"select id,project,metadata from engineering_notifications where project=6 and json_extract(metadata,'$.report_id')=?\",("+repr(report_id)+",)).fetchall();print(json.dumps([{'id':r[0],'project':r[1],'report_id':json.loads(r[2])['report_id']} for r in rows]))")
assert notification,'PROJECT6_RISK_NOTIFICATION_MISSING'
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'OWNER_RAILS_BRIDGE_STATUS_VERIFIED',
        'route':'actual Rails Qldapm::AiBridge Owner18 → Gateway; no browser interaction claim',
        'mode':status['mode'],'knowledge_source_count':len(status['knowledge_sources']),
        'workflows':rows,'risk_notifications':notification}
(OUT/'main-status-projection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'mode':result['mode'],'workflows':len(rows),'risk_notifications':len(notification)}))
