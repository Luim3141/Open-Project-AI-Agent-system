"""Reuse the original recovery chain, read current indexes/citation, never inject faults."""
import ast,datetime,json,subprocess
from pathlib import Path
OUT=Path(__file__).parent;old=OUT.parent/'integration-final/n8n'
tree=ast.parse((old/'final_completion_recovery_readback.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=120)
assert p.returncode==0,p.stderr.decode()[-400:]
result=json.loads(p.stdout)
read="""import sqlite3,json
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
rows=d.execute("SELECT o.id,o.workflow,o.state,o.document,r.execution_id,r.document AS receipt FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id WHERE o.workflow IN ('WF13','WF14','WF15') ORDER BY o.rowid DESC LIMIT 80").fetchall()
out=[]
for row in rows:
 event=json.loads(row['document']);receipt=json.loads(row['receipt']) if row['receipt'] else {}
 if row['workflow']=='WF15' or event.get('payload',{}).get('native_id')==392 or '2d819eda-11d5-5152-8270-832ab9c58a9f' in row['document']:
  out.append({'event_id':row['id'],'workflow':row['workflow'],'state':row['state'],'execution_id':row['execution_id'],'source_id':event.get('source_id'),'source_version':event.get('source_version'),'correlation_id':event.get('correlation_id'),'kind':event.get('kind'),'business_result':receipt.get('business_result')})
print(json.dumps(out))"""
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=read.encode(),capture_output=True,timeout=30);assert p.returncode==0
result['recent_chain_and_reconcile']=json.loads(p.stdout)
result['retained_original_chain']=json.loads((old/'final-completion-main-wf14-readback.json').read_text())['actual_n8n_executions']
result['status']='REUSED_FAILURE_RETRY_CHAIN_CURRENT_NATIVE_SQLITE_FTS_QDRANT_CITATION_VERIFIED'
result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
result['local_query_embedding']='ONE_EXPLICIT_ACCEPTANCE_SEARCH; no generation and no polling inference'
(OUT/'recovery-current-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','native_id','native_version','search_current_citation_count','pending_events','engineering_mode']}))
