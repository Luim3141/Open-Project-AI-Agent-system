"""One capped CPU process, offline fixed ONNX inference; no service or source writes."""
import argparse
from datetime import datetime, timezone
import hashlib,json,os,resource,time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT=Path('/experiment')
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['smoke','score']);parser.add_argument('--input');parser.add_argument('--output',required=True);args=parser.parse_args()
start=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
assert hashlib.sha256((ROOT/'assets/onnx/model_quint8_avx2.onnx').read_bytes()).hexdigest()=='6c2513767fb63d008a4377bef7a7a3555433d9436342bb53e35a3a72ffc52d4b'
assert int(Path('/sys/fs/cgroup/memory.max').read_text())<=768*1024*1024
options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
options.add_session_config_entry('session.intra_op.allow_spinning','0');options.add_session_config_entry('session.inter_op.allow_spinning','0')
ort.disable_telemetry_events()
tokenizer=Tokenizer.from_file(str(ROOT/'assets/tokenizer.json'))
tokenizer.enable_truncation(max_length=512,strategy='longest_first')
session=ort.InferenceSession(str(ROOT/'assets/onnx/model_quint8_avx2.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
loaded=time.perf_counter();inputs=[i.name for i in session.get_inputs()]
if args.action=='smoke':
    pairs=[{'id':'en-relevant','query':'How can I get the title of one task?','passage':'GET /tasks/{task_id}/title returns JSON with the task id and title.'},
        {'id':'en-negative','query':'How can I get the title of one task?','passage':'The system sends SMS reminders for an upcoming event.'},
        {'id':'vi-relevant','query':'Lấy tiêu đề của một công việc bằng ID','passage':'GET /tasks/{task_id}/title trả về JSON chứa id và title của task.'},
        {'id':'vi-negative','query':'Lấy tiêu đề của một công việc bằng ID','passage':'Hệ thống gửi thông báo SMS khi một sự kiện sắp diễn ra.'}]
else:pairs=json.loads((ROOT/args.input).read_text(encoding='utf-8'))['pairs']
results=[]
for pair in pairs:
    t=time.perf_counter();full=tokenizer.encode(pair['query'],pair['passage'])
    feed={'input_ids':np.array([full.ids],dtype=np.int64),'attention_mask':np.array([full.attention_mask],dtype=np.int64),
        'token_type_ids':np.array([full.type_ids],dtype=np.int64)}
    score=float(np.asarray(session.run(None,{k:feed[k] for k in inputs})[0]).reshape(-1)[0])
    assert np.isfinite(score)
    elapsed=time.perf_counter()-t
    assert elapsed<5,'PAIR_CPU_DEADLINE_EXCEEDED'
    results.append({'id':pair['id'],'score':score,'tokens':len(full.ids),'truncated':bool(full.overflowing),
        'visible_text':tokenizer.decode(full.ids),'seconds':elapsed})
    if len(results)%100==0:print('scored',len(results),flush=True)
if args.action=='smoke':assert results[0]['score']>results[1]['score'] and results[2]['score']>results[3]['score']
ended=datetime.now(timezone.utc).isoformat()
output={'started_utc':started,'ended_utc':ended,'model_load_seconds':loaded-start,'total_seconds':time.perf_counter()-start,
    'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'cgroup_memory_peak':int(Path('/sys/fs/cgroup/memory.peak').read_text()),
    'providers':session.get_providers(),'inputs':inputs,'threads':1,'token_limit':512,
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results}
(ROOT/args.output).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in output.items() if k!='results'},indent=2))
if args.action=='smoke':print(json.dumps(results,ensure_ascii=False,indent=2))
