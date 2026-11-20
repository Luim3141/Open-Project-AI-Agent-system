"""Final-image operator isolation, real Native denial, HMAC replay and five queued local workers."""
import concurrent.futures
import hashlib
import hmac
import json
import time
import uuid
import httpx
from tests.remaining_browser_uat import PRIVATE,OUT,BASE,GATEWAY
from tests.qualify_remaining import docker
from gateway.permissions import SANDBOX_ONLY


def main():
    fixture=json.loads((PRIVATE/'fixture-credentials.json').read_text());users=fixture['users']
    pm=next(a for a in users if a['role']=='PM');be=next(a for a in users if a['role']=='BE');identifier=fixture['work_package_id']
    image=json.loads((OUT/'candidate-images.json').read_text())['gateway']['image']
    info=json.loads(docker('inspect','qldapm-rd-gateway-20261018'))[0]
    assert info['Config']['Labels']['qldapm.qualification']=='remaining-20261018' and info['Image']==image
    report={'scope':'FINAL_CANDIDATE_ISOLATED_NEW_FIXTURE_ONLY','image':image,'checks':[],'runs':[]};out=OUT/'final-image-uat.json'
    def check(case,ok,actual=None):
        report['checks'].append({'id':case,'expected':'Assertion in remaining_final_uat.py must hold','status':'PASS' if ok else 'FAIL','actual':actual,'exit_code':0 if ok else 1})
        out.write_text(json.dumps(report,indent=2));assert ok,case
    def headers(a):return {'Authorization':'Bearer '+a['gateway_token']}
    def command(a,action,args=None,key=None):
        return httpx.post(GATEWAY+'/api/v1/commands',headers=headers(a),json={'action':action,'arguments':args or {},'idempotency_key':key},trust_env=False,timeout=90)
    for action in sorted(SANDBOX_ONLY):
        r=command(pm,action,{},uuid.uuid4().hex)
        check('FINAL-DENY-'+action,r.status_code==403 and r.json().get('error')=='NATIVE_BUSINESS_OPERATOR_TOOL_DENIED',{'http':r.status_code})
    mcp_headers={**headers(pm),'Accept':'application/json, text/event-stream'}
    init=httpx.post(GATEWAY+'/mcp',headers=mcp_headers,json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{
        'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'isolated-qualification','version':'1'}}},trust_env=False,timeout=60)
    listing=httpx.post(GATEWAY+'/mcp',headers=mcp_headers,json={'jsonrpc':'2.0','id':2,'method':'tools/list'},trust_env=False,timeout=60)
    names={t['name'] for t in listing.json()['result']['tools']}
    check('FINAL-MCP-CATALOG',init.status_code==200 and not names&SANDBOX_ONLY and 'start_ai_run' in names and 'knowledge_search' in names,{'operator_tools':sorted(names&SANDBOX_ONLY),'tools':len(names)})
    with httpx.Client(trust_env=False,timeout=60) as client:
        item=client.get(BASE+f'/api/v3/work_packages/{identifier}',auth=('apikey',pm['token'])).json()
        denied=client.patch(BASE+f'/api/v3/work_packages/{identifier}',auth=('apikey',be['token']),json={'lockVersion':item['lockVersion'],'subject':'MUST_NOT_WRITE'})
        after=client.get(BASE+f'/api/v3/work_packages/{identifier}',auth=('apikey',pm['token'])).json()
        check('FINAL-NATIVE-RBAC',denied.status_code==403 and after['lockVersion']==item['lockVersion'] and after['subject']==item['subject'],{'http':denied.status_code})
        rejected=client.patch(BASE+f'/api/v3/work_packages/{identifier}',auth=('apikey',pm['token']),json={'lockVersion':item['lockVersion'],'_links':{'status':{'href':'/api/v3/statuses/999999'}}})
        after=client.get(BASE+f'/api/v3/work_packages/{identifier}',auth=('apikey',pm['token'])).json()
        check('FINAL-NATIVE-VALIDATION',rejected.status_code==422 and after['lockVersion']==item['lockVersion'],{'http':rejected.status_code})
    assertion={'actor':pm['id'],'project':fixture['project_id'],'audience':'qldapm-ai-ui','at':int(time.time()),'nonce':uuid.uuid4().hex,
        'operation':'command','command':{'action':'identity','arguments':{}}};body=json.dumps(assertion).encode()
    signature=hmac.new((PRIVATE/'state/ui.key').read_bytes(),body,hashlib.sha256).hexdigest()
    bad=httpx.post(GATEWAY+'/internal/ui',content=body,headers={'Content-Type':'application/json','X-Qldapm-Signature':'0'*64},trust_env=False)
    good=httpx.post(GATEWAY+'/internal/ui',content=body,headers={'Content-Type':'application/json','X-Qldapm-Signature':signature},trust_env=False,timeout=60)
    replay=httpx.post(GATEWAY+'/internal/ui',content=body,headers={'Content-Type':'application/json','X-Qldapm-Signature':signature},trust_env=False)
    check('FINAL-UI-HMAC-REPLAY',bad.status_code==403 and good.status_code==200 and replay.status_code==403,
        {'invalid':bad.status_code,'valid':good.status_code,'replay':replay.status_code})
    def start(a):return a,command(a,'start_ai_run',{'prompt':f'Phân tích yêu cầu công việc #{identifier}','engine':'supervisor'},uuid.uuid4().hex)
    started=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:admissions=list(pool.map(start,users))
    check('FINAL-FIVE-ADMISSIONS',all(r.status_code==200 for _,r in admissions),{'http':[r.status_code for _,r in admissions]})
    pending={r.json()['result']['id']:a for a,r in admissions};finished={};deadline=time.monotonic()+180
    while pending and time.monotonic()<deadline:
        for rid,a in list(pending.items()):
            r=command(a,'get_ai_run',{'id':rid});value=r.json().get('result',{})
            if value.get('state')!='running':
                finished[rid]=value;pending.pop(rid);report['runs'].append({'role':a['role'],'actor':a['id'],'id':rid})
        if pending:time.sleep(1)
    check('FINAL-FIVE-OUTPUTS',len(finished)==5 and all(v.get('state')=='done' and v['result'].get('model_used') is False and
        v['result'].get('engine')=='local_supervisor' and 'Phân tích local trên' in v['result'].get('text','') and v['result'].get('plan') for v in finished.values()),
        {'completed':len(finished),'seconds':round(time.monotonic()-started,2)})
    usage=json.loads(docker('exec','qldapm-rd-gateway-20261018','python','-c',
        "import sqlite3,json;d=sqlite3.connect('/state/gateway.sqlite');print(json.dumps({'rows':d.execute('SELECT COUNT(*) FROM gemini_usage').fetchone()[0]}));d.close()"))
    check('FINAL-ZERO-PROVIDER',usage['rows']==0,usage)
    report['passed']=True;out.write_text(json.dumps(report,indent=2));print(json.dumps({'passed':True,'checks':len(report['checks']),'image':image}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'passed':False,'error_type':type(error).__name__,'details_private':True}));raise SystemExit(1)
