"""Read-only execution/provenance manifest, never exports prompts or result text."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).parent
PROGRAM=r'''
import json,sqlite3
b=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);b.row_factory=sqlite3.Row
counts={t:b.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('jobs','ai_runs','agent_tasks','agent_runs','gemini_call_receipts','execution_events')}
runs=[]
for row in b.execute('SELECT * FROM agent_runs ORDER BY rowid'):
 d=json.loads(row['document']);result=d.get('result') or {};related={}
 for t,k in [('ai_runs','id'),('gemini_call_receipts','run_id'),('execution_events','run_id')]:
  related[t]=b.execute('SELECT COUNT(*) FROM '+t+' WHERE '+k+'=?',(row['id'],)).fetchone()[0]
 receipts=[json.loads(r[0]) for r in b.execute('SELECT document FROM gemini_call_receipts WHERE run_id=?',(row['id'],))]
 live=[r for r in receipts if r.get('phase')=='generateContent' and r.get('state')=='SUCCEEDED']
 # Receipt state vocabulary can differ; include counts by exact saved state for review.
 runs.append({'id':row['id'],'actor':row['actor'],'project':row['project'],'created':d.get('created_at'),'state':d.get('state'),
  'task_id':row['task_id'],'has_result':bool(result),'related':related,
  'receipt_states':{s:sum(r.get('state')==s for r in receipts) for s in sorted({str(r.get('state')) for r in receipts})},
  'provider_generation_receipts':sum(r.get('phase')=='generateContent' for r in receipts),
  'models':sorted({str(r.get('model')) for r in receipts}),
  'declared_model_used':result.get('model_used'),'result_fields':list(result)})
print(json.dumps({'counts':counts,'runs':runs,'ai_run_actors':[list(r) for r in b.execute('SELECT actor,count(*) FROM ai_runs GROUP BY actor')]}))
'''

def main():
    inventory={}
    for env,name in [('main','qldapm-ai-gateway-1'),('staging','qldapm-ai-stage-staging-gateway-1')]:
        p=subprocess.run(['docker','exec','-i',name,'python','-'],input=PROGRAM.encode(),capture_output=True,timeout=30)
        assert p.returncode==0,'INVENTORY_FAILED_OUTPUT_WITHHELD'
        inventory[env]=json.loads(p.stdout)
    (OUT/'execution-inventory.json').write_text(json.dumps(inventory,indent=2))
    # Native verified mappings: two logins changed business roles across environments.
    mapping={6:{'login':'ba-pm','source_role':'BA-PM','target_actor':19,'target_role':'PM'},
             7:{'login':'pm','source_role':'PM','target_actor':20,'target_role':'BA'},
             8:{'login':'be','source_role':'BE','target_actor':21,'target_role':'BE'},
             9:{'login':'fe','source_role':'FE','target_actor':22,'target_role':'FE'},
             10:{'login':'qa','source_role':'QA','target_actor':23,'target_role':'QA'}}
    rows=[]
    for r in inventory['staging']['runs']:
        identity=mapping.get(r['actor'])
        conflict=not identity or identity['source_role']!=identity['target_role']
        rows.append({**r,'source_environment':'staging','source_project_identifier':'qldapm-local',
                     'identity_candidate':identity,'ownership_conflict':conflict,
                     'execution_classification':'HAS_PROVIDER_RECEIPTS_REQUIRES_REVIEW' if r['provider_generation_receipts'] else 'NO_PROVIDER_RECEIPTS_DETERMINISTIC_OR_TEST_UNCONFIRMED',
                     'sensitive_data_classification':'UNREVIEWED_NOT_EXPORTED','redaction_required':'REVIEW_REQUIRED',
                     'schema_compatibility':'SAME_GATEWAY_IMAGE_BUT_NO_SUPPORTED_HISTORICAL_PROVENANCE_IMPORTER_VERIFIED',
                     'duplicate_status':'TARGET_HAS_ZERO_AGENT_RUNS','importability':'BLOCKED_MAPPING_AND_PROVENANCE_DESIGN' if conflict else 'BLOCKED_SENSITIVITY_AND_PROVENANCE_DESIGN',
                     'proposed_main_owner':None,'imported':False})
    manifest={'at':datetime.now(timezone.utc).isoformat(),'operation':'PREVIEW_ONLY_NO_IMPORT','records':rows,
              'note':'Existing receipts retained as Staging facts. No prompts, tokens, passwords, raw outputs or credentials exported.'}
    (OUT/'AI_EXECUTION_MIGRATION_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'counts':{env:d['counts'] for env,d in inventory.items()},'manifest_records':len(rows),
                      'ownership_conflicts':sum(r['ownership_conflict'] for r in rows),'imports':0},indent=2))

if __name__=='__main__':main()
