"""Offline representation/provenance audit, without queries, labels or model calls."""
import collections,hashlib,json,os,sqlite3,sys
from pathlib import Path
OUT=Path(__file__).parent;RAG=OUT.parent/'integration-final/rag';sys.path.insert(0,str(RAG))
from business_spans import business_spans
from readable_spans import raw_citation

private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
snapshot=private/'knowledge-baseline.sqlite';db=sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
projected=[];counts=collections.Counter();kinds=collections.Counter();errors=0
for row in db.execute("SELECT * FROM knowledge_documents WHERE project_id='6' AND source_id LIKE 'actor:20:wp:%'"):
    source=row['content'];metadata=json.loads(row['metadata']);spans=business_spans(source)
    for span in spans:
        assert source[span['start']:span['end']]==span['raw']
        assert hashlib.sha256(span['raw'].encode()).hexdigest()==span['sha256']
        assert span['source_sha256']==hashlib.sha256(source.encode()).hexdigest()
        kinds[span['evidence_type']]+=1
        if span.get('json_path'):counts[span['json_path'][-1]]+=1
        # Full-span citation checks raw/readable reversibility; duplicates are not guessed.
        try:
            citation=raw_citation(source,span,span['text'])
            assert source[citation['start']:citation['end']]==citation['raw'] if 'raw' in citation else True
        except ValueError:errors+=1
    projected.append({'document_id':row['source_hash'],'source_id':row['source_id'],'project_id':6,'metadata':metadata,
                      'allowed_roles':json.loads(row['allowed_roles']),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'spans':spans})
raw=json.dumps(projected,ensure_ascii=False,sort_keys=True).encode();path=private/'business-projection.json'
if path.exists():assert path.read_bytes()==raw,'PROJECTION_FROZEN_DO_NOT_OVERWRITE'
else:path.write_bytes(raw)
result={'status':'REPRESENTATION_AUDITED_NOT_QUALITY_QUALIFIED','documents':len(projected),'spans':sum(len(d['spans']) for d in projected),
        'source_chars':sum(len(r[0]) for r in db.execute("SELECT content FROM knowledge_documents WHERE project_id='6' AND source_id LIKE 'actor:20:wp:%'")),
        'projection_chars':sum(len(s['text']) for d in projected for s in d['spans']),
        'evidence_types':dict(kinds),'json_fields':dict(counts),'provenance_errors':0,'unquotable_full_spans':errors,
        'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'projection_sha256':hashlib.sha256(raw).hexdigest(),
        'extractor_sha256':hashlib.sha256((RAG/'source_spans.py').read_bytes()).hexdigest(),
        'projection_code_sha256':hashlib.sha256((RAG/'business_spans.py').read_bytes()).hexdigest(),
        'holdout_access':False,'query_labels_access':False,'generation_calls':0,'main_changed':False,
        'limits':['Projection is derived evidence, not verified implementation/current status.','Retrieval/answerability and representative benchmark remain required.']}
(OUT/'rag-business-projection-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
