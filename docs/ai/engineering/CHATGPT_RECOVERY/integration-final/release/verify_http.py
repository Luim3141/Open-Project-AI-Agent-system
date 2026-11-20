"""Read-only MAIN API checks plus exact-release HTTP fixtures on a separate SQLite."""
import datetime,json,sys,urllib.error,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.engineering_worker import wsl
out=Path(__file__).parent;deployment=json.loads((out/'deployment.json').read_text())
base='http://127.0.0.1:18791'
def get(path):
 try:response=urllib.request.urlopen(base+path,timeout=10)
 except urllib.error.HTTPError as error:response=error
 with response:return response.status,dict(response.headers),response.read()
checks=[]
for path,expected in [('/healthz',200),('/release',200),('/tasks/summary',200),('/tasks',200),('/tasks/export.csv',200),('/tasks/999999999',404),('/tasks/999999999/exists',200),('/tasks/999999999/title',404),('/tasks/not-an-id/title',422),('/tasks?status=invalid',422),('/tasks/export.csv?status=invalid',422)]:
 status,headers,body=get(path);assert status==expected,(path,status)
 assert headers.get('x-qldapm-revision')==deployment['head_sha']
 assert headers.get('x-qldapm-release-type')=='UNMERGED_INTEGRATION_TEST_RELEASE'
 checks.append({'path':path,'http_status':status,'revision':headers['x-qldapm-revision']})
code=r'''
import sys,tempfile,threading,time,urllib.request,urllib.error,urllib.parse,csv,io
from pathlib import Path
sys.path.insert(0,document['release'])
import uvicorn
from task_manager.app import create_app
with tempfile.TemporaryDirectory(prefix='qldapm-integration-http-') as folder:
 app=create_app(str(Path(folder)/'tasks.sqlite'),release=document['metadata'])
 config=uvicorn.Config(app,host='127.0.0.1',port=18792,access_log=False,log_level='error')
 server=uvicorn.Server(config);thread=threading.Thread(target=server.run,daemon=True);thread.start()
 def request(path,method='GET',value=None):
  data=json.dumps(value,ensure_ascii=False).encode() if value is not None else None
  req=urllib.request.Request('http://127.0.0.1:18792'+path,data=data,method=method,headers={'Content-Type':'application/json'})
  try:response=urllib.request.urlopen(req,timeout=10)
  except urllib.error.HTTPError as error:response=error
  with response:return response.status,dict(response.headers),response.read()
 try:
  for _ in range(50):
   try:
    if request('/healthz')[0]==200:break
   except OSError:pass
   time.sleep(.1)
  title='ĐI CHỢ, mua "sữa"\nvà bánh'
  status,_,body=request('/tasks','POST',{'title':title});assert status==201;first=json.loads(body)
  status,_,body=request('/tasks','POST',{'title':'=SUM(1,2)'});assert status==201;formula=json.loads(body)
  status,_,body=request('/tasks/'+str(first['id']),'PATCH',{'status':'done'});assert status==200
  status,_,body=request('/tasks/'+str(first['id']));assert status==200 and json.loads(body)=={**first,'status':'done'}
  assert json.loads(request('/tasks/'+str(first['id'])+'/exists')[2])=={'exists':True}
  assert json.loads(request('/tasks/'+str(first['id'])+'/title')[2])=={'id':first['id'],'title':title}
  assert json.loads(request('/tasks/summary')[2])=={'total':2,'active':1,'completed':1}
  query=urllib.parse.urlencode({'q':'đi chợ','status':'done'})
  assert json.loads(request('/tasks?'+query)[2])==[{**first,'status':'done'}]
  status,headers,body=request('/tasks/export.csv?'+query);assert status==200
  assert list(csv.reader(io.StringIO(body.decode())))==[['id','title','status'],[str(first['id']),title,'done']]
  body=request('/tasks/export.csv')[2].decode();rows=list(csv.reader(io.StringIO(body)))
  assert rows[2]==[str(formula['id']),'\t=SUM(1,2)','todo'] and '"\t=SUM(1,2)"' in body
  assert json.loads(request('/tasks/'+str(formula['id'])+'/title')[2])['title']=='=SUM(1,2)'
  assert request('/tasks/export.csv?status=invalid')[0]==422
  assert request('/tasks/'+str(formula['id']),'DELETE')[0]==204
  assert json.loads(request('/tasks/'+str(formula['id'])+'/exists')[2])=={'exists':False}
  result={'status':'PASS','source_revision':document['metadata']['revision'],'port':18792,'scope':'isolated temporary SQLite, actual uvicorn HTTP; not MAIN task writes','checks':['create','detail','exists','title','edit','delete','summary','q/status AND filter','Vietnamese casefold','Unicode/comma/quote/newline CSV roundtrip','quoted tab formula mitigation','JSON title unchanged','invalidstatus422']}
  print(json.dumps(result))
 finally:
  server.should_exit=True;thread.join(timeout=10);assert not thread.is_alive()
'''
metadata={'revision':deployment['head_sha'],'type':'UNMERGED_INTEGRATION_TEST_RELEASE','included_prs':[6,7,8,9,10]}
source='import json\ndocument=json.loads('+repr(json.dumps({'release':deployment['release'],'metadata':metadata}))+')\n'+code
process=wsl(['/home/openclaw/engineering/feedback-2ec52f6742aa972f/.venv/bin/python','-'],data=source.encode(),timeout=120,check=False)
if process.returncode:
 (out/'http-fixture-failure.log').write_bytes(process.stdout+process.stderr)
 raise RuntimeError('ISOLATED_HTTP_FIXTURE_FAILED; read scoped fixture log')
fixtures=json.loads(process.stdout)
result={'status':'MAIN_READ_ONLY_AND_ISOLATED_HTTP_BUSINESS_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_revision':deployment['head_sha'],'main_checks':checks,'isolated_http':fixtures,'main_task_writes':0,'sqlite_preservation':'deployment.json exact logical schema/task/sequence hash identical','browser_uat':'PENDING ROOT FINAL PHASE'}
(out/'http-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
