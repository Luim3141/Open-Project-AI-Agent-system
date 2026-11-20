"""Bounded relevance-only DEV experiment; abstention and live security gates are not established."""
import datetime,hashlib,json,math,os,subprocess,time
from pathlib import Path

ROOT=Path(__file__).parent;EVAL=ROOT/'eval'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev/span-reranker'
PREVIOUS=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
data=json.loads((PRIVATE/'pairs.json').read_text(encoding='utf-8'));metadata=json.loads((PRIVATE/'candidates.json').read_text())
cases=json.loads((EVAL/'dev.json').read_text(encoding='utf-8'))['cases'];plan=json.loads((EVAL/'evaluation-plan.json').read_text())
assert hashlib.sha256((EVAL/'dev.json').read_bytes()).hexdigest()==plan['dev_sha256']==metadata['dev_sha256']
assert len(cases)==len(metadata['metadata'])
assert not (ROOT/'span-dev-relevance.json').exists(),'PRESERVE_PREVIOUS_DEV_RESULT'
by_id={p['id']:p for p in data['pairs']};assert len(by_id)==len(data['pairs'])
image='sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb'
def mount(source,target,ro=False):return ['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly' if ro else '')]
def score_batch(label,items):
    base=PRIVATE/label;inp=base/'input';out=base/'output';inp.mkdir(parents=True,exist_ok=False);out.mkdir()
    (inp/'pairs.json').write_text(json.dumps({'pairs':items},ensure_ascii=False),encoding='utf-8')
    cmd=['docker','run','--rm','--network','none','--cpus','1','--memory','768m']
    cmd+=mount(PREVIOUS/'assets','/experiment/assets',True)+mount(PREVIOUS/'venv','/experiment/venv',True)
    cmd+=mount(ROOT,'/src',True)+mount(inp,'/data',True)+mount(out,'/output')
    cmd+=['--entrypoint','/experiment/venv/bin/python',image,'/src/span_reranker_offline.py']
    started=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=300)
    if p.returncode:raise RuntimeError('SPAN_DEV_SCORER_FAILED: '+p.stderr.decode(errors='replace')[-400:])
    value=json.loads((out/'scores.json').read_text(encoding='utf-8'));value['container_wall_seconds']=round(time.monotonic()-started,3)
    return value
pilot=metadata['metadata'][:3];pilot_ids={c['pair_id'] for m in pilot for c in m['candidates']}
assert pilot_ids
first=score_batch('pilot',[p for p in data['pairs'] if p['id'] in pilot_ids])
scores={r['id']:r for r in first['rows']};assert scores.keys()==pilot_ids
pilot_times=[m['embedding_and_retrieval_seconds']+sum(scores[c['pair_id']]['seconds'] for c in m['candidates']) for m in pilot]
common={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dev_sha256':plan['dev_sha256'],
        'source_hash':hashlib.sha256((ROOT/'source_spans.py').read_bytes()).hexdigest(),
        'prepare_hash':hashlib.sha256((ROOT/'span_dev_prepare.py').read_bytes()).hexdigest(),
        'scorer_hash':hashlib.sha256((ROOT/'span_reranker_offline.py').read_bytes()).hexdigest(),
        'pilot_query_seconds':pilot_times,'pilot_container_wall_seconds':first['container_wall_seconds'],
        'pilot_model_load_seconds':first['model_load_seconds'],'pilot_peak_memory':first['cgroup_memory_peak'],
        'warm_latency_limitations':'embedding+Qdrant wall and ONNX per-pair execution, excludes cross-process IPC and production concurrency',
        'interpretation':'unthresholded relevance-only DEV; no answerability, ACL or human acceptance claim'}
if max(pilot_times)>5:
    result={**common,'status':'STOPPED_PILOT_OVER_5_SECONDS'}
else:
    rest=[p for p in data['pairs'] if p['id'] not in pilot_ids]
    second=score_batch('remaining',rest) if rest else None
    if second:scores.update({r['id']:r for r in second['rows']})
    assert set(scores)==set(by_id)
    rows=[]
    for case,m in zip(cases,metadata['metadata']):
        assert case['id']==m['case'];candidates=sorted(m['candidates'],key=lambda c:-scores[c['pair_id']]['score'])
        hits=[]
        for c in candidates:
            score=scores[c['pair_id']]
            if score['truncated']:continue
            if c['native_id'] not in [h['native_id'] for h in hits]:hits.append({**c,'score':score['score']})
            if len(hits)==5:break
        rank=next((i+1 for i,h in enumerate(hits) if h['native_id'] in case['relevant_ids']),None)
        support=any(h['native_id'] in case['relevant_ids'] and h['start']<=case.get('support_offset',-1)
                    and h['end']>=case.get('support_offset',-1)+len(case.get('support_literal','')) for h in hits)
        elapsed=m['embedding_and_retrieval_seconds']+sum(scores[c['pair_id']]['seconds'] for c in m['candidates'])
        rows.append({'case':case['id'],'kind':case['kind'],'rank':rank,'support_contained':support,
                     'ids':[h['native_id'] for h in hits],'seconds':round(elapsed,4)})
    positive=[r for r in rows if r['kind']=='positive'];negative=[r for r in rows if r['kind']=='negative'];times=sorted(r['seconds'] for r in rows)
    result={**common,'status':'DEV_RELEVANCE_ONLY_NOT_DEPLOYABLE','positive':len(positive),'negative':len(negative),
        'document_hit5':sum(r['rank'] is not None for r in positive),'support_span_hit5':sum(r['support_contained'] for r in positive),
        'negative_with_any_candidate':sum(bool(r['ids']) for r in negative),'p95_lower_bound_seconds':times[math.ceil(.95*len(times))-1],
        'truncated_pairs':sum(r['truncated'] for r in scores.values()),'rows':rows,
        'remaining_container_wall_seconds':second['container_wall_seconds'] if second else 0,
        'remaining_model_load_seconds':second['model_load_seconds'] if second else 0,
        'peak_memory_bytes':max(first['cgroup_memory_peak'],second['cgroup_memory_peak'] if second else 0)}
(ROOT/'span-dev-relevance.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
