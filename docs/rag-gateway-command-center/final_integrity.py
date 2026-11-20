"""Read back deployed sources, corpus metadata, payloads and exact product PR state."""
import hashlib,json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
base=json.loads((OUT/'baseline.json').read_text());checks={};report={}
sources={};changes=[];absent={}
for role,name,folder,target in [('core','qldapm-openproject-web-1','openproject/ai/core/overlay','/app'),('gateway','qldapm-ai-gateway-1','openproject/ai/gateway','/app/gateway'),('telegram','qldapm-ai-telegram-ai-1','openproject/ai/telegram-ai/app','/app/app')]:
    expected={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.rb','.erb','.js','.css','.json'}}
    paths={k:target+'/'+str(Path(k).relative_to(folder)).replace('\\','/') for k in expected}
    code="import json,sys,hashlib,pathlib;d=json.load(sys.stdin);print(json.dumps({k:hashlib.sha256(pathlib.Path(v).read_bytes()).hexdigest() if pathlib.Path(v).is_file() else None for k,v in d.items()}))"
    p=subprocess.run(['docker','exec','-i',name,'python','-c',code] if role!='core' else ['docker','exec','-i',name,'ruby','-rjson','-rdigest','-e',"d=JSON.parse(STDIN.read);puts JSON.generate(d.transform_values{|p| File.file?(p) ? Digest::SHA256.file(p).hexdigest : nil})"],input=json.dumps(paths),text=True,capture_output=True,check=True)
    actual=json.loads(p.stdout);absent[role]=[k.removeprefix(folder+'/') for k,v in actual.items() if v is None]
    baseline_absent=json.loads((OUT/'baseline-source-parity.json').read_text())['absent_host_modules'][role]
    checks[role+'_all_source_parity']=sorted(absent[role])==sorted(baseline_absent) and all(v==expected[k] for k,v in actual.items() if v is not None)
    sources[role]={'present':sum(v is not None for v in actual.values()),'absent_legacy':absent[role]}
    changes.extend(k for k,v in expected.items() if base['sources'].get(k)!=v)
report['source_parity']=sources;report['product_changed']=changes;checks['exactly_11_product_files']=len(changes)==11
code='''import json,sqlite3,hashlib
from gateway.vector_client import VectorClient
d=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
docs=[]
for row in d.execute('SELECT * FROM knowledge_documents'):
 x=dict(row);docs.append({k:x.get(k) for k in ['source_hash','source_id','title','project_id','doc_type','allowed_roles','metadata']}|{'content_chars':len(x.get('content') or '')})
v=VectorClient();points=v.scroll_points('5')+v.scroll_points('6');v.close();points.sort(key=lambda p:str(p['id']))
def sha(x,compact=False):return hashlib.sha256(json.dumps(x,sort_keys=True,**({'separators':(',',':')} if compact else {})).encode()).hexdigest()
shapes={'points':points,'payloads':[p['payload'] for p in points],'id_payload':[{k:p[k] for k in ['id','payload']} for p in points],'pairs':[(p['id'],p['payload']) for p in points]}
print(json.dumps({'documents':docs,'chunks':d.execute('select count(*) from knowledge_chunks').fetchone()[0],'points':len(points),'payload_fingerprints':{k+str(c):sha(x,c) for k,x in shapes.items() for c in [False,True]}}))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code,text=True,capture_output=True,check=True,timeout=50);corpus=json.loads(p.stdout)
checks['corpus_metadata_pins_roles_lengths']=corpus['documents']==base['knowledge']['documents'];checks['corpus_counts']=corpus['chunks']==2485 and corpus['points']==2488
expected=json.loads((OUT/'corpus-evidence.json').read_text())['index_audit']['point_payload_sha256']
report['payload_baseline_sha']=expected;report['payload_matching_normalization']=[k for k,v in corpus['payload_fingerprints'].items() if v==expected]
checks['whole_vector_payload_unchanged']=bool(report['payload_matching_normalization'])
report['corpus']={k:v for k,v in corpus.items() if k!='documents'}
pr=subprocess.run(['gh','pr','view','15','--repo','Luim3141/mini-task-manager','--json','state,headRefOid,url,mergedAt,statusCheckRollup'],text=True,capture_output=True,check=True);report['pr15']=json.loads(pr.stdout)
checks['PR15_open_unmerged']=report['pr15']['state']=='OPEN' and report['pr15']['mergedAt'] is None
n8n=json.loads(subprocess.check_output(['docker','inspect','qldapm-n8n-main']))[0];checks['n8n_container_image_unchanged']=n8n['Id']==base['containers']['qldapm-n8n-main']['id'] and n8n['Image']==base['containers']['qldapm-n8n-main']['image']
report['checks']=checks
(OUT/'final-integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(checks));assert all(checks.values())
