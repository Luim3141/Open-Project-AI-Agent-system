from support import *
assert CONTEXT['stage']=='SERVING_IMAGES_DATA_AND_SECURITY_VERIFIED'
for relative,expected in PROPOSAL['worker_sha256'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected
started=time.time()
execute(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"],name='worker-start')
stage('APPROVED_WORKER_RESTARTED')
heartbeat=None
for _ in range(30):
    code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row;r=d.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone();print(json.dumps(dict(r) if r else None))"
    heartbeat=json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',code))
    if heartbeat and heartbeat['seen']>=started and heartbeat['run_id'] is None:break
    time.sleep(1)
else:raise RuntimeError('NEW_WORKER_HEARTBEAT_NOT_SEEN')
raw=execute(['powershell.exe','-NoProfile','-NonInteractive','-Command',"ConvertTo-Json -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -like '*openproject*ai*automation*engineering_worker.py*--watch*' } | Select-Object ProcessId,ParentProcessId,ExecutablePath,@{Name='Created';Expression={$_.CreationDate.ToUniversalTime().ToString('o')}}) -Depth 4"])
processes=json.loads(raw);assert processes
ids={r['ProcessId'] for r in processes};roots=[r for r in processes if r['ParentProcessId'] not in ids];assert len(roots)==1
assert queue()=={'mode':'OFF','active':0,'provider_receipts':358}
write('worker-verification.json',{'started_at_epoch':started,'processes':processes,'worker_roots':1,'heartbeat':heartbeat,
                               'source_hashes':PROPOSAL['worker_sha256'],'queue':queue()})
# Use stored Native identity/permission guards; no new Gateway token or UI session is created.
code=r'''
import json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway import engineering,engineering_reporting
base=Service(Store('/state'),json.loads(Path('/state/config.json').read_text()),Path('/workspaces'))
service=engineering.scoped_service(base,6)
result={}
for actor in [18,20]:
 native,who=engineering.authorized(service,actor)
 reports=engineering_reporting.list_reports(service,actor,limit=2)
 details=[]
 for r in reports['reports']:
  doc=engineering_reporting.get_report(service,actor,r['id'])
  details.append({'id_matches':doc.get('id')==r['id'],'narrative_nonempty':bool(str(doc.get('narrative','')).strip())})
 result[str(actor)]={'native_actor':who['user_id'],'role':who['role'],'project':who['project_id'],'reports_total':reports['total'],'report_details':details}
 if actor==18:
  hits=service.knowledge(who,native,'knowledge_search',{'query':'healthz','native_ids':[384],'limit':3})
  result[str(actor)]['rag_native_ids']=[v.get('native_id') for v in hits.get('items',[])]
  result[str(actor)]['rag_hits']=len(hits.get('items',[]))
try:engineering.authorized(service,19)
except PermissionError:result['actor19_engineering_denied']=True
else:raise AssertionError('ACTOR19_SHOULD_BE_DENIED')
print(json.dumps(result))
'''
result=json.loads(docker('exec','-i','qldapm-ai-gateway-1','python','-',data=code.encode(),timeout=180,name='owner-pm-read-smoke'))
assert result['actor19_engineering_denied']
assert all(d['id_matches'] and d['narrative_nonempty'] for key in ['18','20'] for d in result[key]['report_details'])
assert result['18']['rag_hits']>0
write('authenticated-service-read-smoke.json',result)
stage('WORKER_AND_AUTHORIZED_READ_SMOKE_VERIFIED')
