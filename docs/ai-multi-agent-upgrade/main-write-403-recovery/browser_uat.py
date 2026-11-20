"""Real Chromium/Rails/worker/Native writes on isolated Main clone, provider test double only."""
import json
import argparse
import shutil
import os
import time
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from playwright.sync_api import sync_playwright
from inspect_runtime import ROOT, OUT, run
import sys
sys.path.insert(0,str(ROOT/'openproject/ai'))
from tests.remaining_browser_uat import otp
from gateway.native import Native

ASSISTANT='/projects/qldapm-local/qldapm-ai'

def main():
    output=OUT/'clone-browser-results.json'
    parser=argparse.ArgumentParser();parser.add_argument('--after-clone-permission-fix',action='store_true');parser.add_argument('--resume-proposal');args=parser.parse_args()
    if args.resume_proposal:
        old=json.loads(output.read_text());assert old['created_child']==367 and old['checks'][-1]['id']=='WRITE-11-PREVIEW'
        shutil.copy2(output,OUT/'clone-browser-preview-wait-failed.json')
    elif args.after_clone_permission_fix:
        old=json.loads(output.read_text());assert len(old['checks'])==1 and old['clone_before_count']==329
        assert json.loads((OUT/'native-permission-before.json').read_text())['clone_permission_change']['passed']
        shutil.copy2(output,OUT/'clone-browser-initial-blocked.json')
    else:assert not output.exists(),'UAT_ALREADY_STARTED_RECONCILE_BEFORE_REPEAT'
    q=json.loads((OUT/'qualification.json').read_text());private=Path(q['private']);base=q['base']
    users=json.loads((private/'browser-accounts.json').read_text())['users']
    credentials=json.loads((private/'clone-state/credentials.json').read_text())
    config=json.loads((private/'clone-state/config.json').read_text())
    pm=next(a for a in users if a['role']=='PM');native=lambda:Native(base,credentials[str(pm['id'])],5)
    types=native().collection('/api/v3/projects/5/types');subtask=next(t['id'] for t in types if t['name']=='Subtask')
    assert subtask in config['type_ids']
    (private/'clone-state/isolated-write-fixture.json').write_text(json.dumps({'parent_id':50,'type_id':subtask}))
    before=native().packages();before_ids={p['id'] for p in before}
    if args.resume_proposal:
        assert len(before)==330 and any(p['id']==367 for p in before),'UNEXPECTED_CLONE_STATE'
        before=[p for p in before if p['id']!=367]
    result={'mode':'MOCK_PROVIDER_NATIVE_REAL','images':{k:q[k] for k in ('core_image','gateway_image')},
            'checks':[],'google_calls':0,'main_business_mutations':0,'clone_before_count':len(before)}
    def save():output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    def check(case,passed,actual=None):
        result['checks'].append({'id':case,'status':'PASS' if passed else 'FAIL','actual':actual,'exit_code':0 if passed else 1});save()
        assert passed,case
    def login(browser,account):
        ctx=browser.new_context(viewport={'width':1366,'height':900})
        ctx.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base+'/') else route.abort())
        p=ctx.new_page();p.set_default_timeout(30000)
        p.goto(base+'/login',wait_until='domcontentloaded',timeout=90000)
        p.locator('#username').fill(account['login']);p.locator('#password').fill(account['password'])
        p.locator('form:has(#username) button[type=submit]').click();p.locator('#otp').wait_for()
        if time.time()%30>26:time.sleep(4)
        p.locator('#otp').fill(otp(account['totp_secret']));p.locator('input[type=submit][name=login]').click()
        p.wait_for_load_state('domcontentloaded')
        me=ctx.request.get(base+'/api/v3/users/me');check('LOGIN-'+account['role'],me.status==200 and me.json()['id']==account['id'])
        return ctx,p
    def submit(p,allow,scope='',engine='gemini',prompt=None):
        p.goto(base+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
        form=p.locator('form:has(select#engine)');form.locator('#engine').select_option(engine)
        form.locator('#prompt').fill(prompt or 'Tạo 1 subtask mới tên là test cho task 50, giao cho QA, tự sử dụng các agent thích hợp để làm.')
        form.locator('#allow_routine_writes').set_checked(allow);form.locator('#write_scope_ids').fill(scope)
        data=form.evaluate('(f)=>Object.fromEntries(new FormData(f))')
        with p.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/qldapm-ai/commands')) as response:
            form.locator('input[type=submit]').click()
        p.wait_for_load_state('domcontentloaded')
        return data,response.value.status
    def wait_run(p):
        identifier=parse_qs(urlparse(p.url).query).get('run_id',[None])[0]
        assert identifier,'NO_RUN_CREATED'
        p.locator('.qldapm-ai-result:not(.-running)').wait_for(timeout=120000)
        return identifier,p.locator('.qldapm-ai-result').inner_text()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        ctx,p=login(browser,pm);errors=[];p.on('pageerror',lambda e:errors.append(str(e)[:100]))
        if args.resume_proposal:
            result['checks'] += [c for c in old['checks'] if c['id']!='WRITE-11-PREVIEW' and not c['id'].startswith('LOGIN')]
            result.update(direct_run=old['direct_run'],created_child=367,test_harness_fix='Wait for Turbo navigation; no product assertion changed; original failure retained.')
            p.goto(base+ASSISTANT+'?proposal_id='+args.resume_proposal,wait_until='domcontentloaded')
        else:
            data,status=submit(p,True);identifier,text=wait_run(p)
            check('WRITE-02-03',status in (302,303) and 'Đã thực hiện thành công' in text,{'post':status,'run':identifier})
            after=native().packages();created=[r for r in after if r['id'] not in before_ids]
            check('WRITE-08-09',len(created)==1 and created[0]['subject']=='test' and created[0]['_links']['parent']['href']=='/api/v3/work_packages/50'
                  and created[0]['_links']['assignee']['href']=='/api/v3/users/23' and created[0]['_links']['type']['href']==f'/api/v3/types/{subtask}',
                  {'new_ids':[r['id'] for r in created],'parent':50,'assignee':23,'type':subtask})
            result['direct_run']=identifier;result['created_child']=created[0]['id'];save()
            p.screenshot(path=str(OUT/'clone-native-create.png'),full_page=False)
            duplicate=ctx.request.post(base+ASSISTANT+'/commands',form=data,max_redirects=0)
            check('WRITE-10',duplicate.status in (302,303) and identifier in duplicate.headers.get('location','') and len(native().packages())==len(before)+1,
                  {'status':duplicate.status,'same_run':identifier in duplicate.headers.get('location','')})
            _,status=submit(p,False,'50');proposal_run,text=wait_run(p)
            check('WRITE-04',status in (302,303) and 'chờ bạn duyệt' in text and len(native().packages())==len(before)+1)
            p.get_by_role('link',name='Xem thay đổi và duyệt',exact=True).click()
        p.locator('form[action$="/confirm"]').wait_for(timeout=30000)
        check('WRITE-11-PREVIEW',p.locator('form[action$="/confirm"]').count()==1)
        p.locator('form[action$="/confirm"] input[type=submit]').click();p.wait_for_load_state('domcontentloaded')
        check('WRITE-11-APPROVE',len(native().packages())==len(before)+2 and p.get_by_role('link',name='Mở công việc',exact=True).count()==1)
        _,status=submit(p,False,'50');wait_run(p)
        p.get_by_role('link',name='Xem thay đổi và duyệt',exact=True).click();p.locator('form[action$="/reject"]').wait_for(timeout=30000)
        p.locator('form[action$="/reject"] input[type=submit]').click();p.wait_for_load_state('domcontentloaded')
        check('WRITE-11-REJECT',len(native().packages())==len(before)+2)
        _,status=submit(p,True,'2.5')
        check('WRITE-12-SCOPE',status==422 and 'Phạm vi chỉ nhận ID nguyên dương' in p.locator('.qldapm-ai-result').inner_text())
        _,status=submit(p,True,'',engine='supervisor')
        check('WRITE-12-POLICY',status==403 and 'Supervisor local chỉ phân tích' in p.locator('.qldapm-ai-result').inner_text()
              and 'chưa sẵn sàng' not in p.locator('.qldapm-ai-result').inner_text())
        _,status=submit(p,False,engine='supervisor',prompt='BA và QA phân tích công việc #50; chỉ đọc; không ghi thay đổi.')
        local_run,text=wait_run(p);check('WRITE-01-13',status in (302,303) and 'LOCAL_DETERMINISTIC' in text)
        p.goto(base+ASSISTANT+'/executions/'+local_run,wait_until='domcontentloaded')
        p.locator('.em-node').first.wait_for(timeout=30000)
        check('WRITE-13-GRAPH',p.locator('.em-node').count()==5,{'nodes':p.locator('.em-node').count(),'run':local_run})
        p.screenshot(path=str(OUT/'clone-local-supervisor.png'),full_page=False)
        bad_csrf=ctx.request.post(base+ASSISTANT+'/commands',form={'prompt':'Đọc công việc 50','engine':'supervisor','authenticity_token':'invalid'})
        check('WRITE-07-CSRF',bad_csrf.status in (403,422),{'status':bad_csrf.status})
        check('BROWSER-CONSOLE',not errors,errors)
        ctx.close()
        for user in users:
            if user['role']=='PM':continue
            ctx,p=login(browser,user)
            _,status=submit(p,True)
            check('WRITE-05-'+user['role'],status==403 and 'Chỉ PM được tạo' in p.locator('.qldapm-ai-result').inner_text())
            ctx.close()
        browser.close()
    result['passed']=True;result['clone_after_count']=len(native().packages());save()
    print(json.dumps({'passed':True,'checks':len(result['checks']),'clone_created':2,'google_calls':0,'main_business_mutations':0}))

if __name__=='__main__':main()
