"""Publish the reviewed action inventory; coverage is per binding, never per repeated row."""
import collections,csv,json,re
from pathlib import Path
OUT=Path(__file__).parent
source=json.loads((OUT/'source-inventory.json').read_text(encoding='utf-8'))
assert source['count']==70
assert source['rows'][46]['label_template']=='Lưu cấu hình'
clone={12,20,26,27,37,49,50}
safety={32,33,34,51}
untested={1,2}
assert not (clone&safety or clone&untested or safety&untested)
rows=[]
operations={12:'engineering_run_once',13:'engineering_run_once',14:'engineering_control',15:'engineering_control',16:'engineering_control',17:'engineering_control',18:'engineering_github_sync',20:'engineering_report_generate',23:'sprint_risks',24:'bug_triage',26:'engineering_cancel',27:'engineering_resume',29:'engineering_github_sync',32:'knowledge_file_ingest',33:'knowledge_search',34:'knowledge_file_search',37:'engineering_plan',47:'engineering_report_schedule_update',49:'delegated_control',50:'delegated_preview',51:'knowledge_file_read',56:'engineering_notifications_dismiss'}
inspect={25,28,53,54,55,58,66,69}
report={31,60,61,62,63,64,65}
schedule={19,30,45,46,47}
local_modal={21,35,36,38,39,40,41,42,43,44,57}
copy={52,59,67,70}
nav={*range(3,12),22,68}
for number,item in enumerate(source['rows'],1):
    label=item['label_template'];file=item['file'];raw=item['source']
    result='CLONE_PASS_ONLY' if number in clone else 'SAFETY_NOT_EXERCISED' if number in safety else 'NOT_TESTED' if number in untested else 'MAIN_UI_PASS'
    tab='Global / modal'
    if 3<=number<=11:tab=label
    elif number in {25,26,27,28}:tab='Execution Center'
    elif number==29:tab='GitHub & Delivery'
    elif number in {30,31}:tab='Reports & Analytics'
    elif number in {32,33,34,51}:tab='Knowledge / RAG'
    elif number in {49,50,68}:tab='System Integrations'
    elif '_plans.' in file or number in {23,24,66,67}:tab='Backlog & Tasks'
    elif number in {69,70}:tab='Agent Workforce'
    elif number in {52,53,54}:tab='Mission / Pipeline'
    elif number in {55,56}:tab='Notifications'
    handler='qccOn click: close-toast';endpoint='LOCAL_DOM';op='NONE'
    pre='Visible enabled control; authenticated Project6 PM/Owner'
    state='Local DOM only';feedback='Visible local state/focus changes'
    response='Local action; no server ACK expected'
    expected='Apply the labeled local action'
    actual='Representative instance directly exercised; repeated rows are not individually promoted'
    evidence='browser-uat.json'
    error='Not injected on MAIN; see qualification.json for available contracts'
    if number in operations:
        handler='qccStartLiveTransport.submit (capture, correlated UUID)'
        endpoint='POST /projects/ai-dev-demo/qldapm-ai/commands';op=operations[number]
        state='Durable Gateway operation/receipt, operation-specific SQLite rows; Native write only behind guarded workflow'
        feedback='Correlated accepted/rejected/unknown message; pending button disabled; polling read-back'
        response='accepted boolean + reason_code/request_id; 4xx rejected; uncertain transport/5xx stays UNKNOWN without automatic replay'
        expected='Validate permission/source/revision and persist one accepted effect or explicit rejection'
        pre+='; CSRF, fresh Native authority, operation source/version/budget guards'
    if number in inspect:
        handler='qcc-run-inspector-btn delegated click';endpoint='GET /projects/ai-dev-demo/qldapm-ai/executions/:run_id';op='get_execution_monitor'
        state='Local modal; read only';response='200 monitor; 403/404/503 explicit error';feedback='Loading, current run summary, tabs or error'
        expected='Show the selected run, never Resume it'
    if number in report:
        handler='qccReportReader.handleClick';op='engineering_report_get (open only)'
        endpoint='GET /projects/ai-dev-demo/qldapm-ai/reports/:id' if number==31 else 'LOCAL_DOM / clipboard / download'
        pre+='; valid report ID; Copy/Export/Raw disabled until loaded'
        response='200 reader; 401/403/404/503 error; timeout15s; local actions require loaded document'
        expected='Read the complete persisted document; preserve original Markdown'
        state='Local reader; export file/clipboard only';feedback='Loading/error, raw view, expanded sections, copy status/download'
        actual='Daily 6766 characters, six report sections; Raw/collapse/expand/close; real clipboard paste6766 and file7242 bytes'
        error='Node reader contracts: loading/error/timeout/stale response/close; not injected on MAIN'
    if number in schedule:
        handler='qccShowModal/qccCloseModals' if number!=47 else 'qccStartLiveTransport.submit: captured expected_updated'
        expected='Read saved Daily/Weekly; validate; Save without resetting other fields; close restores snapshot'
        actual='Daily08:00→08:01→08:00 on MAIN v9; Weekly09:00→09:01→09:00 on final Gateway; version checked; no due cron triggered'
        evidence='browser-uat.json; main-control-readback.json; schedule-200-main.png'
        error='Native invalid hour99 blocked; stale/concurrent/duplicate/bad timezone exercised in image/Native clone'
    if number in local_modal:
        handler='qccShowModal/qccCloseModals; delegated subtab click'
        expected='Open/close expected modal or select matching Inspector panel; restore focus'
        actual='Actual intake/inspector open and X/footer close; five Inspector panels select and show content; no intake submission'
        error='Focus/Tab/ShiftTab/Escape contract and actual Escape; inspector failure not forced on MAIN'
    if number in copy:
        handler='qccOn click [data-qcc-copy] -> navigator.clipboard.writeText'
        expected='Copy full ID; empty IDs disabled with visible reason';pre+='; nonempty source ID'
        actual='Full Run ID b7fd UUID and Plan/Workforce96b4 UUID verified by actual paste into unsent then cleared intake; empty Supervisor copy disabled'
        feedback='Đã sao chép / explicit clipboard failure';state='Clipboard only'
    if number in nav:
        handler='qcc navigation / data-qcc-open-tab / restoreActiveTab'
        expected='Select correct panel and URL/history state without a backend wait'
        actual='Nine tabs,36 repeated switches; F5 on every tab; Back backlog and Forward reports; workflow action opens knowledge without executing search'
        evidence='browser-uat.json; tab-switch-main.json; f5-main.json'
    if number in {12,13,14,15,16,17,26,27}:
        error='221 image contracts: revision conflict, no work, eligible fixture, PAUSED, provider failure, checkpoints, duplicate Resume, cancel and unknown outcome'
        evidence='browser-uat.json; main-control-readback.json; clone-qualification-caption.json; image-regression-reports.json'
        actual='MAIN final: no-work rejected; OFF→AUTO_IDLE→PAUSED plus TẮT PAUSE→OFF→PAUSED; no new coding run' if number in {13,14,15,16,17} else 'Controlled fixture/Service contracts only; no eligible/blocked/active MAIN task manufactured'
    if number in {18,29}:
        actual='MAIN QUEUED→SYNCING→COMPLETED/NO CHANGES;12 checked/0 changed; operation IDs retained; no F5'
        error='Admission concurrency/dedup, transport failure/restart/unknown covered by immutable-image fixture contracts'
        evidence='browser-uat.json; main-control-readback.json; image-regression-reports.json'
    if number in clone:
        actual='Gateway immutable-image controlled fixture/contract PASS; actual Native/Core boundaries additionally covered by exact clone qualification. This row is not MAIN UI acceptance of its side effect.'
        evidence='image-regression-reports.json; clone-qualification-caption.json; qualification.json'
    if number in safety:
        actual='Not executed: RAG frozen/out of scope; no indexing or semantic/provider call for button cosmetics'
        error='Source/DOM mapping only; no claim of RAG qualification'
    if number in untested:
        actual='Server-rendered success/error toast branches not displayed in this JSON-command UAT; client toast close tested separately at site48'
        evidence='source-inventory.json; browser-uat.json'
    if number==48:actual='Real completed Sync toast closed by its X; after animation zero toasts remain'
    api='PASS' if result=='MAIN_UI_PASS' and (number in inspect or number in {13,14,15,16,17,18,23,24,29,31,47,56}) else 'SAFETY_NOT_EXERCISED' if number in clone|safety else 'NOT_APPLICABLE'
    rows.append({'site':number,'Tab':tab,'Button':label,'DOM_handler':handler,'Rails_endpoint':endpoint,'Gateway_n8n_operation':op,'Required_permission':'Fresh Native Project6 PM/AI_SYSTEM_OWNER; report/source ACL applies','Input_state_preconditions':pre,'Accepted_rejected_unknown':response,'Persisted_state':state,'UI_feedback':feedback,'Expected':expected,'Actual':actual,'MAIN_UI':result=='MAIN_UI_PASS','MAIN_API':api,'CLONE':result=='CLONE_PASS_ONLY','Error_Path':error,'Evidence':evidence,'Result':result,'Source':file+':'+str(item['line'])})
assert len(rows)==70
with (OUT/'button-acceptance.csv').open('w',encoding='utf-8-sig',newline='') as out:
    writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
counts=dict(collections.Counter(row['Result'] for row in rows))
(OUT/'button-acceptance.json').write_text(json.dumps({'scope':'70 frontend button declaration sites, conditional branches included. MAIN_UI_PASS means one representative binding/branch actually used, never all570 repeated instances. Version lineage is explicit in browser-uat.json. CLONE includes immutable-image fixture contracts, not a cloned-browser UI claim.','counts':counts,'rows':rows},indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(counts))
