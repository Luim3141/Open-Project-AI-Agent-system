"""Actual registered-file form and visible source readback, no Gemini invocation."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'agent-studio-v2-stabilization'))
from browser_probe import authenticated,BASE,STUDIO
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page()
    p.goto(BASE+STUDIO.removesuffix('/observer'),wait_until='domcontentloaded',timeout=90000)
    p.locator('[data-tab="tab-knowledge"]').click()
    mode=p.get_by_label('Chế độ truy vấn tài liệu đã đăng ký',exact=True);mode.select_option('answer')
    form=mode.locator('xpath=ancestor::form');form.locator('[name="knowledge_query"]').fill('ORBIT-RECEIPT-20261103')
    with p.expect_response(lambda r:r.request.method=='POST' and '/qldapm-ai/commands' in r.url,timeout=115000) as response:form.get_by_role('button').click()
    r=response.value;packet=r.json();assert r.status==200 and packet['result']['model_used'] is False
    result=p.locator('#qcc-knowledge-results');result.locator('blockquote').first.wait_for(timeout=30000)
    assert result.is_visible() and 'does not certify' in result.inner_text() and 'EXTRACTS_AVAILABLE' in result.inner_text()
    result.scroll_into_view_if_needed();result.screenshot(path=str(OUT/'main-file-extract-visible.png'))
    with p.expect_response(lambda r:r.request.method=='POST' and '/qldapm-ai/commands' in r.url,timeout=30000) as response:result.get_by_role('button',name='Đọc nội dung đúng source pin',exact=True).click()
    r=response.value;file_packet=r.json();assert r.status==200
    output=p.locator('#qcc-business-action-output');output.wait_for()
    assert 'does not certify' in output.inner_text() and 'ORBIT-RECEIPT-20261103' in output.inner_text()
    output.scroll_into_view_if_needed();output.screenshot(path=str(OUT/'main-file-read-visible.png'))
    report={'scope':'Actual MAIN authenticated file-only form, modeanswer is extract not Gemini; source opened visibly','checks':{'file_form_extract':True,'model_used_false':True,'visible_citations':True,'visible_pinned_readback':True},'extract':packet,'readback':file_packet}
    (OUT/'main-file-ui.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    c.close();b.close()
print(json.dumps(report['checks']))
