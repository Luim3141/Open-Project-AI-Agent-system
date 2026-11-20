"""Dev-only frozen support-span coverage; no model, network or holdout access."""
import datetime,hashlib,json,os,sqlite3
from pathlib import Path
from source_spans import extract_spans

ROOT=Path(__file__).parent;EVAL=ROOT/'eval';PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev'
sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads((EVAL/'evaluation-plan.json').read_text(encoding='utf-8'))
assert sha((EVAL/'native-source-manifest.json').read_bytes())==plan['source_manifest_sha256']
assert sha((EVAL/'dev.json').read_bytes())==plan['dev_sha256']
manifest=json.loads((EVAL/'native-source-manifest.json').read_text(encoding='utf-8'))
documents={r['source_id']:r for r in manifest['documents']}
cases=json.loads((EVAL/'dev.json').read_text(encoding='utf-8'))['cases']
with sqlite3.connect((PRIVATE/'knowledge.sqlite').as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row;cache={};rows=[]
    for case in cases:
        if case['kind']!='positive':continue
        source=documents[case['source_id']];meta=source['metadata'];identifier=meta['native_id']
        assert meta['actor_id']==20 and 'PM' in source['roles'] and source['source_hash']==case['source_hash']
        assert meta['lock_version']==case['source_version'] and identifier in case['relevant_ids']
        copy=EVAL/'private'/source['snapshot_file'];assert sha(copy.read_bytes())==source['snapshot_sha256']
        if case['source_id'] not in cache:
            row=db.execute('SELECT * FROM knowledge_documents WHERE project_id=? AND source_id=?',('6',case['source_id'])).fetchone()
            assert row and row['source_hash']==source['source_hash'] and json.loads(row['metadata'])==meta
            assert row['content']==copy.read_text(encoding='utf-8')
            cache[case['source_id']]=(row['content'],extract_spans(row['content']))
        text,spans=cache[case['source_id']];start=case['support_offset'];literal=case['support_literal'];end=start+len(literal)
        assert text[start:end]==literal and sha(literal.encode())==case['support_sha256']
        matches=[s for s in spans if s['start']<=start and s['end']>=end]
        rows.append({'case':case['id'],'source_id':case['source_id'],'support_found':bool(matches),
                     'span_kind':matches[0]['kind'] if matches else None})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dev_sha256':plan['dev_sha256'],
        'extractor_sha256':sha((ROOT/'source_spans.py').read_bytes()),'positive':len(rows),
        'support_span_contained':sum(r['support_found'] for r in rows),'rows':rows,
        'status':'EXTRACTION_ONLY_NOT_RETRIEVAL_OR_ANSWERABILITY',
        'limitations':['snapshot PM actor20 only; not live ACL or freshness','source spans are untrusted and not secret-scrubbed',
                       'source/queries previously seen during dev; no document-unseen claim','no holdout access or model inference']}
target=ROOT/'span-dev-coverage.json'
if target.exists():
    previous=json.loads(target.read_text(encoding='utf-8'))
    assert all(previous.get(key)==result.get(key) for key in ['dev_sha256','extractor_sha256','positive','support_span_contained','rows','status','limitations']), 'PREVIOUS_COVERAGE_RESULT_DIFFERS'
else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','positive','support_span_contained')}))
