"""Actual local OpenProject MCP read smoke; no Jira operations or MCP mutations."""
import json,os,urllib.request,urllib.error
from pathlib import Path
OUT=Path(__file__).resolve().parent
token=(Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai/secrets/gateway.token').read_text().strip()
headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def rpc(body,authorized=True):
    request=urllib.request.Request('http://127.0.0.1:18089/mcp',data=json.dumps(body).encode(),headers=headers if authorized else {k:v for k,v in headers.items() if k!='Authorization'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=40) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
report={'route':'ACTUAL local OpenProject Gateway /mcp, not Atlassian','checks':{},'reads':[]}
for name,packet in [
    ('initialize',{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'phase4-read-smoke','version':'1'}}}),
    ('tools/list',{'jsonrpc':'2.0','id':2,'method':'tools/list'}),
    ('identity',{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'identity','arguments':{'arguments':{},'project_id':6}}})]:
    status,result=rpc(packet);report['reads'].append({'name':name,'status':status,'response':result});report['checks'][name]=status==200 and 'error' not in result and not result.get('result',{}).get('isError',False)
identity=report['reads'][-1]['response'].get('result',{})
texts=[json.loads(x['text']) for x in identity.get('content',[]) if x.get('type')=='text' and x.get('text','').startswith('{')]
report['checks']['identity_actor_project']=any(x.get('result',{}).get('user_id')==18 and x.get('result',{}).get('project_id')==6 for x in texts)
status,_=rpc({'jsonrpc':'2.0','id':4,'method':'tools/list'},False);report['checks']['unauthenticated_denied']=status==401
(OUT/'mcp-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report['checks']));assert all(report['checks'].values())
