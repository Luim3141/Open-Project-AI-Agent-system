"""Offline viability probe; no production data, generation or network."""
import json,math,resource,time,os
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
options.add_session_config_entry('session.intra_op.allow_spinning','0')
tokenizer=Tokenizer.from_file('/model/tokenizer.json');tokenizer.enable_truncation(max_length=384)
start=time.monotonic();model=ort.InferenceSession('/model/'+os.environ.get('NLI_MODEL','model.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
inputs=[v.name for v in model.get_inputs()];labels=['entailment','neutral','contradiction']
pairs=[
 ('positive_en','The task title can be updated and saved.','The task title can be changed.'),
 ('negative_en','The task title can be updated and saved.','Tasks can be exported as a spreadsheet.'),
 ('positive_vi','Người dùng có thể sửa tên công việc và lưu thay đổi.','Người dùng có thể thay đổi tên công việc.'),
 ('negative_vi','Người dùng có thể sửa tên công việc và lưu thay đổi.','Ứng dụng gửi tin nhắn SMS cho người thực hiện.'),
 ('condition_en','The endpoint returns a CSV file with id and title.','The endpoint returns an XLSX file.'),
 ('condition_vi','Tệp CSV có hai cột id và title.','Tệp CSV có cột email người được giao.'),
]
rows=[]
for case,premise,hypothesis in pairs:
 t=time.monotonic();enc=tokenizer.encode(premise,hypothesis)
 feed={'input_ids':np.array([enc.ids],np.int64),'attention_mask':np.array([enc.attention_mask],np.int64),'token_type_ids':np.array([enc.type_ids],np.int64)}
 logits=np.asarray(model.run(None,{k:feed[k] for k in inputs})[0]).reshape(-1);prob=np.exp(logits-np.max(logits));prob/=prob.sum()
 rows.append({'case':case,'probs':{k:float(v) for k,v in zip(labels,prob)},'seconds':time.monotonic()-t})
result={'model_load_and_tests_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'cgroup_memory_peak':int(Path('/sys/fs/cgroup/memory.peak').read_text()),'threads':1,'network':'none','cases':rows}
Path('/result/'+os.environ.get('NLI_RESULT','nli-smoke.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
