"""Read-only Phase 4 baseline; credential values and conversation contents are not exported."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'docs/agent-studio-v2-stabilization'))
from preservation import capture
def run(args,**kw):return subprocess.check_output(args,text=True,encoding='utf-8',**kw)
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (OUT/'baseline.json').exists()
result=capture();result['at']=time.time();result['git']={'head':run(['git','rev-parse','HEAD']).strip(),'branch':run(['git','branch','--show-current']).strip(),'tracked_changes':run(['git','status','--porcelain','--untracked-files=no']).splitlines(),'untracked_count':len(run(['git','ls-files','--others','--exclude-standard']).splitlines())}
result['containers']={}
for name in ['qldapm-openproject-web-1','qldapm-ai-gateway-1','qldapm-ai-telegram-ai-1','qldapm-n8n-main']:
    d=json.loads(run(['docker','inspect',name]))[0]
    result['containers'][name]={'image':d['Image'],'id':d['Id'],'health':d['State'].get('Health',{}).get('Status'),'restart':d['HostConfig']['RestartPolicy']}
result['sources']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['openproject/ai/gateway','openproject/ai/core/overlay','openproject/ai/telegram-ai/app'] for p in (ROOT/base).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.rb','.erb','.js','.css','.json'}}
program='''import json,sqlite3
from gateway.vector_client import VectorClient
d=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
tables=[r[0] for r in d.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
r={'sqlite_tables':{t:{'rows':d.execute('SELECT count(*) FROM '+t).fetchone()[0],'columns':[c[1] for c in d.execute('PRAGMA table_info('+t+')')]} for t in tables},'documents':[]}
for row in d.execute('SELECT * FROM knowledge_documents'):
 x=dict(row);r['documents'].append({k:x.get(k) for k in ['source_hash','source_id','title','project_id','doc_type','allowed_roles','metadata'] }|{'content_chars':len(x.get('content') or '')})
v=VectorClient()
try:
 r['collections']=v._http.get(v.qdrant_url+'/collections',timeout=5).json()
 r['dense_collection']=v._http.get(v.qdrant_url+'/collections/'+v.collection_name,timeout=5).json()
 r['ollama_models']=[{'name':m['name'],'digest':m['digest']} for m in v._http.get(v.ollama_url+'/api/tags',timeout=5).json().get('models',[])]
finally:v.close()
print(json.dumps(r,ensure_ascii=False))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=program,text=True,capture_output=True,encoding='utf-8',check=True,timeout=60);result['knowledge']=json.loads(p.stdout)
save('baseline.json',result)
print(json.dumps({'git':result['git'],'images':result['containers'],'knowledge_tables':{k:v['rows'] for k,v in result['knowledge']['sqlite_tables'].items()},'documents':len(result['knowledge']['documents']),'dense_collection':result['knowledge']['dense_collection'],'ollama_models':result['knowledge']['ollama_models']},ensure_ascii=False))
