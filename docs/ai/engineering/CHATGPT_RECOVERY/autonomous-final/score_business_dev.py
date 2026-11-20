"""Observed DEV only, lexical/identity diagnostic; never an acceptance holdout."""
import hashlib,json,os,sys,time
from pathlib import Path
OUT=Path(__file__).parent;RAG=OUT.parent/'integration-final/rag';sys.path.insert(0,str(RAG))
from business_candidate import BusinessCandidate,constraints
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
source=private/'native-candidate-canonical.json';raw=source.read_bytes();records=json.loads(raw)['documents']
active={r['metadata']['native_id']:{'lock_version':r['metadata']['lock_version'],'document_id':r['document_id']} for r in records}
engine=BusinessCandidate(records,project_id=6,source_actor=20,role='PM',current_sources=active)
cases=json.loads((RAG/'eval/dev.json').read_text(encoding='utf-8'))['cases'];rows=[];responses=[]
for case in cases:
    started=time.monotonic();reply=engine.answer(case['query']);ids=reply['retrieved_native_ids'];relevant=case['relevant_ids']
    groups,unknown=constraints(case['query'])
    rows.append({'case':case['id'],'kind':case['kind'],'retrieved_native_ids':ids,'retrieval_hit':bool(set(ids)&set(relevant)),
                 'answer_emitted':reply['answer'] is not None,'state':reply['state'],'reason':reply['reason'],
                 'answer_native_ids':[c['native_id'] for c in reply['citations']],'unknown_terms':sorted(unknown),
                 'concepts':sorted(groups),'seconds':round(time.monotonic()-started,6)})
    responses.append({'case':case,'reply':reply})
pos=[r for r in rows if r['kind']=='positive'];neg=[r for r in rows if r['kind']=='negative']
result={'status':'OBSERVED_DEV_DIAGNOSTIC_NOT_QUALIFICATION','scope':'FTS/identity only; no dense embedding/model/holdout',
        'authorized_current_records':len(engine.records),'snapshot_sha256':hashlib.sha256(raw).hexdigest(),
        'code_sha256':hashlib.sha256((RAG/'business_candidate.py').read_bytes()).hexdigest(),'positives':len(pos),'negatives':len(neg),
        'retrieval_hit_at_5':sum(r['retrieval_hit'] for r in pos)/len(pos),
        'positive_answers_emitted':sum(r['answer_emitted'] for r in pos),'negative_answers_emitted':sum(r['answer_emitted'] for r in neg),
        'negative_answer_emission_rate':sum(r['answer_emitted'] for r in neg)/len(neg),'rows':rows,
        'holdout_access':False,'generation_calls':0,'main_changed':False,
        'limits':['Existing correlated DEV labels; not independent human truth.','Answer emission is not semantic correctness.','New corpus/header/journal representation differs from previous serving snapshot.','No deployment qualification.']}
(private/'business-dev-responses.json').write_text(json.dumps(responses,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'rag-business-dev.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
