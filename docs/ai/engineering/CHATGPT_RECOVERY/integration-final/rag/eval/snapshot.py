"""Freeze only Project6 PM-visible Native knowledge without changing live state."""
import datetime,hashlib,json,re,subprocess
from pathlib import Path

out=Path(__file__).parent;private=out/'private';private.mkdir(parents=True,exist_ok=True)
code=r'''
import json,sqlite3
db=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True)
rows=db.execute("select source_id,title,content,source_hash,metadata,allowed_roles from knowledge_documents where project_id=? and source_id like ? order by source_id",('6','actor:20:wp:%')).fetchall()
print(json.dumps([{'source_id':r[0],'title':r[1],'content':r[2],'source_hash':r[3],'metadata':json.loads(r[4]),'roles':json.loads(r[5])} for r in rows],ensure_ascii=False))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,check=True,timeout=45)
docs=json.loads(p.stdout)
assert len(docs)>=10 and all(d['metadata']['actor_id']==20 and 'PM' in d['roles'] for d in docs)
secret=re.compile(r'(?i)(?:sk-[a-z0-9]{20,}|AIza[0-9A-Za-z_-]{25,}|Bearer\s+[A-Za-z0-9._-]{20,}|(?:password|api_key|client_secret|claim_token)\s*[=:]\s*["\']?[a-z0-9._-]{12,})')
for doc in docs:
 if secret.search(doc['content']):raise ValueError('SENSITIVE_SOURCE_OMITTED_REQUIRES_REVIEW')
 target=private/(str(doc['metadata']['native_id'])+'.txt')
 assert not target.exists()
 target.write_text(doc['content'],encoding='utf-8')
 doc.pop('content');doc['snapshot_file']=target.name;doc['snapshot_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':{'project':6,'actor':20,'role':'PM'},
        'source':'Read-only Project6 actor-specific knowledge rows, no writes','documents':docs,
        'warning':'Native document describes specifications and evidence; a source citation is not evidence feature is deployed.'}
(out/'native-source-manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'count':len(docs),'native_ids':[d['metadata']['native_id'] for d in docs],'source_hashes_recorded':True}))
