"""Semantic/API/browser qualification for Native configuration, isolated clone only."""
import json
import time
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl,urlencode
from playwright.sync_api import sync_playwright,expect
from native_configure_views import Configuration,OUT
from browser_clone_uat import otp

def main():
    config=Configuration('clone');assert config.base.endswith(':18088')
    clone=json.loads((OUT/'clone.json').read_text());private=Path(clone['private'])
    accounts=json.loads((private/'browser-accounts.json').read_text())['users']
    pm=next(a for a in accounts if a['role']=='PM')
    manifest=json.loads((OUT/'clone-native-views-configuration.json').read_text(encoding='utf8'))
    boards=[e for e in manifest['events'] if e['kind']=='board']
    gantt=next(e for e in manifest['events'] if e['kind']=='query')
    result={'scope':'CLONE_ONLY','checks':[],'main_writes':0,'provider_calls':0}
    def check(name,passed,actual=None):
        result['checks'].append({'id':name,'status':'PASS' if passed else 'FAIL','actual':actual})
        (OUT/'native-views-clone-qualification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    def rows_for_query(identifier):
        query=config.call('/api/v3/queries/'+str(identifier))
        link=urlsplit(query['_links']['results']['href'])
        params=[(k,v) for k,v in parse_qsl(link.query,keep_blank_values=True) if k not in ('pageSize','offset')]
        path=link.path+'?'+urlencode(params)
        rows=config.collection(path)
        check(f'query-{identifier}-project-scope',query['_links']['project']['href']=='/api/v3/projects/5' and not query['includeSubprojects'] and all(r['_links']['project']['href']=='/api/v3/projects/5' for r in rows))
        return rows
    packages=config.collection('/api/v3/projects/5/work_packages');by_id={w['id']:w for w in packages}
    check('baseline-329',len(packages)==329,len(packages))
    all_gantt=rows_for_query(gantt['id']);check('gantt-all-329',set(w['id'] for w in all_gantt)==set(by_id))
    expected_columns={'status':7,'assignee':6,'subtasks':5,'version':4}
    for event in boards:
        board=config.call('/api/v3/grids/'+str(event['id']));attribute=board['options']['attribute']
        widgets=sorted(board['widgets'],key=lambda w:w['startColumn'])
        check(f'board-{attribute}-native-type',board['options']['type']=='action' and len(widgets)==expected_columns[attribute])
        seen=[]
        for widget in widgets:
            rows=rows_for_query(widget['options']['queryId']);ids={w['id'] for w in rows};seen+=list(ids)
            filt=widget['options']['filters'][0];name,rule=next(iter(filt.items()));values=rule['values']
            if attribute=='status':expected={w['id'] for w in packages if w['_links']['status']['href'].rsplit('/',1)[-1] in values}
            elif attribute=='assignee':expected={w['id'] for w in packages if (not w['_links'].get('assignee',{}).get('href') if rule['operator']=='!*' else (w['_links'].get('assignee',{}).get('href') or '').rsplit('/',1)[-1] in values)}
            elif attribute=='subtasks':expected={w['id'] for w in packages if (w['_links'].get('parent',{}).get('href') or '').rsplit('/',1)[-1] in values}
            else:expected={w['id'] for w in packages if (w['_links'].get('version',{}).get('href') or '').rsplit('/',1)[-1] in values}
            check(f'board-{attribute}-column-{widget["startColumn"]}-actual-cards',ids==expected,{'actual':len(ids),'expected':len(expected)})
        if attribute in ('status','assignee'):check('board-'+attribute+'-coverage',set(seen)==set(by_id),len(set(seen)))
        if attribute=='version':check('version-board-real-undated-versions',all(f'"version_id"' in json.dumps(w['options']['filters']) for w in widgets))
    for a in accounts:
        if a['role']=='PM':continue
        from gateway.native import Native,NativeError
        native=Native(config.base,a['token'],5)
        try:
            native.call('/api/v3/grids/'+str(boards[0]['id']),'PATCH',{'name':'UNAUTHORIZED_CLONE_CONFIGURATION'})
            denied=False
        except NativeError as error:denied=error.status in (403,404)
        check(a['role']+'-board-config-write-denied',denied)
    shots=OUT/'native-views-clone-screenshots';shots.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(viewport={'width':1920,'height':1080});page=ctx.new_page();page.set_default_timeout(45000)
        try:
            page.goto(config.base+'/login',wait_until='domcontentloaded')
            page.locator('#username').fill(pm['login']);page.locator('#password').fill(pm['password'])
            page.locator('form:has(#username) button[type=submit]').click();page.locator('#otp').wait_for()
            if time.time()%30>26:time.sleep(4)
            page.locator('#otp').fill(otp(pm['totp_secret']));page.locator('input[type=submit][name=login]').click()
            page.wait_for_load_state('domcontentloaded')
            for event in boards:
                response=page.goto(config.base+'/projects/qldapm-local/boards/'+str(event['id']),wait_until='domcontentloaded')
                board=config.call('/api/v3/grids/'+str(event['id']));attribute=board['options']['attribute']
                expect(page.locator('.op-board-list')).to_have_count(expected_columns[attribute],timeout=60000)
                page.locator('.op-board-list--header').first.wait_for()
                check('ui-'+attribute+'-columns',response.status==200 and page.locator('.op-board-list').count()==expected_columns[attribute])
                check('ui-'+attribute+'-no-load-errors',page.locator('.op-board-list--toaster-box.-error').count()==0)
                page.screenshot(path=str(shots/(attribute+'.png')))
            response=page.goto(config.base+'/projects/qldapm-local/gantt?query_id='+str(gantt['id']),wait_until='domcontentloaded')
            page.locator('tr.wp-row-38').wait_for(timeout=60000)
            roots=page.locator('tr.wp-table--row').evaluate_all("es=>es.filter(e=>[38,39,40,41,42,43,44,45,46,47,48].some(i=>e.classList.contains('wp-row-'+i))).length")
            check('gantt-11-root-rows',roots==11,roots)
            row=page.locator('tr.wp-row-38')
            indicator=row.locator('.wp-table--hierarchy-indicator')
            before=indicator.get_attribute('class')
            indicator.click();page.wait_for_timeout(700)
            after=indicator.get_attribute('class')
            check('gantt-root-toggle',after!=before)
            page.wait_for_timeout(1800)
            check('gantt-user-toggle-not-recollapsed',indicator.get_attribute('class')==after)
            page.screenshot(path=str(shots/'gantt.png'))
            workload=next(b for b in boards if 'Workload' in b['name'])
            page.goto(config.base+'/projects/qldapm-local/boards/'+str(workload['id']),wait_until='domcontentloaded')
            card=page.locator('wp-single-card[data-work-package-id="49"]')
            card.wait_for(timeout=60000)
            target=page.locator('.op-board-list[data-query-name$=" — BE"] .drop-zone')
            target.wait_for();card.scroll_into_view_if_needed()
            before=config.call('/api/v3/work_packages/49');old=before['_links']['assignee']['href']
            check('dd-card-native-draggable',card.locator('[data-qa-draggable]').count()==1)
            card.drag_to(target)
            moved=False
            for _ in range(12):
                current=config.call('/api/v3/work_packages/49')
                if current['_links']['assignee']['href']=='/api/v3/users/21':moved=True;break
                page.wait_for_timeout(500)
            check('dd-assignee-native-readback',moved)
            if moved:
                config.call('/api/v3/work_packages/49','PATCH',{'lockVersion':current['lockVersion'],'_links':{'assignee':{'href':old}}})
                restored=config.call('/api/v3/work_packages/49')
                check('dd-original-business-values-restored',restored['_links']['assignee']['href']==old and restored['subject']==before['subject'] and restored['_links']['status']==before['_links']['status'])
                result['clone_wp49_revision_and_journal_changes']='Expected native audit from authorized clone drag/revert; Main unchanged'
        except Exception as error:
            check('ui-exception',False,{'type':type(error).__name__,'message':str(error)[:900]})
            if '/login' not in page.url:
                page.screenshot(path=str(shots/'failure.png'))
                (shots/'failure.txt').write_text(page.locator('body').inner_text(),encoding='utf8')
        finally:ctx.close();browser.close()
    result['passed']=all(c['status']=='PASS' for c in result['checks'])
    (OUT/'native-views-clone-qualification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'failed':[c for c in result['checks'] if c['status']=='FAIL']}))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
