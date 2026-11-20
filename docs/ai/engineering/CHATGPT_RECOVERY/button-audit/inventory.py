"""Enumerate actual modern templates and retain every observed DOM control instance."""
import collections,csv,json,re
from pathlib import Path
OUT=Path(__file__).parent
ROOT=OUT.resolve().parents[4]
rows=[]
for file in sorted((ROOT/'openproject/ai/core/overlay/app/views/qldapm_ai').glob('_engineering*.erb')):
    if file.name=='_engineering_classic.html.erb':continue
    text=file.read_text(encoding='utf-8')
    for match in re.finditer(r'<button\b[^>]*(?:<%.*?%>[^>]*)?>.*?</button>',text,re.S):
        raw=match.group()
        label=re.sub(r'<[^>]+>',' ',re.sub(r'<%.*?%>',' [dynamic] ',raw,flags=re.S))
        if not label.strip():
            accessible=re.search(r'aria-label="([^"]+)"',raw)
            label=accessible.group(1) if accessible else '[icon button: inspect accessible name]'
        rows.append({'file':str(file.relative_to(ROOT)),'line':text[:match.start()].count('\n')+1,'label_template':' '.join(label.split()),'source':raw})
(OUT/'source-inventory.json').write_text(json.dumps({'scope':'Button template sites, not dynamic row instances; classic UI excluded','count':len(rows),'rows':rows},indent=2,ensure_ascii=False),encoding='utf-8')
dom_path=OUT/('dom-final.json' if (OUT/'dom-final.json').exists() else 'dom-inventory.json')
dom=json.loads(dom_path.read_text(encoding='utf-8'))
with (OUT/'dom-control-ledger.csv').open('w',encoding='utf-8-sig',newline='') as out:
    writer=csv.DictWriter(out,fieldnames=['index','tab','tag','label','id','href','DOM_handler','Rails_endpoint','Gateway_n8n_operation','permission','preconditions','accepted_rejected_unknown','persisted_state','UI_feedback','MAIN_UI','MAIN_API','CLONE','Error_Path','Evidence','Result'])
    writer.writeheader()
    for index,item in enumerate(dom['rows'],1):
        attrs=dict(item['attributes']);label=item['label'];handler='NOT_MAPPED';endpoint='LOCAL_DOM';operation='NONE';permission='Authenticated Project6 reader';preconditions='Visible enabled element'
        if 'data-tab' in attrs or 'data-qcc-open-tab' in attrs:handler='qcc navigation click / restoreActiveTab'
        elif 'data-run-id' in attrs:handler='qcc-run-inspector-btn delegated click';endpoint='GET /projects/ai-dev-demo/qldapm-ai/executions/:run_id';operation='get_execution_monitor'
        elif 'data-qcc-copy' in attrs:handler='navigator.clipboard.writeText'
        elif item['tag']=='SUMMARY':handler='Native details/summary toggle'
        elif item['tag']=='A':handler='Anchor navigation';endpoint=item['href'] or ''
        elif item['id'] in {'qcc-task-search','qcc-plan-search','qcc-task-state'}:handler='qccApplyWorkFilters'
        elif label=='Xem toàn văn':handler='qccReportReader.handleClick';endpoint='GET /projects/ai-dev-demo/qldapm-ai/reports/:id';operation='engineering_report_get'
        elif item['id'].startswith('qcc-report-') or item['id']=='btn-copy-report':handler='qccReportReader.handleClick'
        elif item['type']=='submit':handler='qccStartLiveTransport.submit';endpoint='POST /projects/ai-dev-demo/qldapm-ai/commands';operation='See source-inventory and action matrix; hidden form fields intentionally not exported';permission='Fresh Native PM/Owner plus operation guards';preconditions='CSRF, request UUID, operation source/revision checks'
        elif attrs.get('data-action')=='close-modal':handler='qccCloseModals'
        elif item['id'] in {'btn-open-schedule-modal','btn-open-intake-modal'}:handler='qccShowModal'
        writer.writerow({'index':index,'tab':item['tab'],'tag':item['tag'],'label':label,'id':item['id'],'href':item['href'],'DOM_handler':handler,'Rails_endpoint':endpoint,'Gateway_n8n_operation':operation,'permission':permission,'preconditions':preconditions,'accepted_rejected_unknown':'Operation-specific; see ACCEPTANCE.md','persisted_state':'Operation-specific; no inference from DOM presence','UI_feedback':'See scenario evidence','MAIN_UI':'NOT_TESTED_PER_INSTANCE','MAIN_API':'NOT_TESTED_PER_INSTANCE','CLONE':'See scenario-level matrix','Error_Path':'See scenario-level matrix','Evidence':'dom-inventory.json; source-inventory.json','Result':'NOT_TESTED'})
summary={'dom_counts':dom['counts'],'dom_evidence':dom_path.name,'template_button_sites':len(rows),'instance_status':'Presence inventory only; scenario PASS never auto-promoted to every repeated row','tags':dict(collections.Counter(r['tag'] for r in dom['rows']))}
(OUT/'inventory-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
