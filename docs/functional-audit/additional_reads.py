"""Additional existing-record reads, no provider call or business mutation."""
import json,subprocess,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
prior=json.loads((OUT/'main-integrations.json').read_text(encoding='utf-8'))
report_id=next(r['result']['reports'][0]['id'] for r in prior['commands'] if r['action']=='engineering_report_list')
script='''import asyncio,json,tempfile,sqlite3
from pathlib import Path
from app.config import Settings
from app.gateway import GatewayClient
from app.storage import Repository
from app.tools import ToolExecutor,sanitize
async def main():
 s=Settings.from_env();g=GatewayClient(s);out=[]
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'copy.sqlite'
  with sqlite3.connect(s.db_path.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(p) as b:a.backup(b)
  executor=ToolExecutor(g,Repository(p),s)
  cases=[('get_project_options',{}),('engineering_report_get',{'id':REPORT_ID}),('get_agent_run',{'id':'de391b2f-e5f2-4bc3-be10-54ab11d73099'}),('get_agent_trace',{'id':'de391b2f-e5f2-4bc3-be10-54ab11d73099','limit':5})]
  for action,args in cases:
   try:
    value=await executor.execute(action,args,1916909968,1916909968,6) if action=='get_project_options' else await g.command(action,args,6)
    out.append({'action':action,'status':'READ_RETURNED','correlation_id':g.last_correlation_id,'result':sanitize(value)})
   except Exception as e:out.append({'action':action,'status':'DENIED_OR_ERROR','error':str(e)[:250]})
 await g.close();return out
print(json.dumps(asyncio.run(main()),ensure_ascii=False))'''.replace('REPORT_ID',repr(report_id))
p=subprocess.run(['docker','exec','-i','qldapm-ai-telegram-ai-1','python','-'],input=script,text=True,capture_output=True,encoding='utf-8',check=True,timeout=180)
result={'at':time.time(),'scope':'MAIN existing-record reads; no model inference or new business record','reads':json.loads(p.stdout)}
(OUT/'additional-reads.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k!='result'} for r in result['reads']]))
