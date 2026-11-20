"""Actual MAIN read/ACL smoke. Explicit --generate permits only two fixed RAG generations."""
import json,os,sys,time,urllib.request,urllib.error
from pathlib import Path
OUT=Path(__file__).resolve().parent
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
def command(action,args,project=6):
    token=(PRIVATE/'telegram-ai/secrets/gateway.token').read_text().strip()
    request=urllib.request.Request('http://127.0.0.1:18089/api/v1/commands',data=json.dumps({'action':action,'arguments':args,'project_id':project}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=120) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as error:return error.code,json.load(error)
report={'at':time.time(),'scope':'ACTUAL MAIN commands, no business mutation; optional two explicit existing-Free-policy Gemini calls','cases':[],'checks':{}}
def case(name,action,args,project=6):
    start=time.monotonic();status,packet=command(action,args,project);report['cases'].append({'name':name,'status':status,'seconds':time.monotonic()-start,'correlation_id':packet.get('correlation_id'),'result':packet.get('result'),'error':packet.get('error')});return status,packet.get('result') or {}
_,search=case('registered_file_generic_search','knowledge_search',{'query':'ORBIT-RECEIPT-20261103','mode':'search','limit':5})
report['checks']['generic_registered_source']=any(i['source_id']=='file:project6-integration-qualification' for i in search.get('items',[]))
report['checks']['search_is_not_generation']=search.get('model_used') is False and search.get('answer') is None
_,quote=case('extract_no_hidden_model','knowledge_search',{'query':'ORBIT-RECEIPT-20261103','mode':'extract','limit':5})
report['checks']['extract_not_fake_answerability']=quote.get('answerability',{}).get('state')=='EXTRACTS_AVAILABLE' and quote.get('model_used') is False
_,wrong=case('wrong_project_scope','knowledge_search',{'query':'ORBIT-RECEIPT-20261103','limit':5},5)
report['checks']['wrong_project_no_fixture_leak']=all(i.get('project_id')==5 and i.get('source_id')!='file:project6-integration-qualification' for i in wrong.get('items',[]))
for key,args in [('invalid_mode',{'query':'x','mode':'execute'}),('invalid_limit',{'query':'x','limit':0}),('forged_native_scope',{'query':'x','native_ids':['398']})]:
    status,_=case(key,'knowledge_search',args);report['checks'][key]=status==422
_,task=case('398_current_acceptance','observer_task_progress',{'task_id':398,'view':'graph'})
report['checks']['398_still_awaiting_owner']=task.get('acceptance_status')=='AWAITING_OWNER_APPROVAL' and task.get('business_status')=='READY FOR RELEASE'
report['cases'][-1]['result']={k:task.get(k) for k in ['task_id','workflow_status','business_status','acceptance_status','version','latest_run_id']}
if '--generate' in sys.argv:
    _,answer=case('explicit_grounded_answer','knowledge_search',{'query':'Tài liệu có mã ORBIT-RECEIPT-20261103 nói gì và có chứng nhận Owner acceptance không?','mode':'answer','limit':5})
    claims=(answer.get('answer') or {}).get('claims',[]);quoted='\n'.join(c['quote'] for c in claims)
    report['checks']['actual_model_grounded_facts']=answer.get('answerability',{}).get('state')=='SUPPORTED' and 'does not certify' in quoted and 'Owner acceptance' in quoted
    report['checks']['actual_exact_model']=answer.get('generation',{}).get('resolved_model_version')=='gemini-3.5-flash-lite'
    _,negative=case('missing_answer_abstention','knowledge_search',{'query':'Tổng thống sao Hỏa uống cà phê giá bao nhiêu?','mode':'answer','limit':5})
    report['checks']['missing_answer_no_fabrication']=negative.get('answer') is None and negative.get('answerability',{}).get('state') in ['ABSTAIN','NO_EVIDENCE']
(OUT/'main-read.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':report['checks'],'cases':[{k:r[k] for k in ['name','status','seconds','correlation_id']} for r in report['cases']]},ensure_ascii=False));assert all(report['checks'].values())
