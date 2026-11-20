"""Publish one evidence-backed current block; preserve historical reports below it."""
import datetime,hashlib,json,re
from pathlib import Path

OUT=Path(__file__).parent;REPORT=OUT.parents[1]
live=json.loads((OUT/'final-live-verification.json').read_text())
native=json.loads((OUT.parent/'native-after-functional.json').read_text())
cards=json.loads((OUT/'main-status-projection.json').read_text())
run=live['engineering']['runs']['301dbdd8-6f6f-4df4-b6c6-b5ca3f073795']
pilot_path=OUT.parent/'rag/short-context-pilot-result.json'
pilot=json.loads(pilot_path.read_text()) if pilot_path.exists() else {'status':'NOT_RUN'}
pilot4_path=OUT.parent/'rag/short-context-pilot-4b-result.json'
pilot4=json.loads(pilot4_path.read_text()) if pilot4_path.exists() else {'status':'NOT_RUN'}
grouped_path=OUT.parent/'rag/grouped-quote-pilot-result.json'
grouped=json.loads(grouped_path.read_text(encoding='utf-8')) if grouped_path.exists() else {'status':'NOT_RUN'}
stamp=live['utc'];images={k:v['image'] for k,v in live['containers'].items()}
def block(path,text):
    original=path.read_text(encoding='utf-8')
    original=re.sub(r'\A<!-- FUNCTIONAL_CURRENT_20261104 -->.*?<!-- END_FUNCTIONAL_CURRENT_20261104 -->\s*','',original,flags=re.S)
    path.write_text('<!-- FUNCTIONAL_CURRENT_20261104 -->\n'+text.strip()+'\n<!-- END_FUNCTIONAL_CURRENT_20261104 -->\n\n'+original,encoding='utf-8')

base='integration-final/functional-completion/'
shared=f'''Cập nhật {stamp}. **DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY; OWNER_ACCEPTANCE_PENDING.** Phần phía dưới block này là lịch sử.
Gateway `{images['gateway']}`, Core `{images['core']}`, n8n `{images['n8n']}`. Source/pins, OFF/active0, worker và provider gatefalse: [{base}final-live-verification.json]({base}final-live-verification.json).
'''
progress=f"WP394/run301dbdd8: **{run['result_status']}**, {run['provider_calls']} generation receipts, recovery_count={run['recovery_count']}; PR {run.get('pr_url') or 'chưa có'}. Một coding task, cùng run qua các continuation; không replay391/385, không merge/deploy PR mới. Dev hoàn tất, Review/QA PASS, host acceptance 57 tests PASS; Native394 vẫn NEW, tách biệt với engineering delivery và Owner acceptance."
rag='RAG chưa đạt. Serving baseline trên observed DEV: Hit@5=2/13 (15.38%), FPR1/20 (5%); chưa có benchmark mới được chứng nhận. Reader candidate DEV Hit@5=6/13 (46.15%), support3/13, FPR4/20 (20%) bị REJECTED và không deploy. Owner đã xác nhận3intents WP392;6cards VN/EN tương quan không phải benchmark đại diện hay phê duyệt candidate.'
pilot_text=f"Hai pilot context ngắn cùng6câu đều `{pilot['status']}`/`{pilot4['status']}` và không đạt:1.7B chọn supporting span1/4 positive, trả unsupported match1/2 negative;4B support2/4, negative output0/2. Warm model-only0.570–0.782s và2.601–4.862s; cold load, cached retrieval và whole-answer quality được báo riêng. Không chạy full DEV/holdout theo gate đã đóng băng. Chi tiết: `integration-final/rag/SHORT_CONTEXT_CAPACITY_RESULT.md`; không dùng các tỷ lệ pilot như benchmark acceptance."
pilot_text+=f" Grouped-source + answer/quote pilot `{grouped['status']}`:2responses hợp lệ, response thứ3 bị exact-quote validation từ chối (`{grouped.get('reason')}`); valid selections support1/2 và answer còn mơ hồ. Dừng đúng gate, không mở full DEV/holdout hoặc deploy. Raw response bị từ chối chưa được lưu nên chưa kết luận cụ thể loại quote error."
wf='WF01/03/08/09/10 đã publish MAIN. WF08/09/10/01 command receipts3423/3424/3426/3427 đối chiếu business read-back; WF03 actual planning96b4cee5 và WF10 PUBLISHED plan/Native units. WF14 own-source392 failed-attempt1 → execution3393 WAITING_RETRY → retryverified2 → WF13execution3394/currentcitation. WF05/06 PENDING_OWNER_DECISION; WF09 đã triage read-only, chưa approval/Native status transition. WF12 cron clonePASS, current-period MAIN four-reader cron chưa tới lịch Fri17:00 Bangkok; manual READY không phải cron.'
remaining='Còn mở: semantic answerability/quality + independent evaluation; Owner UI UAT; WF05/06 Owner decision; WF09 approved Project6 mapping/transition; actual WF12 current-period cron. Historical WF13/WP385 DEAD và WF10 old plan chứa385 được giữ, không force retry.'
master=f'''# Functional completion — trạng thái hiện hành04/11/2026

{shared}
{progress}

## 16 câu trả lời Owner

1. **16/16 tích hợp hoàn chỉnh?** Chưa chứng nhận mọi branch. Có16published workflows, producer/command/cron contracts; còn các gate ở mục16.
2. **Từ Command Center:** Work Intake/Planning→WF03/10; risk→WF08; Bug triage→WF09; file ingest→WF01; run lifecycle→WF04; status cards16WF. Actual Rails bridge/API + Core clone đã kiểm, chưa browserclick UAT.
3. **WF03/05/06/08/09/10:** {wf}
4. **WF12 cron:** actual schedule branch PASS trên clone; MAIN manual report có thật, bốn-reader cron kỳ hiện tại chưa có execution. Không đổi production schedule để lấy PASS.
5. **WF14 recovery:** có positive MAIN own-source392, durablefailure/retry/FTS/chunk/vector/currentcitation; không gây outage Qdrant toàn cục.
6. **Thiếu positive MAIN proof:** WF05/06 decision/write, WF09 Native status transition và current-period WF12 four-reader cron; UAT qua browser chưa thực hiện.
7. **Hit@5/FPR:** {rag}
8. **Answer/citation:** identity/freshness/index proof có; chất lượng semantic answer chưa đạt. Serving trả answer:null/NO_EVIDENCE hoặc UNVERIFIED_RETRIEVAL theo bằng chứng, không giả answer. {pilot_text}
9. **Fresh E2E:** {progress}
10. **PR/ACK:** PR12 OPEN/head1ece6705; WF04 RUN_COMPLETED3535, WF11 QA_VERIFIED3539, GitHub observation3540 ACKED và n8n SUCCESS. Native citation394,13notifications và report ON_DEMAND d349463e có read-back; automatic GitHub poll checked12/SUCCESS, Native marker đúng1lần. Source: `functional-completion/fresh-e2e-final-readback.json`, `fresh-e2e-github-n8n-readback.json`, `fresh-e2e-github-report-readback.json`.
11. **Duplicate:** một durable intake marker FINAL-E2E-27FB-1da0d2f7, một WP394/unit/run/PR12, một Native sync marker. PR12 có hai observation khác identity:3534 trước mapping (work_package_id=null),3540 sau mapping394; cùng head, không tạo hai PR hoặc hai Native comments. Continuation dùng request keys riêng và checkpoint SHA, không tạo task thay thế.
12. **Command Center:** NameError `who` đã sửa và deploya6fe1d61; actual Owner Rails bridge đọc đủ16cards/source/risk notification. Global workflow success và business ACK tách biệt, stale/permission/error không biến thànhPASS.
13. **Computer Use:** không dùng trong lượt tiếp tục này; ưu tiên actual Rails bridge/CLI/API theo prompt. Trước đó tool policy chặn browser target; chưa có browser scenario/screenshot/human sign-off.
14. **Serving:** exactimages ở đầu block;18file source/pins đối chiếu, host worker hash riêng sau sửa prepare. Core reused unchanged91af.
15. **Project5:** [{native['comparison']['status']} — snapshot read-only](integration-final/native-after-functional.json); giữ341WP/344relations/968journals và security/config tables; thay đổi user timestamps nếu có được ghi đúng comparison, không khẳng định bảng ngoài phạm vi.
16. **Chưa đạt:** {remaining}

Validation mới:72targeted Windows tests PASS;13tests trên immutable Gateway image PASS;10host prepare/recovery tests PASS (RED→GREEN);6readable-span tests PASS. Source trước statusrepair có123regression tests và exact Core/n8n clone evidence, kế thừa rõ trong qualification; không cộng gộp thành số test độc lập.

Hai lỗi prepare đã xử lý: thiếu exact Demo SHA trong WSL → trusted object-only import; start CLI exit1 khi service convergence → vẫn yêu cầu bounded RPC health trước chạy. Full prepare without inference PASS. Fresh Dev từng hết12calls nội bộ;24calls trước continuation4 đều HTTP200, không đổi quota/budget/auto_continue.
'''
block(REPORT/'FINAL_INTEGRATION_ACCEPTANCE.md',master)
parts={
 'FINAL_SYSTEM_STATUS.md':shared+'\n'+progress+'\n'+rag+'\n'+remaining+'\nAuthority: `FINAL_INTEGRATION_ACCEPTANCE.md` current block.',
 'N8N_16_WORKFLOW_STATUS.md':shared+'\n'+wf+'\nRead-back: `integration-final/n8n/final-completion-main-business-readback.json`, `final-completion-main-wf14-readback.json`, `functional-completion/main-status-projection.json`. Clone/human/cron/MAIN vẫn phân biệt.',
 'SECOND_BRAIN_RAG_EVALUATION.md':'# RAG04/11 — chưa đạt\n\n'+rag+'\n'+pilot_text+'\n`integration-final/rag/OWNER_REVIEW_PACKET_V2_REVIEWED.json` lưu đúng Owner reply; không mở/tune heldout queries/labels. JSON decoding chỉ đổi8/226spans, không phải lời giải answerability. Giữ source-span hashes/offsets, ACL/freshness và các failure receipts.',
 'DEMO_COMPLETION_MATRIX.md':shared+'\n'+progress+'\nDemo18791 vẫn SHA01d765c / unmerged integration PR11; không deploy featurecount hoặc merge PR.\n'+wf+'\n'+rag+'\n'+remaining,
 'FULL_DEFECT_REGISTER.md':'# Defects04/11\n\nRESOLVED: Command Center registered-source NameError (immutable13PASS/MAIN bridge); WSL missing verifiedbase import; startup CLI false-negative convergence (host10PASS/fullprepare).\n'+progress+'\n'+rag+'\n'+remaining+'\nBudget exhaustion giữ nguyên policy, không gọi là upstream429. Redacted diagnostic text được quan sát trong exported trajectory; chưa chứng minh runtime model-input corruption, không tắt guard.',
 'OWNER_MANUAL_UAT_GUIDE.md':shared+'\nKhông tạo lại task394 hoặc Resume391/385. Dùng current existing task/run để kiểm status/workflow links/risk/Bugtriage/source search+read và GitHub refresh. Không nhấn approve/hash nếu chưa xem exactproposal. WF05/06 vẫn cần quyết định thật của Owner; Bugtransition cần mapping Project6 được duyệt. Không coi API/clone checks là browser/human acceptance.\n'+remaining,
 'CONTINUATION_HANDOFF.md':shared+'\n'+progress+'\n'+remaining+'\nĐọc `FINAL_INTEGRATION_ACCEPTANCE.md` current block trước. Các subagent cũ đã dừng; root làm tuần tự, không spawn mới. Intent duy nhất ở private operator functional-e2e-27fb7d12; không prepare/intake/run lần nữa. Nếu cònblocked, reconcile checkpoint/tree/provider budget; max5continuations/task72calls không đổi. Không tự replay unknown outcomes.\n'+pilot_text,
}
for name,text in parts.items():block(REPORT/name,text)
repository=OUT.parents[5]
architecture=f'''# Functional completion — deployed04/11/2026

{shared}
Native Project6 là nguồn work/ACL; Gateway sở hữu durable queue, checkpoint, quotas và indexing; n8n quan sát contract cố định, không phải coding scheduler thứ hai. Completed risk/Bugtriage/WBSdraft/file commands có minimal durable source record; crash-gap repair dùng publisher hiện hữu. WF03 planning admission và WF10 published-plan verification không gọi generation mới. Host worker chỉ xuất metadata16workflows có TTL/size/ID guards, không đưa Docker hoặc credential access vào Gateway. Core hiển thị global workflow execution tách khỏi exact business ACK/source freshness.

Status registered-source identity repair đã deploy a6fe1d61; Core91af dùng lại. Host prepare nhập missing exact SHA qua trusted host bare repo/object-only bundle và đối chiếu trước/sau; existing bounded RPC health là điều kiện chạy sau CLI start convergence. Không copy agent Git config/hooks về host, không đổi branches/history hoặc provider budgets.

{progress}
WF04 lifecycle3535, GitHub3540, WF11 QA3539, Native394v2/currentcitation và report d349463e đã read-back. PR12 unmerged; Demo18791 vẫn release01d765c. {rag}
{pilot_text}

{remaining}
'''
block(repository/'architecture.md',architecture)
checkpoint=f'''# MAIN current04/11/2026

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_INTEGRATION_ACCEPTANCE.md` current block; `integration-final/functional-completion/final-live-verification.json`.
Gatewaya6fe1d61/Core91afae9c/n8n05376355, OFF/active0/provider gatefalse/workerALIVE. WP394/run301dbdd8 SUCCEEDED/PR12 OPEN/57tests;43calls, recovery5. WP391/b7fd SUCCEEDED unchanged/PR10/checkpoint39; never replay. One coding task admitted; private intent consumed, never prepare/intake/run again. No new Codex subagents; root continues sequentially. RAG FAILED/candidates rejected; Owner UAT and WF05/06 decision pending, WF09 transition pending approved mapping, WF12 actual cron awaits schedule. Exact source/images/counters must be read from new evidence, older blocks below are history.
'''
for name in ('README.md','CHECKPOINT.md'):block(repository/'openproject/ai'/name,checkpoint)
target=REPORT/'FINAL_TEST_RESULTS.json';backup=OUT/'prior-final-test-results-schema6.json'
if not backup.exists():backup.write_bytes(target.read_bytes())
result={'schema_version':7,'snapshot_utc':stamp,'overall_status':'DEPLOYED_PARTIAL_NOT_FUNCTIONAL_DEMO_READY_OWNER_UAT_PENDING','current_images':images,
 'serving_source':base+'final-live-verification.json','fresh_e2e':run,'project5':native['comparison'],
 'new_checks':{'windows_targeted':{'status':'PASS','count':72},'immutable_gateway_status':{'status':'PASS','count':13},'host_prepare_recovery':{'status':'PASS','count':10},'readable_span':{'status':'PASS','count':6},'fresh_e2e_acceptance':{'status':'PASS','count':57,'evidence':base+'fresh-e2e-final-readback.json'}},
 'qualification':base+'status-patch/qualification.json','prior_snapshot':base+backup.name,'rag':{'status':'FAILED_CANDIDATE_NOT_DEPLOYED','serving_observed_dev_hit5':'2/13','serving_observed_dev_fpr':'1/20','reader_candidate_hit5':'6/13','reader_candidate_fpr':'4/20','pilot':pilot,'pilot4b':pilot4,'grouped_quote_pilot':grouped},
 'owner_ui_uat':'PENDING','remaining':remaining,'no_new_codex_subagents':True}
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'NINE_REQUIRED_REPORTS_UPDATED','fresh_e2e':run['result_status'],'utc':stamp}))
