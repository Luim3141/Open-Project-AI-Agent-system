"""One frozen observed-DEV run; reuse identical pilot replies, never open old holdout."""
import datetime,hashlib,json,os,sys,time,urllib.request
from pathlib import Path
OUT=Path(__file__).parent;RAG=OUT.parent/'integration-final/rag';ROOT=OUT.resolve().parents[4]
sys.path[:0]=[str(RAG),str(ROOT/'openproject/ai')]
from fact_candidate import FactCandidate
from gateway.vector_client import VectorClient
from evidence_validation import capture_response
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
work=private/'semantic-fact-dev';assert not work.exists(),'DEV_INTENT_EXISTS_RECONCILE_NO_REPLAY'
pilot=private/'fact-selector-semantic';freeze=json.loads((pilot/'freeze.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
for name,digest in freeze['code_sha256'].items():
    if name!='fact_selector_pilot.py':assert sha((RAG/name).read_bytes())==digest,'PILOT_SOURCE_CHANGED'
source=private/'native-candidate-canonical.json';assert sha(source.read_bytes())==freeze['snapshot_sha256']
records=json.loads(source.read_text(encoding='utf-8'))['documents'];active={r['metadata']['native_id']:{'lock_version':r['metadata']['lock_version'],'document_id':r['document_id']} for r in records}
engine=FactCandidate(records,project_id=6,source_actor=20,role='PM',current_sources=active)
cases=json.loads((RAG/'eval/dev.json').read_text(encoding='utf-8'))['cases']
old_cases=json.loads((pilot/'cases.json').read_text(encoding='utf-8'));old_packets=json.loads((pilot/'packets.json').read_text(encoding='utf-8'))
cached={c['query']:(p,json.loads((pilot/f'answer-{i}.json').read_text(encoding='utf-8'))) for i,(c,p) in enumerate(zip(old_cases,old_packets,strict=True))}
work.mkdir();plan={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FROZEN_OBSERVED_DEV_NOT_ACCEPTANCE',
 'cases_sha256':sha((RAG/'eval/dev.json').read_bytes()),'pilot_freeze_sha256':sha((pilot/'freeze.json').read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),
 'max_generation_requests':len(cases)-sum(c['query'] in cached for c in cases),'warm_seconds':5,'max_generation_seconds':150,
 'gates':{'retrieval_hit_at_5':.8,'negative_answer_emission_rate':.05,'semantic_support':'SOURCE_REVIEW_REQUIRED_EVERY_EMITTED_ANSWER'},
 'holdout_access':False,'human_ground_truth':False,'main_rag_changed':False}
(OUT/'semantic-fact-dev-freeze.json').write_text(json.dumps(plan,indent=2)+'\n');(work/'runner-frozen.py').write_bytes(Path(__file__).read_bytes())
rows=[];responses=[];result={**plan,'rows':rows,'status':'RUNNING'};calls=0;generation_seconds=0
def ollama(path,payload):
    req=urllib.request.Request('http://127.0.0.1:11434/api/'+path,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
try:
    vector=VectorClient(collection_name='qldapm_autonomous_fact_pilot_v2',timeout=60)
    queries=[c['query'] for c in cases if c['query'] not in cached]
    embeddings=iter(vector.embed_texts(queries));packets={}
    for case in cases:
        query=case['query']
        if query in cached:packets[query]=cached[query][0];continue
        body={'vector':next(embeddings),'limit':15,'with_payload':True,'filter':{'must':[{'key':'project_id','match':{'value':6}},{'key':'actor_id','match':{'value':20}},{'key':'allowed_roles','match':{'value':'PM'}}]}}
        response=vector._http.post(vector.qdrant_url+'/collections/'+vector.collection_name+'/points/search',json=body);response.raise_for_status()
        packets[query]=engine.semantic_packet(query,[],response.json()['result'])
    (work/'packets.json').write_text(json.dumps(packets,ensure_ascii=False),encoding='utf-8')
    ollama('embed',{'model':'bge-m3','input':'','keep_alive':0})
    for index,case in enumerate(cases):
        query=case['query'];packet=packets[query];reuse=query in cached;seconds=None;meta={}
        if reuse:answer=cached[query][1]
        else:
            payload={'model':'qwen3:4b','stream':False,'think':False,'keep_alive':'1m','format':freeze['schema'],'options':freeze['options'],
                     'messages':[{'role':'system','content':freeze['system']},{'role':'user','content':json.dumps(engine.model_input(packet),ensure_ascii=False,separators=(',',':'))}]}
            (work/f'request-{index}.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
            begin=time.monotonic();calls+=1;reply=ollama('chat',payload);seconds=time.monotonic()-begin;generation_seconds+=seconds
            capture_response(reply,work/f'response-{index}.json');answer=engine.render(packet,json.loads(reply['message']['content']))
            meta={'prompt_tokens':reply.get('prompt_eval_count'),'done_reason':reply.get('done_reason'),'model_load_seconds':(reply.get('load_duration') or 0)/1e9}
        rows.append({'case':case['id'],'kind':case['kind'],'retrieval_hit':bool(set(case['relevant_ids'])&set(packet['retrieved_native_ids'])),
                     'retrieved_ids':packet['retrieved_native_ids'],'answer_emitted':answer['answer'] is not None,'reuse_pilot_response':reuse,'seconds':None if seconds is None else round(seconds,3),**meta})
        responses.append({'case':case,'answer':answer})
        (OUT/'semantic-fact-dev-result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(rows[-1]),flush=True)
        if not reuse:
            if reply.get('done_reason')!='stop' or (reply.get('prompt_eval_count') or 0)>=2048:raise ValueError('FORMAT_OR_CONTEXT_GATE')
            if calls>1 and seconds>5:raise ValueError('WARM_QUERY_OVER_5_SECONDS')
            if generation_seconds>150:raise ValueError('GENERATION_BUDGET_EXCEEDED')
    pos=[r for r in rows if r['kind']=='positive'];neg=[r for r in rows if r['kind']=='negative']
    result.update(status='COMPLETE_PENDING_SEMANTIC_REVIEW',retrieval_hit_at_5=sum(r['retrieval_hit'] for r in pos)/len(pos),
                  positive_answers_emitted=sum(r['answer_emitted'] for r in pos),negatives=len(neg),
                  negative_answer_emission_rate=sum(r['answer_emitted'] for r in neg)/len(neg))
except Exception as error:result.update(status='STOPPED',reason=str(error)[:150],error_type=type(error).__name__)
finally:
    result.update(new_generation_requests=calls,generation_seconds=round(generation_seconds,3))
    (work/'answers.json').write_text(json.dumps(responses,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'semantic-fact-dev-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
