"""Offline source adjudication and retrieval scoring, no new inference or holdout access."""
import datetime,hashlib,json,os
from pathlib import Path
OUT=Path(__file__).parent;RAG=OUT.parent/'integration-final/rag'
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
cases=json.loads((RAG/'eval/dev.json').read_text(encoding='utf-8'))['cases']
packets=json.loads((private/'semantic-fact-dev/packets.json').read_text(encoding='utf-8'))
positive=[c for c in cases if c['kind']=='positive']
pilot=json.loads((OUT/'fact-selector-semantic-result.json').read_text())
development=json.loads((OUT/'semantic-fact-dev-result.json').read_text())
source={r['document_id']:r for r in json.loads((private/'native-candidate-canonical.json').read_text(encoding='utf-8'))['documents']}
checked=0
for work in ['fact-selector-semantic','semantic-fact-dev']:
    answers=([json.loads((private/work/f'answer-{i}.json').read_text(encoding='utf-8')) for i in range(6)] if work=='fact-selector-semantic'
             else [r['answer'] for r in json.loads((private/work/'answers.json').read_text(encoding='utf-8'))])
    for answer in answers:
        for c in answer['citations']:
            record=source[c['document_id']];raw=record['content'][c['start']:c['end']]
            assert hashlib.sha256(raw.encode()).hexdigest()==c['sha256'] and c['source_sha256']==record['source_sha256']
            assert c['lock_version']==record['metadata']['lock_version'] and c['citation']==f"/work_packages/{record['metadata']['native_id']}"
            checked+=1
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAILED_QUALIFICATION_NOT_DEPLOYED',
 'reviewer':'root assistant source review; NOT independent human ground truth; only prior WP392 intent is human-confirmed',
 'retrieval':{'scope':'Observed correlated DEV, exact frozen candidate corpus, actual BGE/Qdrant906facts + FTS/identity union',
              'hit_at_5':sum(bool(set(c['relevant_ids'])&set(packets[c['query']]['retrieved_native_ids'])) for c in positive)/len(positive),'positives':len(positive)},
 'six_case_pilot':{'positive_source_hits':4,'positive_queries':4,'strict_complete_source_supported_answers':3,
                  'negative_answers':0,'negative_queries':2,'warm_seconds':[r['seconds'] for r in pilot['rows'][1:]],
                  'source_issue':'CRUD selection includes parent379 copied assignment objective as a second answer identity; child381 is relevant, but complete unambiguous unit answer not accepted.',
                  'limits':'Six correlated questions cannot establish representative <=5% FPR.'},
 'expanded_dev':{'status':development['status'],'reason':development['reason'],'evaluated_positive_answers':4,'complete_supported_answers':2,
                 'not_supported':['dev:create_list:vi','dev:create_list:en'],
                 'support_reason':'Only unit identifier/name was selected; it does not establish the complete initial/order plus create/list and SQLite requirements.',
                 'stopping_warm_seconds':5.944,'warm_gate_seconds':5,'new_generation_requests':development['new_generation_requests'],
                 'negatives_evaluated_in_expanded_run':0,'representative_fpr':None},
 'citation_integrity':{'checked':checked,'hash_offset_native_id_version_errors':0,'scope':'Candidate source identity only; exact quote is not semantic support'},
 'main_semantic_e2e':'NOT_RUN_NO_QUALIFIED_CANDIDATE','locked_holdout':'NOT_CREATED_OR_SCORED_AFTER_FAILED_DEV_GATE','old_holdout_access':False,
 'main_rag_changed':False,'gemini_generation_calls':0,'this_continuation_local_4b_generation_requests':11,
 'next_required':'Fix complete-evidence/answerability and worst-case latency without changing gates, then freeze a broader source-reviewed benchmark; qualify before serving integration.'}
(OUT/'rag-final-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
