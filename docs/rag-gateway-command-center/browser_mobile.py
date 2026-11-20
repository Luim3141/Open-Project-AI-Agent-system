"""Visible MAIN mobile form, no provider invocation; 0x0 hidden elements are not evidence."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'agent-studio-v2-stabilization'))
from browser_probe import authenticated,BASE,STUDIO
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page();p.set_viewport_size({'width':390,'height':844})
    p.goto(BASE+STUDIO.removesuffix('/observer'),wait_until='domcontentloaded',timeout=90000)
    inventory=p.locator('#qldapm-command-center button,#qldapm-command-center a,#qldapm-command-center select').evaluate_all('''nodes=>nodes.map(n=>({tag:n.tagName,text:(n.innerText||n.getAttribute('aria-label')||'').trim().slice(0,160),component:n.closest('.qcc-tab-pane')?.id||'global',class:n.className,href:n.getAttribute('href'),disabled:n.disabled,action:n.dataset.action,tab:n.dataset.tab,form_tool:n.form?.querySelector('[name=tool]')?.value,form_action:n.form?.getAttribute('action'),form_method:n.form?.method}))''')
    (OUT/'main-dom-inventory.json').write_text(json.dumps({'scope':'Actual authenticated MAIN DOM, no control writes or inference','controls':inventory},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p.locator('[data-tab="tab-knowledge"]').click()
    query=p.get_by_role('searchbox',name='Câu hỏi tìm evidence trong Second Brain',exact=True)
    assert query.is_visible()
    query.scroll_into_view_if_needed()
    dims=query.locator('xpath=ancestor::form').evaluate('n=>{const bar=n.querySelector(".qcc-search-bar");return {width:bar.clientWidth,scroll:bar.scrollWidth,box:bar.getBoundingClientRect().toJSON(),formBox:n.getBoundingClientRect().toJSON()}}')
    assert dims['width']>100 and dims['box']['height']>20 and dims['scroll']<=dims['width']+1,dims
    assert dims['box']['top']<844 and dims['box']['bottom']>0,dims
    p.screenshot(path=str(OUT/'main-rag-mobile-visible.png'),full_page=True)
    (OUT/'main-mobile.json').write_text(json.dumps({'scope':'ACTUAL authenticated MAIN 390px, visible knowledge form','layout':dims,'passed':True,'supersedes':'browser-uat.json mobile_form 0x0 used clientWidth on inline form; visible bounding box is nonzero. Search-bar measurement is the correct overflow proof.'},indent=2)+'\n')
    c.close();b.close()
print(json.dumps(dims))
