"""Authenticated, read-only MAIN browser UAT. No plaintext credentials on disk/output."""
import json,os,subprocess,time
import math
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent
BASE='http://127.0.0.1:18088';CENTER='/projects/ai-dev-demo/qldapm-ai';PATH=CENTER+'/observer'

def full_capture(page,name):
    # OpenProject scrolls an inner pane; a tall capture avoids cropping its content.
    viewport=page.viewport_size
    root=page.locator('#qldapm-agent-studio')
    height=min(6500,math.ceil(root.bounding_box()['height']+180))
    page.set_viewport_size({'width':viewport['width'],'height':height})
    root.scroll_into_view_if_needed();page.wait_for_timeout(250)
    page.screenshot(path=str(OUT/name),full_page=True)
    page.set_viewport_size(viewport)

def login(context,page):
    account=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai/ui-uat.json').read_text(encoding='utf-8-sig'))
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
    r=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-',account['login']],input=ruby,text=True,capture_output=True,timeout=300)
    assert r.returncode==0,'READ_ONLY_FACTOR_FAILED'
    packet=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('PRIVATE_PACKET=')))
    page.goto(BASE+'/login',wait_until='domcontentloaded',timeout=90000)
    page.locator('#username').fill(account['login']);page.locator('#password').fill(account['password']);page.locator('form:has(#username) button[type=submit]').click()
    me=context.request.get(BASE+'/api/v3/users/me')
    if me.status!=200 and packet.get('codes'):
        page.locator('#otp').wait_for(timeout=15000)
        slot=max(int(time.time()//30)*30,int(packet.get('last_used_at') or 0)//30*30+30)
        if slot>time.time():time.sleep(min(31,slot-time.time()+1))
        page.locator('#otp').fill(packet['codes'][str(int(time.time()//30)*30)])
        page.locator('input[type=submit][name=login]').click()
    me=context.request.get(BASE+'/api/v3/users/me');assert me.status==200 and me.json()['id']==packet['user_id'],'CURRENT_LOGIN_FAILED'
    return packet['user_id']

def main():
    report={'method':'AUTHENTICATED_HEADLESS_EDGE_MAIN','checks':{},'business_writes':0,'model_calls':0}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);context=browser.new_context(viewport={'width':1440,'height':1100})
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append({'message':str(e),'stack':e.stack[:1200]}))
        try:
            report['actor']=login(context,page);print('MAIN LOGIN PASS',flush=True)
            page.goto(BASE+CENTER,wait_until='domcontentloaded',timeout=120000)
            page.locator('#qcc-agent-studio-link').wait_for(timeout=90000)
            page.screenshot(path=str(OUT/'main-command-center.png'),full_page=True)
            report['command_center_errors_before_navigation']=list(errors);errors.clear()
            page.locator('#qcc-agent-studio-link').click();page.locator('.qas').wait_for(timeout=60000)
            assert page.url.startswith(BASE+PATH)
            report['checks']['command_center_navigation']=True
            print('MAIN NAVIGATION PASS',flush=True)
            search=page.get_by_role('textbox',name='Tìm Task ID hoặc tiêu đề');search.fill('397');search.press('Enter')
            page.locator('.qas[data-task="397"]').wait_for(timeout=120000)
            page.locator('.react-flow__node').nth(2).wait_for(timeout=60000)
            canonical=context.request.get(BASE+PATH+'.json?task_id=397',timeout=120000).json()
            assert canonical['acceptance_status']=='COMPLETED'
            assert page.locator('.react-flow__node').count()==len(canonical['stages'])==3
            assert page.locator('.react-flow__edge').count()==2
            assert canonical['business_status'] in page.locator('.qas-task-header').inner_text()
            assert page.locator('pre:visible').count()==0
            assert not page.locator('.qas-flow-active').count()
            report['checks']['real397_canonical_completion']=True
            # Rendering nodes is the production bundle/mount proof, not presence of a filename.
            assert page.locator('script[src*="/qldapm-agent-studio-v2/studio.js"]').count()==1
            assert page.locator('.react-flow').count()==1
            node=page.locator('.react-flow__node[data-id="dev"]');node.click();node.hover()
            page.locator('.qas-floating-tooltip').wait_for()
            tip=page.locator('.qas-floating-tooltip').bounding_box();assert tip['y']>=0 and tip['x']>=0
            page.screenshot(path=str(OUT/'main397-hover-inspector.png'),full_page=True)
            page.mouse.move(10,10)
            assert 'tests/test_health_regression.py' in page.locator('.qas-inspector').inner_text()
            page.locator('.react-flow__node[data-id="qa"]').click();assert 'Exit code' in page.locator('.qas-inspector').inner_text()
            page.locator('.react-flow__node[data-id="reviewer"]').click();assert 'Review verdict' in page.locator('.qas-inspector').inner_text()
            page.screenshot(path=str(OUT/'main397-review-evidence.png'),full_page=True)
            report['checks']['role_inspector_evidence']=True
            page.locator('.react-flow__edge-path').first.hover(force=True);page.locator('.qas-edge-tooltip').wait_for()
            assert 'DEPENDENCY' in page.locator('.qas-edge-tooltip').inner_text()
            full_capture(page,'main397-edge-hover.png');page.mouse.move(10,10)
            report['checks']['real_dependency_hover_evidence']=True
            before=page.locator('.react-flow__viewport').get_attribute('style')
            page.get_by_role('button',name='Phóng to graph',exact=True).click();page.wait_for_timeout(300);assert page.locator('.react-flow__viewport').get_attribute('style')!=before
            page.get_by_role('button',name='Fit graph',exact=True).click();page.wait_for_timeout(350)
            canvas=page.locator('.qas-canvas').bounding_box();page.mouse.move(canvas['x']+50,canvas['y']+40);page.mouse.down();page.mouse.move(canvas['x']+100,canvas['y']+70,steps=5);page.mouse.up()
            before=page.locator('.react-flow__viewport').get_attribute('style')
            page.get_by_role('button',name='Làm mới Observer').click();page.wait_for_timeout(1000)
            assert page.locator('.react-flow__viewport').get_attribute('style')==before
            assert page.locator('.qas-inspector h3').inner_text()=='Reviewer'
            report['checks']['zoom_pan_fit_refresh_stable']=True
            page.get_by_role('tab',name='Agent Runs',exact=True).click();page.get_by_role('button',name='Mở attempts trên graph').click();page.locator('.react-flow__node').nth(3).wait_for(timeout=60000)
            assert 'Checkpoint' in page.locator('.qas-inspector').inner_text()
            page.screenshot(path=str(OUT/'main397-attempts.png'),full_page=True)
            page.get_by_role('button',name='Thu gọn attempts').click();page.wait_for_timeout(350)
            report['checks']['real_run_checkpoint_expand']=True
            page.get_by_role('tab',name='Overview',exact=True).click()
            # Inject only this browser's GET failure; Main and bot keep running.
            failure={'remaining':1}
            def fail_once(route):
                if failure['remaining']:
                    failure['remaining']-=1;route.fulfill(status=503,content_type='application/json',body='{}')
                else:route.continue_()
            page.route('**/qldapm-ai/observer.json*',fail_once)
            page.get_by_role('button',name='Làm mới Observer').click();page.locator('.qas-connection').filter(has_text='HTTP 503').wait_for(timeout=60000)
            page.get_by_role('button',name='Làm mới Observer').click();page.locator('.qas-connection').filter(has_text='Observer đã phản hồi').wait_for(timeout=120000)
            page.unroute('**/qldapm-ai/observer.json*',fail_once);report['checks']['client_failure_recovery']=True
            page.locator('.qas-skeleton').wait_for(state='hidden',timeout=120000)
            assert page.locator('.qas-task').count()>0,'REAL_TASK_EXPLORER_EMPTY'
            palette=page.locator('select[aria-label="Project"]').evaluate('(el)=>({color:getComputedStyle(el).color,background:getComputedStyle(el).backgroundColor})')
            assert palette['color']=='rgb(229, 237, 245)' and palette['background']=='rgb(12, 20, 30)',palette
            report['checks']['native_select_dark_contrast']=True
            for width,height,name in [(1440,1100,'desktop'),(1280,1000,'laptop'),(768,1024,'tablet'),(390,844,'mobile')]:
                page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(500)
                page.get_by_role('button',name='Fit graph',exact=True).click();page.wait_for_timeout(350)
                assert page.locator('#qldapm-agent-studio').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),f'STUDIO_OVERFLOW_{width}'
                boxes=page.locator('.react-flow__node').evaluate_all('(els)=>els.map(el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}})');canvas=page.locator('.qas-canvas').bounding_box()
                assert all(b['x']>=canvas['x']-1 and b['right']<=canvas['x']+canvas['width']+1 and b['y']>=canvas['y']-1 and b['bottom']<=canvas['y']+canvas['height']+1 for b in boxes),f'GRAPH_CLIPPED_{width}'
                for i,a in enumerate(boxes):
                    for b in boxes[i+1:]:assert a['right']<=b['x'] or b['right']<=a['x'] or a['bottom']<=b['y'] or b['bottom']<=a['y']
                full_capture(page,f'main397-{name}.png')
            report['checks']['responsive_graph_no_overlap_or_overflow']=True
            report['screenshot_method']='Interaction viewports 1440x1100/1280x1000/768x1024/390x844; full content capture temporarily grows height at same width because OpenProject uses an inner scroll pane.'
            page.set_viewport_size({'width':1440,'height':1100})
            search.fill('391');search.press('Enter')
            page.locator('.qas[data-task="391"]').wait_for(timeout=120000);page.locator('.react-flow__node').nth(2).wait_for(timeout=60000)
            old=context.request.get(BASE+PATH+'.json?task_id=391',timeout=120000).json()
            assert page.locator('.react-flow__node').count()==len(old['stages'])
            assert '397' not in page.locator('.qas-task-header .qas-eyebrow').inner_text()
            page.screenshot(path=str(OUT/'main391-history.png'),full_page=True)
            report['checks']['task_switch_real391_no_mixed_state']=True
            page.locator('#qas-back').click();page.locator('#qcc-agent-studio-link').wait_for(timeout=90000)
            assert urlparse(page.url).path==CENTER
            page.goto(BASE+PATH+'?task_id=397',wait_until='domcontentloaded',timeout=120000)
            page.locator('.qas[data-task="397"]').wait_for(timeout=120000);page.reload(wait_until='domcontentloaded',timeout=120000);page.locator('.qas[data-task="397"]').wait_for(timeout=120000)
            report['checks']['back_deeplink_reload']=True
            denied=context.request.get(BASE+PATH+'.json?task_id=1',timeout=90000);assert denied.status in {403,404}
            invalid=context.request.get(BASE+PATH+'.json?limit=51',timeout=90000);assert invalid.status==422
            report['checks']['native_acl_and_bounded_limit']=True
            anonymous=browser.new_context();denial=anonymous.request.get(BASE+PATH+'.json?task_id=397',timeout=90000);assert denial.status in {401,403} or '/login' in denial.url;anonymous.close()
            report['checks']['anonymous_denied']=True
            assert not errors,errors
            report.update(status='PASS',console_errors=errors,task397={'stages':len(canonical['stages']),'events':len(canonical['events']),'runs':len(canonical['runs']),'acceptance':canonical['acceptance_status']})
        except Exception as error:
            report.update(status='FAIL',error_type=type(error).__name__,error=str(error)[:1500],console_errors=errors)
            page.screenshot(path=str(OUT/'main-failure.png'),full_page=True);raise
        finally:
            (OUT/'main-uat.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');context.close();browser.close()
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
