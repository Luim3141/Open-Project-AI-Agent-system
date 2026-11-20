"""Replay scan preparation with GET/read-only SQLite; never invoke scan/refresh."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

CODE=r'''
import json,sqlite3,time
from pathlib import Path
from gateway.native import Native
from gateway.openproject_loader import work_package_to_document,actor_work_package_document
config=json.loads(Path('/state/config.json').read_text())
credentials=json.loads(Path('/state/credentials.json').read_text())
native=Native(config['openproject_url'],credentials['18'],5)
db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
generation=db.execute('SELECT generation FROM native_index_scans WHERE actor=18 AND project=5').fetchone()[0]
db.close()
db=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row
indexed={r['source_id']:dict(r) for r in db.execute("SELECT * FROM knowledge_documents WHERE project_id='5'")}
db.close()
step='identity';identifier=None;audited=0;started=time.monotonic()
try:
 native.identity(18);step='packages';items=native.packages();ordered=sorted(i['id'] for i in items)
 audit={ordered[(generation*32+i)%len(ordered)] for i in range(min(32,len(ordered)))}
 for item in items:
  identifier=item['id'];step='canonical_classification'
  doc=work_package_to_document(item,'5');old=indexed.get(doc.source_id)
  current=old is not None and old['source_hash']==doc.source_hash and json.loads(old['metadata']).get('lock_version')==item['lockVersion']
  previous=indexed.get(f'actor:18:wp:{identifier}');updated=item.get('updatedAt')
  if updated is not None and previous and 'source_updated_at' in json.loads(previous['metadata']):
   current=current and json.loads(previous['metadata'])['source_updated_at']==updated
  if current and identifier in audit:
   step='activities';activities=native.collection(f'/api/v3/work_packages/{identifier}/activities');audited+=1
   step='activity_classification';actor_work_package_document(item,5,18,'AI_SYSTEM_OWNER',activities)
 result={'success':True,'generation':generation,'audit_ids':sorted(audit),'audited':audited}
except Exception as error:
 result={'success':False,'generation':generation,'step':step,'native_id':identifier,
  'error_class':type(error).__name__,'status':getattr(error,'status',None),
  'code':str(error).split(':',1)[0],'audited':audited}
result['seconds']=time.monotonic()-started
print(json.dumps(result))
'''

if __name__=='__main__':
    response=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=CODE,
        capture_output=True,text=True,encoding='utf-8',timeout=120,check=True)
    result={'utc':datetime.now(timezone.utc).isoformat(),'command':
        'openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/rag/diagnose_scan_blocker.py',
        'route':'OS_OPERATOR_NATIVE_GET_AND_SQLITE_RO_ONLY','probe':json.loads(response.stdout),
        'source_mutations':0,'index_mutations':0,
        'limits':'Preparation replay only, not invoking native_incremental.scan or advancing inventory; Native authorization unchanged.'}
    Path(__file__).with_name('scan-blocker.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
