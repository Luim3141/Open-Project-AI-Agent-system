"""Dev-only deterministic calibration, then one locked holdout assessment."""
from datetime import datetime,timezone
import argparse,hashlib,json,math,os
from pathlib import Path
ROOT=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
OUT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('split',choices=['dev','holdout']);args=parser.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
data=json.loads((ROOT/f'{args.split}-candidates.json').read_text(encoding='utf-8'))
scores=json.loads((ROOT/f'{args.split}-scores.json').read_text(encoding='utf-8'))
scoremap={r['id']:r for r in scores['results']}
source=json.loads((ROOT/'source-snapshot.json').read_text(encoding='utf-8'))
docs={d['source_hash']:d for d in source['documents']}
chunks={(c['document_id'],c['chunk_index']):c for c in source['chunks']}
assert len(scoremap)==sum(len(r['pool']) for r in data['cases'])
rows=[]
for row in data['cases']:
    ranked=sorted([{**p,**scoremap[p['pair_id']]} for p in row['pool']],key=lambda p:(-p['score'],p['document_id'],p['chunk_index']))
    best={}
    for p in ranked:
        if p['document_id'] not in best:best[p['document_id']]=p
    rows.append({**row,'ranked':list(best.values()),'rerank_seconds':sum(scoremap[p['pair_id']]['seconds'] for p in row['pool'])})
def selected(row,cutoff):return [p for p in row['ranked'] if p['score']>=cutoff][:5]
def report(rows,cutoff=None,baseline=False):
    detailed=[]
    for row in rows:
        case=row['case'];hits=row['baseline'] if baseline else selected(row,cutoff);ids=[h['native_id'] for h in hits]
        rank=next((i+1 for i,native in enumerate(ids) if native in case['relevant_ids']),None)
        citation_identity_errors=0;chunk_support_checked=0;chunk_support_passed=0;truncated_support=0
        if not baseline:
            for hit in hits:
                d=docs[hit['document_id']];chunk=chunks[(hit['document_id'],hit['chunk_index'])]
                citation_identity_errors+=int(hit['chunk_hash']!=chunk['chunk_hash'] or json.loads(d['metadata'])['native_id']!=hit['native_id'])
                if hit['native_id'] in case['relevant_ids']:
                    chunk_support_checked+=1
                    support=(hit['chunk_hash'] in {s['chunk_hash'] for s in case['supporting_chunks']} or
                        case['evidence_literal'].casefold() in d['title'].casefold())
                    chunk_support_passed+=int(support)
                    # Tokenizer decoding preserves most literals; whitespace/escaped punctuation can differ.
                    if support and hit['truncated'] and case['evidence_literal'].casefold() not in hit['visible_text'].casefold():truncated_support+=1
        seconds=row['embedding_seconds']+(row['baseline_retrieval_seconds'] if baseline else row['candidate_retrieval_seconds']+row['rerank_seconds'])
        detailed.append({'query':case['query'],'language':case['language'],'kind':case['kind'],'intent':case['intent'],
            'exact_case':'exact' in case['intent'],
            'ids':ids,'rank':rank,'recall5':len(set(ids)&set(case['relevant_ids']))/max(1,len(case['relevant_ids'])),
            'result_judgments':['relevant' if n in case['relevant_ids'] else 'partial' if n in case['partial_ids'] else 'irrelevant' for n in ids],
            'seconds':seconds,'citation_identity_errors':citation_identity_errors,'relevant_chunk_support_checked':chunk_support_checked,
            'relevant_chunk_support_passed':chunk_support_passed,'support_literal_missing_after_truncation':truncated_support,
            'hits':[{'document_id':h['document_id'],'native_id':h['native_id'],**({k:h[k] for k in ['chunk_index','chunk_hash','score','tokens','truncated']} if not baseline else {})} for h in hits]})
    def aggregate(items):
        pos=[r for r in items if r['kind']=='positive'];neg=[r for r in items if r['kind']=='negative'];lat=sorted(r['seconds'] for r in items)
        return {'positive':len(pos),'negative':len(neg),'hit1':sum(r['rank']==1 for r in pos),'hit5':sum(r['rank'] is not None for r in pos),
            'mrr5':sum(1/r['rank'] for r in pos if r['rank'])/len(pos),'recall5':sum(r['recall5'] for r in pos)/len(pos),
            'negative_returned':sum(bool(r['ids']) for r in neg),'abstention_correct':sum(not r['ids'] for r in neg),
            'exact_cases':sum(r['exact_case'] for r in pos),'exact_hit1':sum(r['exact_case'] and r['rank']==1 for r in pos),
            'p50_seconds':lat[len(lat)//2],'p95_seconds':lat[math.ceil(.95*len(lat))-1],
            'citation_identity_errors':sum(r['citation_identity_errors'] for r in items),
            'relevant_chunk_support_checked':sum(r['relevant_chunk_support_checked'] for r in items),
            'relevant_chunk_support_passed':sum(r['relevant_chunk_support_passed'] for r in items),
            'support_literal_missing_after_truncation':sum(r['support_literal_missing_after_truncation'] for r in items)}
    return {'metrics':{lang:aggregate([r for r in detailed if lang=='all' or r['language']==lang]) for lang in ['vi','en','all']},'cases':detailed}
baseline=report(rows,baseline=True)
if args.split=='dev':
    cutoffs=sorted({p['score'] for r in rows for p in r['ranked']})
    options=[];maxneg=min(1,baseline['metrics']['all']['negative_returned'])
    for cutoff in cutoffs:
        result=report(rows,cutoff)['metrics']['all']
        if result['negative_returned']<=maxneg:options.append((result['hit5'],result['mrr5'],cutoff))
    assert options
    cutoff=max(options)[2];candidate=report(rows,cutoff)
    lock={'locked_utc':datetime.now(timezone.utc).isoformat(),'cutoff':cutoff,'calibration_rule':'minimize negative risk<=paired baseline and<=5%; maximize hit5 then MRR then higher cutoff',
        'dev_labels_sha256':sha(ROOT/'labels-frozen.json'),'candidate_script_sha256':sha(OUT/'reranker_candidates.py'),
        'offline_script_sha256':sha(OUT/'reranker_offline.py'),'evaluation_script_sha256':sha(Path(__file__)),
        'dev_scores_sha256':sha(ROOT/'dev-scores.json'),'candidate_pool':'raw dense40 + lexical10 expanded cap60; retain first2 dense-ranked chunks per document, title+originalchunk,512tokens'}
    (ROOT/'calibration-lock.json').write_text(json.dumps(lock,indent=2))
else:
    lock=json.loads((ROOT/'calibration-lock.json').read_text());cutoff=lock['cutoff']
    assert lock['candidate_script_sha256']==sha(OUT/'reranker_candidates.py') and lock['offline_script_sha256']==sha(OUT/'reranker_offline.py') and lock['evaluation_script_sha256']==sha(Path(__file__))
    candidate=report(rows,cutoff)
b=baseline['metrics']['all'];c=candidate['metrics']['all']
gates={'hit5_plus10pp':c['hit5']/c['positive']-b['hit5']/b['positive']>=.1,
    'hit1_not_decreased':c['hit1']>=b['hit1'],'mrr_not_decreased':c['mrr5']>=b['mrr5'],
    'each_language_hit5_not_decreased':all(candidate['metrics'][l]['hit5']>=baseline['metrics'][l]['hit5'] for l in ['vi','en']),
    'negative_not_increased_and_at_most5pct':c['negative_returned']<=b['negative_returned'] and c['negative_returned']/c['negative']<=.05,
    'warm_p95_at_most5seconds':c['p95_seconds']<=5,'memory_at_most768MiB':scores['cgroup_memory_peak']<=768*1024*1024,
    'citation_identity_zero':c['citation_identity_errors']==0,
    'exact_top1_no_regression':all(not (r['exact_case'] and r['rank']==1) or candidate['cases'][i]['rank']==1 for i,r in enumerate(baseline['cases'])),
    'source_chunk_support':c['relevant_chunk_support_checked']==c['relevant_chunk_support_passed'],
    'no_support_literal_lost_to_truncation':c['support_literal_missing_after_truncation']==0}
result={'utc':datetime.now(timezone.utc).isoformat(),'split':args.split,'cutoff':cutoff,'gates':gates,'numeric_pass':all(gates.values()),
    'runtime':{k:v for k,v in scores.items() if k!='results'},'lock':lock,'baseline':baseline,'candidate':candidate,
    'stale_positive_cases_excluded':len(data['stale_snapshot_cases_excluded_before_any_scoring']),
    'limits':'Agent labels humanPENDING; copied scoped vector exact-search fixture; latency includes Python per-pair session.run time + measured embedding/retrieval, excludes model cold load; no Main/source deployment'}
(ROOT/f'{args.split}-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
public={**result,'baseline':baseline['metrics'],'candidate':candidate['metrics']}
(OUT/f'reranker-{args.split}-summary.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(public,ensure_ascii=False,indent=2))
