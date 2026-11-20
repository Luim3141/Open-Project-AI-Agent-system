"""Actual Rails/Edge UAT against the owned isolated clone; generated credentials never leave private files."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import struct
import time
import uuid
import httpx
from playwright.sync_api import sync_playwright

AI=Path(__file__).resolve().parents[1]
OUT=AI.parents[1]/'docs/ai-multi-agent-upgrade/remaining-development'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/remaining-qualification-20261018'
BASE='http://localhost:18095'
GATEWAY='http://localhost:18096'
ASSISTANT='/projects/qldapm-local/qldapm-ai'


def otp(secret):
    value=hmac.new(base64.b32decode(secret,casefold=True),struct.pack('>Q',int(time.time()//30)),hashlib.sha1).digest()
    offset=value[-1]&15
    return f'{(struct.unpack(">I",value[offset:offset+4])[0]&0x7fffffff)%1000000:06d}'


def main():
    data=json.loads((PRIVATE/'fixture-credentials.json').read_text())
    config=json.loads((PRIVATE/'state/config.json').read_text())
    images=json.loads((OUT/'candidate-images.json').read_text())
    result={'scope':'ISOLATED_NEW_FIXTURE_USERS_ONLY','images':images,'started_at':time.time(),'checks':[],
        'provider_calls_requested':0,'serving_native_mutations':0}
    output=OUT/('browser-uat-'+str(int(time.time()))+'.json')
    assets=OUT/(output.stem+'-assets');assets.mkdir()
    result['artifact_directory']=str(assets)
    def check(case,expected,passed,actual=None):
        result['checks'].append({'id':case,'expected':expected,'status':'PASS' if passed else 'FAIL','actual':actual,
            'exit_code':0 if passed else 1})
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False))
    def command(account,action,args=None,key=None):
        body={'action':action,'arguments':args or {}}
        if key:body['idempotency_key']=key
        with httpx.Client(trust_env=False,timeout=90) as client:
            return client.post(GATEWAY+'/api/v1/commands',headers={'Authorization':'Bearer '+account['gateway_token']},json=body)
    def native(account,path):
        with httpx.Client(trust_env=False,timeout=60) as client:
            return client.get(BASE+path,auth=('apikey',account['token']),headers={'Accept':'application/hal+json'})
    def direct_form(page,tool,args):
        page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
        page.locator('details.qldapm-ai-tools').evaluate('(e)=>e.open=true')
        form=page.locator('form:has(select#tool)')
        form.locator('select#tool').select_option(tool)
        form.locator('textarea#arguments').fill(json.dumps(args,ensure_ascii=False))
        form.locator('input[type=submit]').click()
        page.wait_for_load_state('domcontentloaded')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        accounts=sorted(data['users'],key=lambda a:a['role']!='PM')
        for account in accounts:
            role=account['role'];prefix='UAT-'+role
            ctx=browser.new_context(viewport={'width':1280,'height':850})
            page=ctx.new_page();errors=[];network=[]
            page.on('pageerror',lambda error:errors.append(type(error).__name__))
            page.on('response',lambda r:network.append({'status':r.status,'path':r.url.split('?')[0].removeprefix(BASE)}) if r.status>=500 else None)
            authenticated=False;preauth_errors=[]
            try:
                page.goto(BASE+'/login',wait_until='domcontentloaded',timeout=60000)
                page.locator('#username').fill(account['login'])
                page.locator('#password').fill(account['password'])
                page.locator('form:has(#username) button[type=submit]').click()
                page.locator('#otp').wait_for(timeout=30000)
                if time.time()%30>26:time.sleep(4)
                page.locator('#otp').fill(otp(account['totp_secret']))
                page.locator('input[type=submit][name=login]').click()
                page.wait_for_load_state('domcontentloaded')
                me=ctx.request.get(BASE+'/api/v3/users/me')
                observed=me.json() if me.status==200 else {}
                authenticated=observed.get('id')==account['id']
                check(prefix+'-LOGIN','Native login/TOTP identifies synthetic actor',authenticated,{'http':me.status,'id':observed.get('id')})
                if not authenticated:continue
                preauth_errors=errors.copy();errors.clear()
                page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
                check(prefix+'-CONTROL-CENTER','Real Core renders Control Center',page.get_by_role('heading',name='AI Control Center',exact=True).count()==1)
                if role=='PM' and not data.get('work_package_id'):
                    types=command(account,'get_project_options').json()['result']['types']
                    native_type=next((t['id'] for t in types if t.get('name')=='Task'),types[0]['id'])
                    source='rd-uat-'+uuid.uuid4().hex[:16]
                    subject='RD isolated knowledge login fixture'
                    before=native(account,'/api/v3/projects/3/work_packages?pageSize=1').json()['total']
                    direct_form(page,'create_work_package',{'source_id':source,'subject':subject,'type_id':native_type,
                        'description':'Given valid credentials When user logs in Then show dashboard. Draft acceptance criteria and test suggestions.'})
                    proposal=page.locator('form[action$="/confirm"]')
                    check('UAT-PM-PREVIEW','Native data unchanged before explicit confirmation',proposal.count()==1 and native(account,'/api/v3/projects/3/work_packages?pageSize=1').json()['total']==before)
                    if proposal.count()!=1:raise RuntimeError('CREATE_PREVIEW_NOT_RENDERED')
                    proposal.locator('input[type=submit]').click();page.wait_for_load_state('domcontentloaded')
                    link=page.get_by_role('link',name='Mở công việc',exact=True)
                    if link.count()!=1:raise RuntimeError('CREATE_READBACK_LINK_MISSING')
                    identifier=int(link.get_attribute('href').rstrip('/').split('/')[-1])
                    item=native(account,f'/api/v3/work_packages/{identifier}').json()
                    check('UAT-PM-CREATE','UI confirmation creates exact native fixture and source ID',item['subject']==subject and item.get(config['source_field'])==source,{'id':identifier,'lock_version':item['lockVersion']})
                    data['work_package_id']=identifier
                    (PRIVATE/'fixture-credentials.json').write_text(json.dumps(data))
                identifier=data.get('work_package_id')
                if not identifier:raise RuntimeError('FIXTURE_CREATE_REQUIRED')
                if role=='PM':
                    item=native(account,f'/api/v3/work_packages/{identifier}').json()
                    changed='RD isolated knowledge login fixture reviewed '+str(int(time.time()))
                    direct_form(page,'update_work_package',{'id':identifier,'lock_version':item['lockVersion'],'changes':{'subject':changed}})
                    pending=page.locator('form[action$="/confirm"]')
                    if pending.count()!=1:raise RuntimeError('UPDATE_PREVIEW_NOT_RENDERED')
                    pending.locator('input[type=submit]').click();page.wait_for_load_state('domcontentloaded')
                    after=native(account,f'/api/v3/work_packages/{identifier}').json()
                    check('UAT-PM-UPDATE','Native subject/lockVersion match confirmed update',after['subject']==changed and after['lockVersion']>item['lockVersion'])
                else:
                    item=native(account,f'/api/v3/work_packages/{identifier}').json()
                    denied=command(account,'update_work_package',{'id':identifier,'lock_version':item['lockVersion'],'changes':{'subject':'MUST_NOT_WRITE'}},uuid.uuid4().hex)
                    check(prefix+'-WRITE-DENIED','Non-PM mutation denied without changing native fixture',denied.status_code==403 and native(account,f'/api/v3/work_packages/{identifier}').json()['subject']==item['subject'])
                    forged=command(account,'start_ai_run',{'prompt':'Analyze','engine':'supervisor','actor_id':13},uuid.uuid4().hex)
                    check(prefix+'-NO-IMPERSONATION','Client actor override rejected',forged.status_code in (403,422))
                page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
                form=page.locator('form:has(select#engine)')
                form.locator('#engine').select_option('supervisor')
                prompts={'PM':'Phân tích rủi ro sprint','BA-PM':'Phân tích user story và AC','BE':'Phân rã backend','FE':'Phân rã frontend','QA':'Thiết kế kịch bản kiểm thử'}
                form.locator('#prompt').fill(prompts[role]+f' cho công việc #{identifier}')
                form.locator('input[type=submit]').click();page.wait_for_load_state('domcontentloaded')
                run_id=page.url.split('run_id=')[-1].split('&')[0]
                deadline=time.monotonic()+150
                run=None
                while time.monotonic()<deadline:
                    r=command(account,'get_ai_run',{'id':run_id})
                    if r.status_code!=200:raise RuntimeError('RUN_POLL_DENIED')
                    run=r.json()['result']
                    if run['state']!='running':break
                    time.sleep(2)
                check(prefix+'-SUPERVISOR','Real queued worker completes local specialists/reviewer with zero model calls',
                    bool(run and run['state']=='done' and run.get('result',{}).get('engine')=='local_supervisor' and run['result'].get('model_used') is False),{'run_id':run_id,'state':run.get('state') if run else None})
                page.goto(BASE+ASSISTANT+'?run_id='+run_id,wait_until='domcontentloaded',timeout=90000)
                check(prefix+'-OUTPUT','Actual result and execution plan visible in frontend','Phân tích local trên' in page.inner_text('body') and 'Execution plan' in page.inner_text('body'))
                page.locator('.qldapm-ai-result').last.screenshot(path=str(assets/('result-'+role.lower()+'.png')))
                trace=command(account,'get_agent_trace',{'id':run_id}).json()['result']
                check(prefix+'-TRACE','Own persisted trace has specialist events',any(x['action']=='trace_agent' for x in trace['items']),{'events':trace['total']})
                page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
                form=page.locator('form:has(#native_id)');form.locator('#native_id').fill(str(identifier))
                form.get_by_role('button',name='Lập / cập nhật chỉ mục').click();page.wait_for_load_state('domcontentloaded')
                search=page.locator('form:has(#knowledge_query)');search.locator('#knowledge_query').fill('knowledge login')
                search.locator('input[type=submit]').click();page.wait_for_load_state('domcontentloaded')
                check(prefix+'-KNOWLEDGE','UI ingestion/search shows fresh native citation',page.locator('article a[href="/work_packages/'+str(identifier)+'"]').count()>=1 and 'lockVersion' in page.inner_text('body'))
                for width in (390,1280):
                    page.set_viewport_size({'width':width,'height':850})
                    check(prefix+'-VIEWPORT-'+str(width),'No horizontal document overflow',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'))
                page.set_viewport_size({'width':1280,'height':850})
                page.screenshot(path=str(assets/(role.lower()+'-assistant.png')),full_page=True)
                check(prefix+'-CONSOLE','No uncaught Assistant page errors or HTTP5xx after authentication',not errors and not network,
                    {'postauth_page_errors':len(errors),'http_5xx':len(network),'preauth_native_errors':len(preauth_errors),
                     'preauth_evidence':'browser-error-diagnostic.json (upstream Native login HALError)'} )
                page.goto(BASE+'/logout',wait_until='domcontentloaded',timeout=60000)
                check(prefix+'-LOGOUT','Native API rejects expired browser session',ctx.request.get(BASE+'/api/v3/users/me').status==401)
                page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=60000)
                check(prefix+'-SESSION','Assistant redirects unauthenticated session to login',page.locator('#username').count()==1)
            except Exception as error:
                check(prefix+'-FLOW','Complete isolated browser workflow',False,{'error_type':type(error).__name__})
                if authenticated:
                    (PRIVATE/('browser-'+role+'-failure.html')).write_text(page.content())
            finally:
                ctx.close()
        browser.close()
    result['finished_at']=time.time();result['passed']=all(c['status']=='PASS' for c in result['checks'])
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({'evidence':str(output),'passed':result['passed'],'checks':len(result['checks']),
        'failed':[c['id'] for c in result['checks'] if c['status']=='FAIL']},indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'failed':True,'error_type':type(error).__name__,'details_private':True}))
        raise SystemExit(1)
