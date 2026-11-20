"""One exact-input diagnostic replay, before any new RAG selection experiment."""
import datetime,hashlib,json,os,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
RAG=ROOT/'docs/ai/engineering/CHATGPT_RECOVERY/integration-final/rag'
sys.path[:0]=[str(RAG),str(RAG.parent/'functional-completion')]
from short_context_pilot import WORK
from source_spans import extract_spans
from evidence_validation import EvidenceError,capture_response,validate_response
from fresh_e2e import py

OUT=Path(__file__).parent
private=WORK.parent/'autonomous-grouped-failure-diagnostic'
assert not private.exists(),'DIAGNOSTIC_INTENT_EXISTS_RECONCILE_NEVER_BLIND_REPLAY'
freeze=json.loads((RAG/'grouped-quote-pilot-freeze.json').read_text())
payload=json.loads((WORK.parent/'grouped-quote-pilot/requests.json').read_text(encoding='utf-8'))[2]
packet=json.loads((WORK/'input.json').read_text(encoding='utf-8'))['packets'][2]
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode())==freeze['request_sha256'][2]
state=py("import sqlite3,json;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'mode':c.execute('select mode from engineering_control where project=6').fetchone()[0],'active':c.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0]}))")
assert state=={'mode':'OFF','active':0}
ram=int(subprocess.check_output(['powershell.exe','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],timeout=15));gpu=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],timeout=10));assert ram>=1572864 and gpu>=2048
with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=5) as r:models=json.load(r)['models']
model=next(m for m in models if m['name']==payload['model']);assert model['digest']==freeze['model_digest']
sources={};spans={}
for item in json.loads((RAG/'eval/native-source-manifest.json').read_text(encoding='utf-8'))['documents']:
    path=RAG/'eval/private'/item['snapshot_file'];assert sha(path.read_bytes())==item['snapshot_sha256'];text=path.read_text(encoding='utf-8');sources[item['source_hash']]=text
    for s in extract_spans(text):spans[(item['source_hash'],s['start'],s['end'])]=s
private.mkdir();intent={'case_id':packet['case']['id'],'request_sha256':freeze['request_sha256'][2],'model_digest':model['digest'],'max_requests':1,'hypothesis':'Identify the exact failed validator rule with unchanged historical input; not model/cutoff tuning.'};(private/'intent.json').write_text(json.dumps(intent,indent=2)+'\n')
request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
started=time.monotonic()
with urllib.request.urlopen(request,timeout=60) as response:
    raw=response.read(65537);assert len(raw)<=65536,'OLLAMA_RESPONSE_LIMIT';reply=json.loads(raw)
captured=capture_response(reply,private/'response-redacted.json')
try:
    validated=validate_response(reply['message']['content'],packet,sources,spans)
    outcome={'status':'NO_IDENTITY_FAILURE_REPRODUCED','valid_matches':len(validated),'support':'UNVERIFIED'}
except EvidenceError as error:outcome={'status':'VALIDATION_FAILURE_REPRODUCED','diagnostic':error.diagnostic()}
result={**intent,**outcome,**captured,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':round(time.monotonic()-started,3),'private_capture':str(private/'response-redacted.json'),'runner_sha256':sha(Path(__file__).read_bytes()),'main_changed':False,'holdout_access':False,'historical_response_available':False,'limitations':['Historical response was not saved, so byte-for-byte identity with that response cannot be asserted.','Typed validation verifies identity only, not semantic answer support.']}
(OUT/'rag-grouped-failure-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
