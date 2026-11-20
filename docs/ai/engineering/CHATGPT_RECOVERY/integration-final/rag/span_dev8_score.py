"""Capped relevance-only post-hoc DEV experiment, never an answerability gate."""
import datetime,hashlib,json,math,os,subprocess,time
from pathlib import Path

ROOT=Path(__file__).parent;EVAL=ROOT/'eval'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev/span-reranker8'
PREVIOUS=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
plan=json.loads((EVAL/'evaluation-plan.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((EVAL/'dev.json').read_bytes())==plan['dev_sha256']
cases=json.loads((EVAL/'dev.json').read_text(encoding='utf-8'))['cases']
data=json.loads((PRIVATE/'pairs.json').read_text(encoding='utf-8'))['pairs'];meta=json.loads((PRIVATE/'candidates.json').read_text())
assert meta['dev_sha256']==plan['dev_sha256'] and meta['selector_sha256']==sha((ROOT/'span_selection.py').read_bytes())
byid={x['id']:x for x in data};assert len(byid)==len(data) and len(cases)==len(meta['metadata'])
assert not (ROOT/'span-dev8-relevance.json').exists(),'PRESERVE_EXISTING_RESULT'

def mount(source,target,ro=False):return ['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly' if ro else '')]
def score_batch(index,rows):
    base=PRIVATE/('batch-'+str(index));inp=base/'input';out=base/'output';inp.mkdir(parents=True,exist_ok=False);out.mkdir()
    selected=[byid[c['pair_id']] for row in rows for c in row['candidates']];sizes=[len(row['candidates']) for row in rows]
    if not selected:return {'rows':[],'model_load_seconds':0,'cgroup_memory_peak':0,'container_wall_seconds':0}
    assert len(selected)<=400
    (inp/'pairs.json').write_text(json.dumps({'pairs':selected,'group_sizes':sizes},ensure_ascii=False),encoding='utf-8')
    cmd=['docker','run','--rm','--network','none','--cpus','1','--memory','768m']
    cmd+=mount(PREVIOUS/'assets','/experiment/assets',True)+mount(PREVIOUS/'venv','/experiment/venv',True)
    cmd+=mount(ROOT,'/src',True)+mount(inp,'/data',True)+mount(out,'/output')
    cmd+=['--entrypoint','/experiment/venv/bin/python','sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb','/src/span_reranker_offline.py']
    start=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=120);wall=time.monotonic()-start
    if p.returncode:raise RuntimeError('BOUNDED_DEV_SCORER_FAILED: '+p.stderr.decode(errors='replace')[-500:])
    result=json.loads((out/'scores.json').read_text());result['container_wall_seconds']=round(wall,3);return result

rows=meta['metadata'];batches=[rows[:3]];current=[];size=0
for row in rows[3:]:
    n=len(row['candidates'])
    if current and size+n>350:batches.append(current);current=[];size=0
    current.append(row);size+=n
if current:batches.append(current)
scores={};reports=[];status='DEV_RELEVANCE_ONLY_NOT_DEPLOYABLE';pilot=[]
for index,batch in enumerate(batches):
    report=score_batch(index,batch);reports.append({k:v for k,v in report.items() if k not in ('rows','group_seconds')})
    scores.update({r['id']:r for r in report['rows']})
    times=[row['embedding_and_retrieval_seconds']+row['selection_seconds']+sum(scores[c['pair_id']]['seconds'] for c in row['candidates']) for row in batch]
    if index==0:pilot=times
    # The first cached embedding includes the known cold load; subsequent cases are the warm budget probe.
    warm=times[1:] if index==0 else times
    if warm and max(warm)>5:status='STOPPED_WARM_QUERY_OVER_5_SECONDS';break
base={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'dev_sha256':plan['dev_sha256'],
      'selector_sha256':meta['selector_sha256'],'prepare_sha256':sha((ROOT/'span_dev8_prepare.py').read_bytes()),
      'scorer_sha256':sha((ROOT/'span_reranker_offline.py').read_bytes()),'cached_retrieval_sha256':meta['prior_metadata_sha256'],
      'pairs_total':len(data),'pairs_scored':len(scores),'pilot_query_seconds':pilot,'batches':reports,
      'limitations':['post-hoc DEV, documents and cases previously observed','BGE/Qdrant retrieval reused verified frozen snapshot',
                     'latency sums separate measured embedding/retrieval+selection+per-pair inference; excludes production per-query IPC/concurrency',
                     'relevance scores are not answerability or absence proof; negative candidates are not FPR',
                     'no live ACL/freshness/deletion or independent label review','no holdout access']}
if status=='DEV_RELEVANCE_ONLY_NOT_DEPLOYABLE':
    assert set(scores)==set(byid);detailed=[]
    for case,row in zip(cases,rows):
        assert case['id']==row['case'];ranked=sorted(row['candidates'],key=lambda x:-scores[x['pair_id']]['score']);hits=[]
        for c in ranked:
            if scores[c['pair_id']]['truncated']:continue
            if c['native_id'] not in [h['native_id'] for h in hits]:hits.append(c)
            if len(hits)==5:break
        rank=next((i+1 for i,h in enumerate(hits) if h['native_id'] in case['relevant_ids']),None)
        start=case.get('support_offset',-1);end=start+len(case.get('support_literal',''))
        support=any(h['native_id'] in case['relevant_ids'] and h['start']<=start and h['end']>=end for h in hits)
        in_pool=any(h['native_id'] in case['relevant_ids'] and h['start']<=start and h['end']>=end for h in row['candidates'])
        elapsed=row['embedding_and_retrieval_seconds']+row['selection_seconds']+sum(scores[c['pair_id']]['seconds'] for c in row['candidates'])
        detailed.append({'case':case['id'],'kind':case['kind'],'rank':rank,'support_contained':support,'support_in_pool':in_pool,
                         'ids':[h['native_id'] for h in hits],'seconds':round(elapsed,4)})
    pos=[r for r in detailed if r['kind']=='positive'];neg=[r for r in detailed if r['kind']=='negative'];times=sorted(r['seconds'] for r in detailed[1:])
    base.update(positive=len(pos),negative=len(neg),document_hit5=sum(r['rank'] is not None for r in pos),
                support_in_pool=sum(r['support_in_pool'] for r in pos),support_span_hit5=sum(r['support_contained'] for r in pos),
                negative_with_any_candidate=sum(bool(r['ids']) for r in neg),warm_p95_lower_bound_seconds=times[math.ceil(.95*len(times))-1],
                cold_first_query_lower_bound_seconds=detailed[0]['seconds'],peak_memory_bytes=max(r['cgroup_memory_peak'] for r in reports),
                container_wall_total_seconds=round(sum(r['container_wall_seconds'] for r in reports),3),
                truncated_pairs=sum(r['truncated'] for r in scores.values()),rows=detailed)
target=ROOT/'span-dev8-relevance.json';target.write_text(json.dumps(base,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in base.items() if k not in ('rows','batches')}))
