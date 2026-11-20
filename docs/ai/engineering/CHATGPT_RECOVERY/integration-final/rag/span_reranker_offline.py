"""Pinned local relevance scorer for a bounded dev experiment; no network, no answerability claim."""
import hashlib,json,math,resource,sys,time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ASSETS=Path('/experiment/assets');DATA=Path('/data');OUT=Path('/output')
assert int(Path('/sys/fs/cgroup/memory.max').read_text())<=768*1024*1024
for name,expected in [('onnx/model_quint8_avx2.onnx','6c2513767fb63d008a4377bef7a7a3555433d9436342bb53e35a3a72ffc52d4b'),
                      ('tokenizer.json','62c24cdc13d4c9952d63718d6c9fa4c287974249e16b7ade6d5a85e7bbb75626')]:
    assert hashlib.sha256((ASSETS/name).read_bytes()).hexdigest()==expected,'MODEL_HASH_MISMATCH'
batch=json.loads((DATA/'pairs.json').read_text(encoding='utf-8'));pairs=batch['pairs'];groups=batch.get('group_sizes')
assert isinstance(pairs,list) and 1<=len(pairs)<=400
if groups is not None:assert isinstance(groups,list) and all(type(n) is int and n>=0 for n in groups) and sum(groups)==len(pairs)
options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
options.add_session_config_entry('session.intra_op.allow_spinning','0');options.add_session_config_entry('session.inter_op.allow_spinning','0')
ort.disable_telemetry_events();start=time.monotonic()
tokenizer=Tokenizer.from_file(str(ASSETS/'tokenizer.json'));tokenizer.enable_truncation(max_length=512,strategy='longest_first')
session=ort.InferenceSession(str(ASSETS/'onnx/model_quint8_avx2.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
loaded=time.monotonic();input_names=[x.name for x in session.get_inputs()];rows=[]
group_index=0;group_elapsed=0.0;group_seconds=[]
for pair in pairs:
    assert isinstance(pair.get('id'),str) and len(pair['id'])<=120
    assert isinstance(pair.get('query'),str) and len(pair['query'])<=1000
    assert isinstance(pair.get('passage'),str) and len(pair['passage'])<=800
    begin=time.monotonic();enc=tokenizer.encode(pair['query'],pair['passage'])
    feed={'input_ids':np.array([enc.ids],dtype=np.int64),'attention_mask':np.array([enc.attention_mask],dtype=np.int64),
          'token_type_ids':np.array([enc.type_ids],dtype=np.int64)}
    score=float(np.asarray(session.run(None,{k:feed[k] for k in input_names})[0]).reshape(-1)[0])
    assert math.isfinite(score)
    elapsed=time.monotonic()-begin
    if elapsed>=5:raise TimeoutError('SINGLE_PAIR_CPU_BUDGET_EXCEEDED')
    rows.append({'id':pair['id'],'score':score,'seconds':round(elapsed,6),'tokens':len(enc.ids),'truncated':bool(enc.overflowing)})
    if groups is not None:
        while group_index<len(groups) and groups[group_index]==0:group_seconds.append(0);group_index+=1
        group_elapsed+=elapsed
        if group_elapsed>5:raise TimeoutError('WARM_GROUP_CPU_BUDGET_EXCEEDED')
        if len(rows)==sum(groups[:group_index+1]):group_seconds.append(round(group_elapsed,6));group_index+=1;group_elapsed=0
if groups is not None:
    while group_index<len(groups) and groups[group_index]==0:group_seconds.append(0);group_index+=1
    assert group_index==len(groups)
result={'model':'cross-encoder/mmarco-mMiniLMv2-L12-H384-v1','revision':'1427fd652930e4ba29e8149678df786c240d8825',
        'input_sha256':hashlib.sha256((DATA/'pairs.json').read_bytes()).hexdigest(),'model_load_seconds':round(loaded-start,4),
        'total_seconds':round(time.monotonic()-start,4),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'cgroup_memory_peak':int(Path('/sys/fs/cgroup/memory.peak').read_text()),'network':'none','cpu_threads':1,'group_seconds':group_seconds,'rows':rows}
(OUT/'scores.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
