"""Synthetic-only local model smoke in a CPU/memory-capped networkless container."""
import hashlib,json,math,os,subprocess,time
from pathlib import Path

ROOT=Path(__file__).parent
PREVIOUS=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
WORK=ROOT/'synthetic-span-smoke';DATA=WORK/'input';OUTPUT=WORK/'output'
DATA.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(exist_ok=True)
fixtures=[
 ('en-book','How long can a reader borrow a book?','A reader may borrow a book for 14 days.','Readers can reserve books online.'),
 ('vi-book','Mượn sách được bao nhiêu ngày?','Độc giả có thể mượn sách trong 14 ngày.','Độc giả có thể đặt sách trực tuyến.'),
 ('en-sensor','When does the valve close?','The valve closes when pressure exceeds 80 psi.','The pump can deliver 80 litres per minute.'),
 ('vi-sensor','Van đóng khi nào?','Van đóng khi áp suất vượt quá 80 psi.','Bơm cung cấp 80 lít mỗi phút.')]
pairs=[{'id':f'{name}-{kind}','query':query,'passage':passage} for name,query,positive,negative in fixtures for kind,passage in [('positive',positive),('negative',negative)]]
(DATA/'pairs.json').write_text(json.dumps({'pairs':pairs},ensure_ascii=False),encoding='utf-8')
target=OUTPUT/'scores.json';assert not target.exists(),'PRESERVE_PREVIOUS_SMOKE_RESULT'
image='sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb'
mount=lambda source,destination,ro=False:['--mount',f'type=bind,source={source.resolve()},target={destination}'+(',readonly' if ro else '')]
cmd=['docker','run','--rm','--network','none','--cpus','1','--memory','768m']
cmd+=mount(PREVIOUS/'assets','/experiment/assets',True)+mount(PREVIOUS/'venv','/experiment/venv',True)
cmd+=mount(ROOT,'/src',True)+mount(DATA,'/data',True)+mount(OUTPUT,'/output')
cmd+=['--entrypoint','/experiment/venv/bin/python',image,'/src/span_reranker_offline.py']
begin=time.monotonic();run=subprocess.run(cmd,capture_output=True,timeout=120)
if run.returncode:raise RuntimeError('SYNTHETIC_CPU_SMOKE_FAILED: '+run.stderr.decode(errors='replace')[-800:])
result=json.loads(target.read_text(encoding='utf-8'));rows={r['id']:r for r in result['rows']};lat=sorted(r['seconds'] for r in rows.values())
checks={name:rows[name+'-positive']['score']>rows[name+'-negative']['score'] for name,_,_,_ in fixtures}
public={'model':result['model'],'revision':result['revision'],'runner_sha256':hashlib.sha256((ROOT/'span_reranker_offline.py').read_bytes()).hexdigest(),
        'elapsed_container_seconds':round(time.monotonic()-begin,3),'model_load_seconds':result['model_load_seconds'],
        'pair_p95_seconds':lat[math.ceil(.95*len(lat))-1],'peak_memory_bytes':result['cgroup_memory_peak'],
        'synthetic_pair_ordering':checks,'truncated':sum(r['truncated'] for r in rows.values()),
        'status':'SYNTHETIC_SMOKE_ONLY_NOT_RAG_ACCEPTANCE'}
(ROOT/'span-synthetic-smoke.json').write_text(json.dumps(public,indent=2)+'\n',encoding='utf-8');print(json.dumps(public))
