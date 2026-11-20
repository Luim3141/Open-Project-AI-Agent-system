"""Prepare DEV pairs with scoped real local BGE/Qdrant, leaving MAIN data read-only."""
import hashlib,json,math,os,re,sqlite3,time,unicodedata
from pathlib import Path
import httpx
from source_spans import extract_spans
from gateway.knowledge_classifier import _compute_hash

ROOT=Path(__file__).parent;EVAL=ROOT/'eval'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev'
OUTPUT=PRIVATE/'span-reranker'
assert not OUTPUT.exists(),'PRESERVE_PREVIOUS_PREPARATION'
sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads((EVAL/'evaluation-plan.json').read_text(encoding='utf-8'))
assert sha((EVAL/'dev.json').read_bytes())==plan['dev_sha256']
assert sha((EVAL/'native-source-manifest.json').read_bytes())==plan['source_manifest_sha256']
cases=json.loads((EVAL/'dev.json').read_text(encoding='utf-8'))['cases']
manifest=json.loads((EVAL/'native-source-manifest.json').read_text(encoding='utf-8'))
docs={};chunks={};spans={}
secret=re.compile(r'(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[a-z0-9_-]{20,}\b|\bgh[pousr]_[a-z0-9]{25,}\b|\bgithub_pat_[a-z0-9_]{30,}\b|\bAIza[0-9A-Za-z_-]{25,}\b|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b|Bearer\s+[A-Za-z0-9._-]{20,}|(?:password|passwd|api[_-]?key|client[_-]?secret|claim_token|access[_-]?token|refresh[_-]?token|authorization)\s*[=:]\s*["\']?[a-z0-9_./+-]{12,})')
with sqlite3.connect((PRIVATE/'knowledge.sqlite').as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    for item in manifest['documents']:
        copy=EVAL/'private'/item['snapshot_file'];assert sha(copy.read_bytes())==item['snapshot_sha256']
        row=db.execute('SELECT * FROM knowledge_documents WHERE source_hash=? AND project_id=?',(item['source_hash'],'6')).fetchone()
        assert row and row['source_id']==item['source_id'] and json.loads(row['metadata'])==item['metadata']
        assert row['content']==copy.read_text(encoding='utf-8') and json.loads(row['allowed_roles'])==item['roles']
        assert _compute_hash(row['content'],row['doc_type'],row['source_id'],'6')==row['source_hash'],'SOURCE_HASH_MISMATCH'
        assert item['metadata']['actor_id']==20 and 'PM' in item['roles'] and not secret.search(row['content'])
        docs[row['source_hash']]=dict(row);spans[row['source_hash']]=extract_spans(row['content'])
    for r in db.execute('SELECT * FROM knowledge_chunks'):
        if r['document_id'] not in docs:continue
        raw=r['chunk_text'];assert sha(f"{r['chunk_index']}:{raw}".encode())==r['chunk_hash']
        source=docs[r['document_id']]['content'];clean=source.strip();i=r['chunk_index'];window=clean[i*500:i*500+600]
        assert window.strip()==raw
        start=len(source)-len(source.lstrip())+i*500+len(window)-len(window.lstrip())
        assert source[start:start+len(raw)]==raw
        chunks[(r['document_id'],i)]={'text':raw,'hash':r['chunk_hash'],'start':start,'end':start+len(raw)}

def terms(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text.casefold().replace('đ','d')) if not unicodedata.combining(c))
    stop={'what','which','where','when','does','the','and','with','for','how','are','was','can','that','this','document','evidence',
          'theo','nao','cua','cho','khi','duoc','trong','voi','nhu','mot','nhung','bao','gi','co','la','de','va'}
    return {v[:-1] if len(v)>4 and v.endswith('s') else v for v in re.findall(r'\w+',text) if len(v)>2 and v not in stop}

pairs=[];metadata=[];started=time.monotonic()
with httpx.Client(timeout=90,trust_env=False) as client:
    response=client.get('http://127.0.0.1:16341/healthz',timeout=5);response.raise_for_status()
    total=client.post('http://127.0.0.1:16341/collections/frozen_dev/points/count',json={'exact':True});total.raise_for_status()
    expected=json.loads((PRIVATE/'points.json').read_text(encoding='utf-8'))
    assert total.json()['result']['count']==len(expected),'CLONE_INDEX_SNAPSHOT_COUNT_MISMATCH'
    for offset in range(0,len(expected),100):
        batch=expected[offset:offset+100]
        response=client.post('http://127.0.0.1:16341/collections/frozen_dev/points',json={'ids':[p['id'] for p in batch],'with_payload':True,'with_vector':True})
        response.raise_for_status();got={str(p['id']):p for p in response.json()['result']}
        assert len(got)==len(batch)
        for p in batch:
            actual=got.get(str(p['id']));assert actual and actual['payload']==p['payload']
            a=actual['vector'];b=p['vector'];assert len(a)==len(b)==1024 and all(abs(x-y)<=1e-6 for x,y in zip(a,b)),'CLONE_INDEX_SNAPSHOT_VECTOR_MISMATCH'
    for case in cases:
        begin=time.monotonic()
        r=client.post('http://127.0.0.1:11434/api/embed',json={'model':'bge-m3','input':[case['query']],'truncate':False,'options':{'num_thread':1}})
        r.raise_for_status();vector=r.json()['embeddings'][0]
        assert len(vector)==1024 and all(math.isfinite(v) for v in vector)
        r=client.post('http://127.0.0.1:16341/collections/frozen_dev/points/search',json={'vector':vector,'limit':75,'with_payload':True,'filter':{'must':[
            {'key':'project_id','match':{'value':'6'}},{'key':'allowed_roles','match':{'value':'PM'}},
            {'key':'actor_id','match':{'value':20}},{'key':'document_id','match':{'any':list(docs)}}]}})
        r.raise_for_status();selected={}
        for hit in r.json()['result']:
            p=hit['payload'];doc=docs.get(p.get('document_id'));index=p.get('chunk_index');chunk=chunks.get((p.get('document_id'),index))
            if not doc or not chunk:continue
            if (p.get('project_id')!='6' or p.get('actor_id')!=20 or p.get('source_id')!=doc['source_id']
                    or p.get('title')!=doc['title'] or p.get('doc_type')!=doc['doc_type']):continue
            if p.get('allowed_roles')!=json.loads(doc['allowed_roles']) or p.get('metadata')!=json.loads(doc['metadata']):continue
            if p.get('chunk_text')!=chunk['text'] or p.get('chunk_hash')!=chunk['hash']:continue
            key=p['document_id']
            if key not in selected and len(selected)>=5:continue
            if key not in selected:selected[key]=[]
            if len(selected[key])<2:selected[key].append(chunk)
        query_terms=terms(case['query']);candidates=[]
        for document_id,windows in selected.items():
            eligible=[s for s in spans[document_id] if any(w['start']<=s['start'] and s['end']<=w['end'] for w in windows)]
            eligible.sort(key=lambda s:(-len(query_terms & terms(s['raw'])),s['start']))
            for span in eligible[:2]:
                identity=f"{len(pairs):06d}";pairs.append({'id':identity,'query':case['query'],'passage':span['raw']})
                candidates.append({'pair_id':identity,'document_id':document_id,'native_id':json.loads(docs[document_id]['metadata'])['native_id'],
                                   'start':span['start'],'end':span['end'],'span_sha256':span['sha256'],'source_sha256':span['source_sha256']})
        metadata.append({'case':case['id'],
                         'retrieved_native_ids':[json.loads(docs[k]['metadata'])['native_id'] for k in selected],
                         'candidates':candidates,'embedding_and_retrieval_seconds':round(time.monotonic()-begin,4)})
        print('prepared',len(metadata),'/',len(cases),flush=True)
assert 1<=len(pairs)<=400
OUTPUT.mkdir(exist_ok=False)
(OUTPUT/'pairs.json').write_text(json.dumps({'pairs':pairs},ensure_ascii=False),encoding='utf-8')
(OUTPUT/'candidates.json').write_text(json.dumps({'dev_sha256':plan['dev_sha256'],'metadata':metadata},indent=2),encoding='utf-8')
print(json.dumps({'cases':len(metadata),'pairs':len(pairs),'total_seconds':round(time.monotonic()-started,3),'private_dir':str(OUTPUT)}))
