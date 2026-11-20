"""At most six local diagnostics, after Engineering idle; never acceptance or deployment."""
import datetime,hashlib,json,math,subprocess,sys,time,urllib.request
from pathlib import Path
from short_context_pilot import ROOT,WORK,sha

sys.path.insert(0,str(ROOT.parent/'functional-completion'))
from fresh_e2e import py

def request(path,payload=None,timeout=15):
    data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
    req=urllib.request.Request('http://127.0.0.1:11434'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

manifest=json.loads((ROOT/'short-context-pilot-manifest.json').read_text())
assert sha((ROOT/'short_context_pilot.py').read_bytes())==manifest['runner_sha256']
raw=(WORK/'input.json').read_bytes();assert sha(raw)==manifest['input_sha256'];data=json.loads(raw)
plan=json.loads((ROOT/'eval/evaluation-plan.json').read_text())
assert sha((ROOT/'eval/dev.json').read_bytes())==plan['dev_sha256']==data['dev_sha256']
assert sha((ROOT/'eval/native-source-manifest.json').read_bytes())==plan['source_manifest_sha256']
for source in json.loads((ROOT/'eval/native-source-manifest.json').read_text(encoding='utf-8'))['documents']:
    assert sha((ROOT/'eval/private'/source['snapshot_file']).read_bytes())==source['snapshot_sha256']
assert all(p['support_in_context'] for p in data['packets'] if p['case']['kind']=='positive')
state=py("import sqlite3,json;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':c.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':c.execute('select mode from engineering_control where project=6').fetchone()[0]}))")
assert state=={'active':0,'mode':'OFF'},'ENGINEERING_RESOURCE_WINDOW_NOT_GREEN'
memory=int(subprocess.check_output(['powershell.exe','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],timeout=15))
gpu=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],timeout=10).strip())
assert memory>=1572864 and gpu>=2048,'LOCAL_MEMORY_HEADROOM_INSUFFICIENT'
models=request('/api/tags')['models'];model=next(m for m in models if m['name']==data['model'])
payloads=[]
for packet in data['packets']:
    payloads.append({'model':data['model'],'stream':False,'think':False,'keep_alive':'1m','format':data['schema'],'options':data['options'],
        'messages':[{'role':'system','content':data['system']},{'role':'user','content':json.dumps({'question':packet['case']['query'],
            'passages':[{'id':s['id'],'text':s['text']} for s in packet['spans']]},ensure_ascii=False)}]})
freeze={'status':'FROZEN_BEFORE_INFERENCE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_sha256':sha(raw),
    'runner_sha256':sha(Path(__file__).read_bytes()),'model_digest':model['digest'],'request_sha256':[sha(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()) for p in payloads],
    'headroom':{'free_ram_kib':memory,'free_vram_mib':gpu},'resource_limit':'Existing GPU Ollama with num_thread1; no hard process memory cap. Diagnostic only.'}
with (WORK/'run-intent.json').open('x') as f:json.dump(freeze,f,indent=2)
(ROOT/'short-context-pilot-run-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
rows=[];begin=time.monotonic();reason=None
for index,(packet,payload) in enumerate(zip(data['packets'],payloads,strict=True)):
    started=time.monotonic()
    try:
        response=request('/api/chat',payload,timeout=60 if index==0 else 15);seconds=time.monotonic()-started
        ids=json.loads(response['message']['content'])['ids']
        assert isinstance(ids,list) and len(ids)<=5 and all(type(i) is int for i in ids) and len(set(ids))==len(ids)
        spans={s['id']:s for s in packet['spans']};assert all(i in spans for i in ids)
        hits=[spans[i] for i in ids];case=packet['case'];offset=case.get('support_offset',-1);end=offset+len(case.get('support_literal',''))
        supported=any(s['native_id'] in case['relevant_ids'] and s['start']<=offset and s['end']>=end for s in hits)
        correct=supported if case['kind']=='positive' else not hits
        row={'case':case['id'],'kind':case['kind'],'seconds':round(seconds,3),'prompt_tokens':response.get('prompt_eval_count'),'output_tokens':response.get('eval_count'),
            'done_reason':response.get('done_reason'),'model_load_seconds':(response.get('load_duration') or 0)/1e9,'native_ids':list(dict.fromkeys(s['native_id'] for s in hits)),'literal_support_selected':supported,'correct_diagnostic':correct,
            'selected_span_ids':ids,'exact_span_citations':[{k:s[k] for k in ('document_id','native_id','start','end','span_sha256','source_sha256')} for s in hits]}
        rows.append(row)
        if response.get('done_reason')!='stop':reason='OUTPUT_TRUNCATED_OR_INCOMPLETE'
        elif (response.get('prompt_eval_count') or 0)>=data['options']['num_ctx']:reason='CONTEXT_MAY_BE_TRUNCATED'
        elif index and seconds>5:reason='WARM_QUERY_OVER_5_SECONDS'
        elif index and sum(r['seconds'] for r in rows[1:])>60:reason='PILOT_TIME_BUDGET'
    except Exception as error:
        reason='REQUEST_OR_OUTPUT_INVALID_'+type(error).__name__
    result={'status':'DIAGNOSTIC_RUNNING' if reason is None and len(rows)<len(payloads) else 'DIAGNOSTIC_STOPPED' if reason else 'DIAGNOSTIC_COMPLETE',
        'reason':reason,'model_digest':model['digest'],'rows':rows,'elapsed_seconds':round(time.monotonic()-begin,3),
        'all_six_diagnostic_correct':len(rows)==6 and all(r['correct_diagnostic'] for r in rows),'holdout_access':False,'main_retrieval_changed':False,
        'limits':['Observed DEV with correlated VN/EN pairs; no independent acceptance claim.','Cached retrieval/reranking excluded from timings.','Extracted spans are not assessed as complete bilingual generated answers.','No hard memory cap; resource route not deployment-qualified.']}
    (ROOT/'short-context-pilot-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'case':packet['case']['id'],'completed':len(rows),'reason':reason}),flush=True)
    if reason:break
assert rows,'NO_VALID_PILOT_RESPONSE'
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
