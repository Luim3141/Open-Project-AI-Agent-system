"""Calibrate only dev; one immutable file-clause holdout with strict evidence-span metrics."""
import argparse,hashlib,json,math,os,re
from pathlib import Path
from datetime import datetime,timezone
from clause_experiment import normalize
P=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-evidence-clauses';OUT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('split',choices=['dev','holdout']);args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((P/f'{args.split}-candidates.json').read_text(encoding='utf-8'));scores=json.loads((P/f'{args.split}-scores.json').read_text(encoding='utf-8'))
manifest=json.loads((P/'source-manifest.json').read_text());sources={s['source_key']:s for s in manifest['sources']};scoremap={s['id']:s for s in scores['results']}
source_texts={key:Path(s['copy']).read_bytes().decode('utf-8-sig') for key,s in sources.items()}
rows=[]
for row in data['cases']:
    ranked=sorted([{**p,**scoremap[p['pair_id']]} for p in row['pool']],key=lambda p:(-p['score'],p['source_key'],p['start']))
    rows.append({**row,'ranked':ranked,'rerank_seconds':sum(s['seconds'] for s in ranked)})
def compact(value):return re.sub(r'\W+','',normalize(value))
def supported(case,hit):
    return hit['source_key'] in case['relevant_sources'] and any(hit['start']==s['start'] and hit['end']==s['end'] and hit['sha256']==s['sha256'] for s in case['supporting_spans'])
def report(cutoff=0,coverage=0,baseline=False):
    details=[]
    for row in rows:
        case=row['case']
        hits=row['baseline'] if baseline else [p for p in row['ranked'] if p['score']>=cutoff and p['content_coverage']>=coverage and p['constraints_supported']][:5]
        docrank=next((i+1 for i,h in enumerate(hits) if h['source_key'] in case['relevant_sources']),None)
        is_supported=lambda h:(h['source_key'] in case['relevant_sources'] and compact(case['support_literal']) in compact(h['snippet'])) if baseline else supported(case,h)
        rank=next((i+1 for i,h in enumerate(hits) if case['kind']=='positive' and is_supported(h)),None)
        identities=0;truncated=0;wrongspan=0
        if not baseline:
            for h in hits:
                s=sources[h['source_key']];text=source_texts[h['source_key']];literal=text[h['start']:h['end']]
                identities+=int(h['source_revision']!=s['source_revision'] or h['raw_file_sha256']!=s['raw_sha256'] or hashlib.sha256(literal.encode()).hexdigest()!=h['sha256'])
                if case['kind']=='positive' and h['source_key'] in case['relevant_sources']:
                    wrongspan+=int(not supported(case,h))
                    truncated+=int(supported(case,h) and h['truncated'] and compact(case['support_literal']) not in compact(h['visible_text']))
        details.append({'query':case['query'],'intent':case['intent'],'kind':case['kind'],'language':case['language'],
            'evidence_rank':rank,'document_rank':docrank,'has_results':bool(hits),'sources':[h['source_key'] for h in hits],
            'seconds':row['embedding_seconds']+(row['baseline_retrieval_seconds'] if baseline else row['candidate_retrieval_seconds']+row['rerank_seconds']),
            'identity_errors':identities,'wrong_frozen_support_spans':wrongspan,'truncated_support':truncated,
            'hits':[{k:v for k,v in h.items() if k not in ('visible_text','seconds')} for h in hits]})
    def aggregate(items):
        pos=[r for r in items if r['kind']=='positive'];neg=[r for r in items if r['kind']=='negative'];times=sorted(r['seconds'] for r in items)
        return {'positive':len(pos),'negative':len(neg),'evidence_hit1':sum(r['evidence_rank']==1 for r in pos),'evidence_hit5':sum(bool(r['evidence_rank']) for r in pos),
            'evidence_mrr5':sum(1/r['evidence_rank'] for r in pos if r['evidence_rank'])/len(pos),'evidence_recall5':sum(bool(r['evidence_rank']) for r in pos)/len(pos),
            'document_hit1':sum(r['document_rank']==1 for r in pos),'document_hit5':sum(bool(r['document_rank']) for r in pos),
            'negative_returned':sum(r['has_results'] for r in neg),'abstention_correct':sum(not r['has_results'] for r in neg),
            'identity_errors':sum(r['identity_errors'] for r in items),'wrong_frozen_support_spans':sum(r['wrong_frozen_support_spans'] for r in items),
            'truncated_support':sum(r['truncated_support'] for r in items),'p50_seconds':times[len(times)//2],'p95_seconds':times[math.ceil(.95*len(times))-1]}
    return {'metrics':{lang:aggregate([r for r in details if lang=='all' or r['language']==lang]) for lang in ['vi','en','all']},'cases':details}
baseline=report(baseline=True)
if args.split=='dev':
    candidates=[];maxneg=min(1,baseline['metrics']['all']['negative_returned'])
    for coverage in [0.05,0.1,0.15,0.2,0.3,0.4]:
        for cutoff in sorted({s['score'] for r in rows for s in r['ranked']})+[100.0]:
            metrics=report(cutoff,coverage)['metrics']['all']
            if metrics['negative_returned']<=maxneg and metrics['truncated_support']==0:
                candidates.append((metrics['evidence_hit5'],metrics['evidence_mrr5'],-metrics['wrong_frozen_support_spans'],coverage,cutoff))
    assert candidates
    choice=max(candidates);coverage,cutoff=choice[-2:]
    lock={'utc':datetime.now(timezone.utc).isoformat(),'cutoff':cutoff,'coverage':coverage,'labels_sha256':sha(P/'labels-frozen.json'),
        'code_sha256':{n:sha(OUT/n) for n in ['clause_experiment.py','clause_candidates.py','clause_evaluate.py','reranker_offline.py']},
        'selection':'dev only; negatives<=paired baseline and<=5%,no support truncation; maximize strict evidence H5,MRR,then fewer wrong proxy spans,higher coverage/cutoff'}
    (P/'calibration-lock.json').write_text(json.dumps(lock,indent=2))
else:
    lock=json.loads((P/'calibration-lock.json').read_text());assert lock['labels_sha256']==sha(P/'labels-frozen.json')
    assert all(sha(OUT/n)==h for n,h in lock['code_sha256'].items());cutoff,coverage=lock['cutoff'],lock['coverage']
candidate=report(cutoff,coverage);b=baseline['metrics']['all'];c=candidate['metrics']['all']
gates={'evidence_hit5_plus10pp':c['evidence_hit5']/c['positive']-b['evidence_hit5']/b['positive']>=.1,
    'evidence_hit5_at_least_two_thirds':c['evidence_hit5']/c['positive']>=2/3,
    'evidence_hit1_nonregression':c['evidence_hit1']>=b['evidence_hit1'],'evidence_mrr_nonregression':c['evidence_mrr5']>=b['evidence_mrr5'],
    'document_hit1_and_hit5_nonregression':c['document_hit1']>=b['document_hit1'] and c['document_hit5']>=b['document_hit5'],
    'per_language_evidence_hit5_nonregression':all(candidate['metrics'][l]['evidence_hit5']>=baseline['metrics'][l]['evidence_hit5'] for l in ['vi','en']),
    'negative_not_increased_at_most5pct':c['negative_returned']<=b['negative_returned'] and c['negative_returned']/c['negative']<=.05,
    'citation_identity_zero':c['identity_errors']==0,'no_support_lost_to_truncation':c['truncated_support']==0,
    'warm_p95_within5s':c['p95_seconds']<=5,'memory_within768MiB':scores['cgroup_memory_peak']<=768*1024*1024,
    'acl_scope_selfchecks':all(data['scope_checks'].values())}
result={'utc':datetime.now(timezone.utc).isoformat(),'split':args.split,'scope':'repo-file-only; not Native RAG acceptance; humanPENDING',
    'lock':lock,'gates':gates,'passed':all(gates.values()),'baseline':baseline,'candidate':candidate,'runtime':{k:v for k,v in scores.items() if k!='results'},
    'limits':'Strict literal span judgments not human semantic adjudication; baseline evidence proxy uses its returned snippet; document-level metrics separately reported.'}
(P/f'{args.split}-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
public={**result,'baseline':baseline['metrics'],'candidate':candidate['metrics']};(OUT/f'clause-{args.split}-summary.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(public,ensure_ascii=False,indent=2))
