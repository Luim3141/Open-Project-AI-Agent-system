"""Reuse existing real MAIN clicks, add Phase 4 RAG read/answer/source and DOM inventory."""
from pathlib import Path
OUT=Path(__file__).resolve().parent
original=OUT.parent/'functional-audit/browser_uat.py'
source=original.read_text(encoding='utf-8')
inventory='''    report['dom_inventory']=p.locator('#qldapm-command-center button,#qldapm-command-center a,#qldapm-command-center select').evaluate_all('''+repr("nodes=>nodes.map(n=>({tag:n.tagName,text:(n.innerText||n.getAttribute('aria-label')||'').trim().slice(0,160),href:n.getAttribute('href'),disabled:n.disabled,action:n.dataset.action,tab:n.dataset.tab,form_tool:n.form?.querySelector('[name=tool]')?.value}))")+''')
'''
source=source.replace("    for tab in [",inventory+"    for tab in [",1)
extra='''    def phase4_rag():
        p.locator('[data-tab="tab-knowledge"]').click()
        query=p.get_by_role('searchbox',name='Câu hỏi tìm evidence trong Second Brain',exact=True)
        query.fill('Tài liệu có mã ORBIT-RECEIPT-20261103 nói gì và có chứng nhận Owner acceptance không?')
        p.get_by_label('Chế độ truy vấn tri thức',exact=True).select_option('answer')
        with p.expect_response(lambda r:r.request.method=='POST' and '/qldapm-ai/commands' in r.url,timeout=115000) as response:
            p.get_by_role('button',name='Tìm kiếm Tri thức',exact=True).click()
        r=response.value;packet=r.json();assert r.status==200
        p.wait_for_function('()=>document.querySelector("#qcc-knowledge-results").getAttribute("aria-busy")==="false"',timeout=115000)
        result=p.locator('#qcc-knowledge-results');text=result.inner_text()
        assert 'SUPPORTED' in text and 'does not certify' in text and 'Owner acceptance' in text,text[:800]
        assert result.locator('blockquote').count()>0
        p.screenshot(path=str(OUT/'main-rag-answer.png'),full_page=True)
        answer={'text':text,'request_id':r.headers.get('x-qldapm-request-id') or r.headers.get('x-request-id'),'quotes':result.locator('blockquote').all_inner_texts()}
        with p.expect_response(lambda r:r.request.method=='POST' and '/qldapm-ai/commands' in r.url,timeout=30000) as response:
            result.get_by_role('button',name='Đọc nội dung đúng source pin',exact=True).first.click()
        file_response=response.value;assert file_response.status==200
        file_packet=file_response.json();answer['file_read']=file_packet
        assert 'ORBIT-RECEIPT-20261103' in str(file_packet) and 'does not certify' in str(file_packet)
        p.set_viewport_size({'width':390,'height':844})
        p.locator('[data-tab="tab-knowledge"]').click()
        dims=p.locator('form').filter(has=query).locator('.qcc-search-bar').evaluate('n=>({width:n.clientWidth,scroll:n.scrollWidth})')
        assert dims['width']>100 and dims['scroll']<=dims['width']+1,dims
        p.screenshot(path=str(OUT/'main-rag-mobile.png'),full_page=True)
        p.set_viewport_size({'width':1440,'height':1000})
        answer['mobile_form']=dims
        return answer
    check('phase4_actual_gemini_answer_citations_source_read_mobile',phase4_rag)
'''
source=source.replace('    def studio():',extra+'    def studio():',1)
exec(compile(source,str(original),'exec'),{'__name__':'__main__','__file__':str(OUT/'browser_probe_uat.py')})
