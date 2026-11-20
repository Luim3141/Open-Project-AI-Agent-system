"""Real Chromium layout of the actual Knowledge form/CSS, isolated from MAIN APIs."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
source=(ROOT/'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb').read_text(encoding='utf-8')
css='\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',source,re.S))
bar=source.split('<div class="qcc-search-bar">',1)[1].split('</div>',1)[0]
bar=re.sub(r'<%.*?%>','',bar,flags=re.S)
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True);p=b.new_page(viewport={'width':390,'height':700})
    p.set_content('<style>'+css+'</style><div id="qldapm-command-center" style="display:block;width:360px;margin:0;padding:0"><form class="qcc-knowledge-form"><div class="qcc-search-bar">'+bar+'</div></form></div>')
    state=p.locator('.qcc-search-bar').evaluate('(e)=>({client:e.clientWidth,scroll:e.scrollWidth,width:e.getBoundingClientRect().width})')
    p.screenshot(path=str(OUT/'mobile-knowledge-form.png'));b.close()
(OUT/'mobile-form.json').write_text(json.dumps({'scope':'ISOLATED actual template CSS + Chromium, not Main browser','layout':state,'passed':state['scroll']<=state['client']+1},indent=2)+'\n')
print(json.dumps(state));assert state['scroll']<=state['client']+1
