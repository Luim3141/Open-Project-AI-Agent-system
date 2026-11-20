"""Synthetic question-form probe, independent of the locked benchmark corpus."""
import json,time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
o=ort.SessionOptions();o.intra_op_num_threads=1;o.inter_op_num_threads=1;o.add_session_config_entry('session.intra_op.allow_spinning','0')
model=ort.InferenceSession('/model/model-quant.onnx',sess_options=o,providers=['CPUExecutionProvider']);names=[x.name for x in model.get_inputs()]
tokenizer=Tokenizer.from_file('/model/tokenizer.json');tokenizer.enable_truncation(max_length=384)
cases=[
 ('en-open-positive','Books are kept for 14 days before they must be returned.','How many days can a person keep a borrowed book?'),
 ('en-open-negative','Books are kept for 14 days before they must be returned.','How much is the penalty for returning a book late?'),
 ('en-yes-positive','A registered member can reserve books online.','Can a registered member reserve a book online?'),
 ('en-yes-negative','A registered member can reserve books online.','Can a member pay fees with cryptocurrency?'),
 ('vi-open-positive','Sách được mượn trong 14 ngày trước khi phải trả.','Thời hạn mượn sách là bao nhiêu ngày?'),
 ('vi-open-negative','Sách được mượn trong 14 ngày trước khi phải trả.','Mức phạt trả sách quá hạn là bao nhiêu tiền?'),
 ('vi-yes-positive','Thành viên đã đăng ký được đặt trước sách trực tuyến.','Thành viên có thể đặt sách trước qua mạng không?'),
 ('vi-yes-negative','Thành viên đã đăng ký được đặt trước sách trực tuyến.','Thành viên có thể trả phí bằng tiền điện tử không?')]
rows=[]
for name,premise,question in cases:
 for kind,hyp in [('raw',question),('meta_en','This text answers the question: '+question),('meta_vi','Đoạn văn trả lời câu hỏi: '+question)]:
  v=tokenizer.encode(premise,hyp);feed={'input_ids':np.asarray([v.ids],dtype=np.int64),'attention_mask':np.asarray([v.attention_mask],dtype=np.int64),'token_type_ids':np.asarray([v.type_ids],dtype=np.int64)}
  scores=np.asarray(model.run(None,{k:feed[k] for k in names})[0]).reshape(-1);p=np.exp(scores-np.max(scores));p/=p.sum()
  rows.append({'case':name,'hypothesis':kind,'entailment':float(p[0]),'neutral':float(p[1]),'contradiction':float(p[2])})
Path('/result/nli-question-probe.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
