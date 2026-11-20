"""Post-hoc DEV experiment on the previously verified BGE/Qdrant document pool."""
import hashlib,json,os,re,sqlite3,time
from pathlib import Path
from gateway.knowledge_classifier import _compute_hash
from source_spans import extract_spans
from span_selection import select_spans

ROOT=Path(__file__).parent;EVAL=ROOT/'eval'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev'
PREVIOUS=PRIVATE/'span-reranker';OUTPUT=PRIVATE/'span-reranker8'
assert not OUTPUT.exists(),'PRESERVE_EXISTING_EXPERIMENT'
sha=lambda b:hashlib.sha256(b).hexdigest()
old=json.loads((ROOT/'span-dev-warm.json').read_text());plan=json.loads((EVAL/'evaluation-plan.json').read_text())
assert sha((EVAL/'dev.json').read_bytes())==plan['dev_sha256']==old['dev_sha256']
assert sha((EVAL/'native-source-manifest.json').read_bytes())==plan['source_manifest_sha256']
assert sha((ROOT/'span_dev_prepare.py').read_bytes())==old['prepare_sha256']
assert sha((ROOT/'source_spans.py').read_bytes())==old['extractor_sha256']
priorfile=PREVIOUS/'candidates.json';prior=json.loads(priorfile.read_text());assert prior['dev_sha256']==plan['dev_sha256']
cases=json.loads((EVAL/'dev.json').read_text(encoding='utf-8'))['cases'];manifest=json.loads((EVAL/'native-source-manifest.json').read_text(encoding='utf-8'))
docs={};secret=re.compile(r'(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[a-z0-9_-]{20,}\b|\bgh[pousr]_[a-z0-9]{25,}\b|\bgithub_pat_[a-z0-9_]{30,}\b|\bAIza[0-9A-Za-z_-]{25,}\b|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b|Bearer\s+[A-Za-z0-9._-]{20,}|(?:password|passwd|api[_-]?key|client[_-]?secret|claim_token|access[_-]?token|refresh[_-]?token|authorization)\s*[=:]\s*["\']?[a-z0-9_./+-]{12,})')
with sqlite3.connect((PRIVATE/'knowledge.sqlite').as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    for item in manifest['documents']:
        copy=EVAL/'private'/item['snapshot_file'];assert sha(copy.read_bytes())==item['snapshot_sha256']
        row=db.execute('SELECT * FROM knowledge_documents WHERE source_hash=? AND project_id=?',(item['source_hash'],'6')).fetchone()
        assert row and row['source_id']==item['source_id'] and json.loads(row['metadata'])==item['metadata']
        assert row['content']==copy.read_text(encoding='utf-8') and json.loads(row['allowed_roles'])==item['roles']
        assert _compute_hash(row['content'],row['doc_type'],row['source_id'],'6')==row['source_hash']
        assert item['metadata']['actor_id']==20 and 'PM' in item['roles'] and not secret.search(row['content'])
        native=item['metadata']['native_id'];assert native not in docs
        docs[native]={'document_id':row['source_hash'],'spans':extract_spans(row['content'])}
pairs=[];metadata=[];assert len(cases)==len(prior['metadata'])
for case,previous in zip(cases,prior['metadata']):
    assert case['id']==previous['case'];begin=time.monotonic();items=[]
    for native in previous['retrieved_native_ids']:
        assert native in docs
        for span in select_spans(case['query'],docs[native]['spans']):
            identity=f'{len(pairs):06d}';pairs.append({'id':identity,'query':case['query'],'passage':span['raw']})
            items.append({'pair_id':identity,'document_id':docs[native]['document_id'],'native_id':native,
                          'start':span['start'],'end':span['end'],'span_sha256':span['sha256'],'source_sha256':span['source_sha256']})
    metadata.append({'case':case['id'],'retrieved_native_ids':previous['retrieved_native_ids'],'candidates':items,
                     'selection_seconds':round(time.monotonic()-begin,6),
                     'embedding_and_retrieval_seconds':previous['embedding_and_retrieval_seconds']})
OUTPUT.mkdir(exist_ok=False)
(OUTPUT/'pairs.json').write_text(json.dumps({'pairs':pairs},ensure_ascii=False),encoding='utf-8')
(OUTPUT/'candidates.json').write_text(json.dumps({'dev_sha256':plan['dev_sha256'],'prior_metadata_sha256':sha(priorfile.read_bytes()),
    'selector_sha256':sha((ROOT/'span_selection.py').read_bytes()),'metadata':metadata},indent=2),encoding='utf-8')
print(json.dumps({'scope':'post-hoc dev, cached verified retrieval','cases':len(metadata),'pairs':len(pairs),'max_pairs_per_query':max(len(m['candidates']) for m in metadata)}))
