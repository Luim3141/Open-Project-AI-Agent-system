"""Headless read-only Main UI check; credentials and TOTP stay in process memory."""
import json
import sys
import os
from pathlib import Path
import subprocess
import time

from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parent
RUNTIME=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
BASE='http://127.0.0.1:18088'
PATH='/projects/ai-dev-demo/qldapm-ai/observer'


def main():
    preview='--preview-css' in sys.argv
    task_id=int(sys.argv[sys.argv.index('--task-id')+1]) if '--task-id' in sys.argv else 391
    assert task_id in {391,397}
    account=json.loads((RUNTIME/'openproject-ai/telegram-ai/ui-uat.json').read_text(encoding='utf-8-sig'))
    assert account.get('login') and account.get('password'),'CURRENT_UI_LOGIN_REQUIRED_IN_LOCAL_FILE'
    ruby="""require 'json'
Rails.logger=Logger.new(File::NULL);ActiveRecord::Base.logger=nil
packet={}
ActiveRecord::Base.transaction do
 ActiveRecord::Base.connection.execute('SET TRANSACTION READ ONLY')
 user=User.active.find_by!(login:ARGV.fetch(0));packet={user_id:user.id}
 d=TwoFactorAuthentication::Device::Totp.find_by(user_id:user.id,active:true,default:true)
 if d
  base=Time.now.to_i/30*30
  packet.merge!(last_used_at:d.last_used_at,codes:(0..6).to_h{|i| at=base+i*30;[at,d.totp.at(at)]})
 end
end
puts 'PRIVATE_PACKET='+JSON.generate(packet)
"""
    result=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-',account['login']],
        input=ruby,text=True,capture_output=True,timeout=120)
    assert result.returncode==0,'READ_ONLY_OWNER_FACTOR_FAILED'
    packet=json.loads(next(line.split('=',1)[1] for line in result.stdout.splitlines() if line.startswith('PRIVATE_PACKET=')))
    report={'method':'PLAYWRIGHT_EDGE_HEADLESS_MAIN','css_preview_only':preview,'checks':{},'model_calls':0,'business_writes':0}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page()
        try:
            page.goto(BASE+'/login',wait_until='domcontentloaded',timeout=60000)
            page.locator('#username').fill(account['login']);page.locator('#password').fill(account['password'])
            page.locator('form:has(#username) button[type=submit]').click()
            me=context.request.get(BASE+'/api/v3/users/me')
            if me.status!=200 and packet.get('codes'):
                page.locator('#otp').wait_for(timeout=15000)
                slot=max(int(time.time()//30)*30,(int(packet.get('last_used_at') or 0)//30+1)*30)
                if slot>time.time():time.sleep(min(31,slot-time.time()+1))
                code=packet['codes'][str(int(time.time()//30)*30)]
                page.locator('#otp').fill(code);page.locator('input[type=submit][name=login]').click()
            me=context.request.get(BASE+'/api/v3/users/me');assert me.status==200 and me.json()['id']==packet['user_id'],'CURRENT_LOGIN_FAILED'
            report['checks']['real_authenticated_login']=True
            print('UI_PHASE LOGIN_VERIFIED',flush=True)
            response=page.goto(BASE+PATH,wait_until='domcontentloaded',timeout=120000)
            report['observer_http_status']=response.status
            report['native_actor_id']=packet['user_id']
            if response.status!=200:report['page_title']=page.title();report['page_error_excerpt']=page.locator('body').inner_text()[-800:]
            assert response.status==200
            if preview:
                source=(OUT.parents[1]/'openproject/ai/core/overlay/app/views/qldapm_ai/observer.html.erb').read_text(encoding='utf-8')
                page.add_style_tag(content=source.split('</style>',1)[0].split('>',3)[-1])
            page.locator('#qobs-connection').filter(has_text='Đã đồng bộ').wait_for(timeout=90000)
            report['checks']['html_and_live_list']=True
            print('UI_PHASE LIVE_LIST_VERIFIED',flush=True)
            page.locator('#qobs-task-id').fill(str(task_id));page.locator('#qobs-filter button[type=submit]').click()
            page.locator('#qobs-title').filter(has_text='#'+str(task_id)).wait_for(timeout=90000)
            response=context.request.get(BASE+PATH+'.json?task_id='+str(task_id),timeout=90000)
            assert response.status==200
            snapshot=response.json()
            assert snapshot['workflow_status'] in page.locator('#qobs-summary').inner_text()
            assert page.locator('.qobs-stage').count()==len(snapshot['stages'])
            assert page.locator('#qobs-events tr').count()==len(snapshot['events'])
            report['checks']['same_canonical_snapshot']=True
            if snapshot['stages']:
                page.locator('.qobs-stage summary').first.click()
                assert page.locator('.qobs-stage[open]').count()==1
            report.update(task_id=task_id,workflow_status=snapshot['workflow_status'],acceptance=snapshot['acceptance_status'],
                stages=len(snapshot['stages']),runs=len(snapshot['runs']),events=len(snapshot['events']))
            failures={'remaining':1}
            def transient_client_failure(route):
                if failures['remaining']:
                    failures['remaining']-=1
                    route.fulfill(status=503,content_type='application/json',body='{"error":"CLIENT_UAT_FAILURE"}')
                else:route.continue_()
            pattern='**/qldapm-ai/observer.json*'
            page.route(pattern,transient_client_failure)
            page.locator('#qobs-filter button[type=submit]').click()
            page.locator('#qobs-connection').filter(has_text='HTTP 503').wait_for(timeout=90000)
            assert page.locator('#qobs-connection').evaluate('(el)=>el.classList.contains("qobs-warning")')
            page.locator('#qobs-filter button[type=submit]').click()
            page.locator('#qobs-connection').filter(has_text='Đã đồng bộ').wait_for(timeout=90000)
            assert not page.locator('#qobs-connection').evaluate('(el)=>el.classList.contains("qobs-warning")')
            page.unroute(pattern,transient_client_failure)
            report['checks']['client_503_recovery']=True
            page.screenshot(path=str(OUT/('agent-studio-task397.png' if task_id==397 else 'agent-studio-main.png')),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            report['mobile_overflow']=page.locator('#qldapm-agent-studio').evaluate('(el)=>({client:el.clientWidth,scroll:el.scrollWidth,children:[...el.querySelectorAll("*")].filter(x=>x.scrollWidth>x.clientWidth+2).slice(0,10).map(x=>({tag:x.tagName,id:x.id,class:x.className,client:x.clientWidth,scroll:x.scrollWidth}))})')
            page.screenshot(path=str(OUT/('agent-studio-task397-mobile.png' if task_id==397 else 'agent-studio-mobile-preview.png' if preview else 'agent-studio-mobile.png')),full_page=True)
            assert page.locator('#qldapm-agent-studio').evaluate('(el)=>el.scrollWidth<=el.clientWidth+2')
            report['checks']['mobile_layout']=True
            page.set_viewport_size({'width':1440,'height':1000})
            denied=context.request.get(BASE+PATH+'.json?task_id=1',timeout=90000)
            assert denied.status in {403,404},'CROSS_PROJECT_READ_NOT_DENIED'
            report['checks']['cross_project_denied']=True
            page.reload(wait_until='domcontentloaded',timeout=120000)
            page.locator('#qobs-connection').filter(has_text='Đã đồng bộ').wait_for(timeout=90000)
            report['checks']['reload']=True
            report['status']='PASS'
        except Exception as error:
            report.update(status='FAILED',error_type=type(error).__name__);raise
        finally:
            context.close();browser.close()
            (OUT/('ui-smoke-397.json' if task_id==397 else 'ui-smoke-preview.json' if preview else 'ui-smoke.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
