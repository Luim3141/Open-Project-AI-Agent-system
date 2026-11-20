"""Resume unchanged DEV pairs after cold BGE pilot; warm scoring only, no answerability claim."""
import datetime,hashlib,json,math,os,subprocess,time
from pathlib import Path

ROOT=Path(__file__).parent;EVAL=ROOT/'eval'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev/span-reranker'
PREVIOUS=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
old=json.loads((ROOT/'span-dev-relevance.json').read_text());assert old['status']=='STOPPED_PILOT_OVER_5_SECONDS'
assert old['pilot_query_seconds'][0]>5 and max(old['pilot_query_seconds'][1:])<5
assert hashlib.sha256((ROOT/'span_dev_prepare.py').read_bytes()).hexdigest()==old['prepare_hash']
assert hashlib.sha256((ROOT/'source_spans.py').read_bytes()).hexdigest()==old['source_hash']
plan=json.loads((EVAL/'evaluation-plan.json').read_text());assert plan['dev_sha256']==old['dev_sha256']
cases=json.loads((EVAL/'dev.json').read_text(encoding='utf-8'))['cases'];metadata=json.loads((PRIVATE/'candidates.json').read_text())['metadata']
pairs=json.loads((PRIVATE/'pairs.json').read_text(encoding='utf-8'))['pairs'];by_id={r['id']:r for r in pairs}
assert len(metadata)==len(cases) and len(by_id)==len(pairs)
destination=PRIVATE/'warm';inp=destination/'input';out=destination/'output';inp.mkdir(parents=True,exist_ok=False);out.mkdir()
groups=[len(m['candidates']) for m in metadata];ordered=[by_id[c['pair_id']] for m in metadata for c in m['candidates']]
assert len(ordered)==len(pairs) and all(cases[i]['id']==m['case'] for i,m in enumerate(metadata))
(inp/'pairs.json').write_text(json.dumps({'pairs':ordered,'group_sizes':groups},ensure_ascii=False),encoding='utf-8')
mount=lambda source,target,ro=False:['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly' if ro else '')]
cmd=['docker','run','--rm','--network','none','--cpus','1','--memory','768m']
cmd+=mount(PREVIOUS/'assets','/experiment/assets',True)+mount(PREVIOUS/'venv','/experiment/venv',True)
cmd+=mount(ROOT,'/src',True)+mount(inp,'/data',True)+mount(out,'/output')
cmd+=['--entrypoint','/experiment/venv/bin/python','sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb','/src/span_reranker_offline.py']
started=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=120);container_wall=time.monotonic()-started
if p.returncode:raise RuntimeError('WARM_SCORING_FAILED: '+p.stderr.decode(errors='replace')[-500:])
scored=json.loads((out/'scores.json').read_text());scores={r['id']:r for r in scored['rows']};assert set(scores)==set(by_id)
rows=[]
for case,m in zip(cases,metadata):
    ranked=sorted(m['candidates'],key=lambda x:-scores[x['pair_id']]['score']);hits=[]
    for c in ranked:
        if scores[c['pair_id']]['truncated']:continue
        if c['native_id'] not in [h['native_id'] for h in hits]:hits.append(c)
        if len(hits)==5:break
    rank=next((i+1 for i,h in enumerate(hits) if h['native_id'] in case['relevant_ids']),None)
    support=any(h['native_id'] in case['relevant_ids'] and h['start']<=case.get('support_offset',-1)
                and h['end']>=case.get('support_offset',-1)+len(case.get('support_literal','')) for h in hits)
    rows.append({'case':case['id'],'kind':case['kind'],'rank':rank,'support_contained':support,
                 'ids':[h['native_id'] for h in hits],
                 'seconds':round(m['embedding_and_retrieval_seconds']+sum(scores[c['pair_id']]['seconds'] for c in m['candidates']),4)})
positive=[r for r in rows if r['kind']=='positive'];negative=[r for r in rows if r['kind']=='negative']
times=sorted(r['seconds'] for r in rows[1:]);warm_p95=times[math.ceil(.95*len(times))-1]
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DEV_RELEVANCE_ONLY_NOT_DEPLOYABLE',
        'dev_sha256':plan['dev_sha256'],'extractor_sha256':old['source_hash'],'prepare_sha256':old['prepare_hash'],
        'scorer_sha256':hashlib.sha256((ROOT/'span_reranker_offline.py').read_bytes()).hexdigest(),
        'positive':len(positive),'negative':len(negative),'document_hit5':sum(r['rank'] is not None for r in positive),
        'support_span_hit5':sum(r['support_contained'] for r in positive),'negative_with_any_candidate':sum(bool(r['ids']) for r in negative),
        'warm_query_p95_lower_bound_seconds':warm_p95,'cold_query_lower_bound_seconds':rows[0]['seconds'],
        'scorer_cold_load_seconds':scored['model_load_seconds'],'container_wall_seconds':round(container_wall,3),
        'serialized_container_overhead_seconds':round(max(0,container_wall-sum(r['seconds'] for r in scored['rows'])),3),
        'serialized_scoring_average_wall_with_container_startup_seconds':round(container_wall/len(rows),3),
        'peak_memory_bytes':scored['cgroup_memory_peak'],'truncated_pairs':sum(r['truncated'] for r in scores.values()),
        'limitations':['non-concurrent separate embedding/retrieval and scorer execution; summed per pair excludes production IPC and end-to-end wall',
                       'candidate relevance is not answer support; all negatives are expected to retrieve candidates',
                       'no live ACL/freshness/deletion or independent label adjudication','no holdout access'],
        'rows':rows}
target=ROOT/'span-dev-warm.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
