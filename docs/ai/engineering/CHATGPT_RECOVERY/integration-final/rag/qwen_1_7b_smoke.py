"""Public synthetic fixture only; local Ollama answerability feasibility."""
import json,time,urllib.request
from pathlib import Path
cases=[
 ('en-open-positive','Books are kept for 14 days before they must be returned.','How many days can a person keep a borrowed book?',True),
 ('en-open-negative','Books are kept for 14 days before they must be returned.','How much is the penalty for returning a book late?',False),
 ('en-yes-positive','A registered member can reserve books online.','Can a registered member reserve a book online?',True),
 ('en-yes-negative','A registered member can reserve books online.','Can a member pay fees with cryptocurrency?',False),
 ('vi-open-positive','Sách được mượn trong 14 ngày trước khi phải trả.','Thời hạn mượn sách là bao nhiêu ngày?',True),
 ('vi-open-negative','Sách được mượn trong 14 ngày trước khi phải trả.','Mức phạt trả sách quá hạn là bao nhiêu tiền?',False),
 ('vi-yes-positive','Thành viên đã đăng ký được đặt trước sách trực tuyến.','Thành viên có thể đặt sách trước qua mạng không?',True),
 ('vi-yes-negative','Thành viên đã đăng ký được đặt trước sách trực tuyến.','Thành viên có thể trả phí bằng tiền điện tử không?',False)]
schema={'type':'object','properties':{'supported':{'type':'boolean'}},'required':['supported'],'additionalProperties':False}
results=[]
for case,passage,question,expected in cases:
 payload={'model':'qwen3:1.7b','stream':False,'think':False,'format':schema,'keep_alive':'1m',
 'options':{'temperature':0,'num_predict':32,'num_ctx':512,'num_thread':1,'seed':42},
 'messages':[{'role':'system','content':'Decide whether the passage explicitly provides enough information to answer the question. Nearby related topics are not enough. Respond only as JSON with supported true or false.'},
 {'role':'user','content':json.dumps({'passage':passage,'question':question},ensure_ascii=False)}]}
 request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
 started=time.monotonic()
 with urllib.request.urlopen(request,timeout=120) as r:response=json.load(r)
 answer=json.loads(response['message']['content'])
 results.append({'case':case,'expected':expected,'actual':answer.get('supported'),'seconds':round(time.monotonic()-started,3),'tokens':response.get('eval_count')})
out={'model':'qwen3:1.7b','model_digest':'8f68893c685c','data':'synthetic fixtures only','cpu_threads':1,'rows':results}
Path(__file__).with_name('qwen-1.7b-smoke.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

