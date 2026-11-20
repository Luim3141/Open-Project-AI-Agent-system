"""Refresh only explicitly marked current-status blocks; preserve historical content."""
import datetime,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
START='<!-- FULL_INTEGRATION_20261103_CURRENT -->';END='<!-- END_FULL_INTEGRATION_20261103_CURRENT -->'
base='`FINAL_INTEGRATION_ACCEPTANCE.md`'
reports={
'FINAL_SYSTEM_STATUS.md':'''# Full integration — MAIN 03/11/2026

**DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY.** Gateway e9af9565/Core b5f3913a healthy; n8n 05376355 running, no Docker healthcheck. OFF/active0, worker heartbeat, provider gate false, 484 receipts; #391 succeeded checkpoint39/45 calls, không resume. Exact source/image/pins: `integration-final/final-live-verification.json` (13:03Z).

GitHub tự poll hai lần 11/10 rồi 11/0; Demo `01d765c` là unmerged integration, PR6–11 OPEN. 138 event receipts có n8n success; không còn pending/retry/sending, một WP385 DEAD được giữ. WF01 P6 file/readback PASS; WF12 human READY; WF16 HEALTHY sau recovery; 16 workflow clone PASS có phạm vi, không chứng minh mọi branch MAIN. Project5 12 bảng nguyên/users18 chỉ login timestamps.

RAG không đạt, candidate chưa deploy; Computer Use bị tool policy dừng trước scenario, Owner acceptance PENDING. 74 Windows qualification tests PASS; pinned Gateway Linux 73 PASS/1 SKIPPED. Bảng 16 workflow, 15 câu trả lời và evidence links: `FINAL_INTEGRATION_ACCEPTANCE.md`.''',
'FULL_DEFECT_REGISTER.md':'''# Defects — full integration 03/11/2026

1. **OPEN — Semantic RAG:** DEV baseline 2/13, FPR1/20; candidate8/13, FPR2/20 and p95 7.281s. DEV8 document13/13 nhưng supporting span9/13; không có abstention, 20/20 negative có candidate, không được gọi là FPR. Holdout queries/labels sealed, document-unseen không còn do nguồn đã xuất hiện trong dev; labels chưa reviewer độc lập/human.
2. **BLOCKED — UI UAT:** Computer Use không xác định được browser URL để enforce policy; 0 scenario/screenshot, Owner acceptance PENDING. `integration-final/uat/RESULT.json`.
3. **OPEN — WP385 historical event:** WF13 DEAD sau 5 attempts, source visible0/Native404; giữ nguyên, không force retry/bypass.
4. **LIMIT — WF14 MAIN và WF12 cron:** WF14 failure/retry được chứng minh clone, chưa có positive MAIN mới; weekly human MAIN READY nhưng current-period cron bốn readers chưa được chứng minh.
5. **RESOLVED TRANSIENT / retained history — operator throttle:** drain vượt shared 30/min gây 94 HTTP429/retries; dừng drain, worker backoff tự phục hồi, terminal snapshot 0 pending/retry/sending. Không reset quota/attempt/history. `integration-final/n8n/operator-throttle-incident.json`.
6. **LIMIT — GitHub:** socket/DNS treo ngoài library timeout chưa có hard-kill proof; UI auto-refresh chưa UAT.

Chi tiết/bằng chứng: `FINAL_INTEGRATION_ACCEPTANCE.md`. Không nhầm các lỗi hay giới hạn này với Owner approval.''',
'SECOND_BRAIN_RAG_EVALUATION.md':'''# Semantic RAG — full integration 03/11/2026

**FAILED / NOT DEPLOYED.** Baseline DEV Hit@5 2/13, FPR1/20; Qwen candidate8/13, FPR2/20, p95 7.281s. DEV8 post-hoc document13/13, exact support span9/13; 20/20 negative còn candidate vì chưa có abstention, không thể gọi là FPR. Holdout queries/labels chưa mở; DEV đã đưa holdout-source documents vào context, không claim document-unseen, labels chưa independent/human review. BGE/Qdrant hiện phục vụ baseline. Xem `integration-final/SECOND_BRAIN_RAG_EVALUATION.md` và `integration-final/rag/span-dev8-relevance.json`.''',
'N8N_16_WORKFLOW_STATUS.md':'''# n8n WF01–WF16 — full integration 03/11/2026

16 business paths có bounded clone evidence, nhưng không claim mọi branch MAIN. WF01 P6 actual ingest/replay/search/read và SQLite/FTS/Qdrant/citation PASS; WF02/04/11/13/15 có 138 persisted receipts đối chiếu 138 n8n SUCCESS (33/11/10/82/2). WF14 failure/retry chỉ chứng minh trên clone. WF07 current-day cron execution3089 SUCCESS, READY4/4 readers20–23, reuse immutable receipt đã tạo trước đó trong ngày, không fresh generation sau rollout. WF12 human current report READY, cron bốn readers kỳ này chưa chứng minh. WF16 trước recovery DEGRADED, sau recovery bucket mới HEALTHY zero inference.

Operator fast drain tạo 94 HTTP429 retry; đã dừng và retry hợp lệ tự phục hồi, hiện 0 PENDING/RETRY/SENDING; một DEAD WP385 visible0/Native404 được giữ. 16-row matrix + exact sources: `FINAL_INTEGRATION_ACCEPTANCE.md`; `integration-final/n8n/main-receipts-final.json`, `main-events-terminal-readback.json`, `operator-throttle-incident.json`.''',
'GITHUB_SYNC_VERIFICATION.md':'''# GitHub Sync — MAIN 03/11/2026

Gateway e9af9565/Core b5f3913a đã deploy. Poll actor18 tự động 300s SUCCESS checked11/changed10 rồi checked11/changed0; Native đọc lại 10/10 journal operations mỗi marker đúng một lần, không manual sync. [First](integration-final/github/main-github-readback-20261103T124816Z.json), [second](integration-final/github/main-github-readback-20261103T125148Z.json).

PR6–10 + PR11 vẫn OPEN/unmerged. Actual Demo HTTP projection xác nhận commit `01d765c01d62a0d636e276f72bdc5cdc62db8c5a`, `UNMERGED_INTEGRATION_TEST_RELEASE`; review NO_REVIEWS, CI NOT_CONFIGURED không phải PASS. WF04 có 11 ACK/verified n8n executions. UI auto-refresh chưa test vì Computer Use blocked. Chi tiết `FINAL_INTEGRATION_ACCEPTANCE.md`.''',
'DEMO_COMPLETION_MATRIX.md':'''# Demo completion — full integration 03/11/2026

**DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY; OWNER ACCEPTANCE PENDING.** Demo18791 chạy unmerged integration `01d765c`, PR6–10 và PR11 OPEN; 52 tests và actual HTTP/CSV/Unicode fixture PASS, SQLite preserved. Gateway/Core/n8n deployed, 138 verified event receipts; file P6, GitHub polling, weekly human report và post-recovery monitor có MAIN read-back. 16 workflow bounded clone evidence không thành mọi MAIN branch.

Chưa đạt: semantic RAG gate, Computer Use UAT (tool policy dừng trước scenario), current-period WF12 cron 4 readers, WF14 MAIN failure path, historical WP385 DEAD. Xem `FINAL_INTEGRATION_ACCEPTANCE.md`, `integration-final/uat/RESULT.json`.''',
'OWNER_MANUAL_UAT_GUIDE.md':'''# Owner UAT — full integration 03/11/2026

Owner acceptance vẫn PENDING. Computer Use đã được phép nhưng tool dừng trước chọn browser vì không xác định được URL để enforce policy; không có UI scenario/screenshot. `integration-final/uat/RESULT.json`.

Khi công cụ/phiên browser an toàn khả dụng, kiểm read-only Command Center/Workforce/Execution/Reports, GitHub & Delivery (unmerged Demo SHA `01d765c` và auto-refresh), n8n histories WF04, Second Brain/citation, Demo18791/filter/CSV, accessibility/zoom theo checklist `integration-final/uat/PLAN.md`. Kết quả cần ghi từng vai trò/scenario; không xem READY backend như Owner acceptance. Không retry/resume WP391, force retry WP385 DEAD, hoặc merge PR11 nếu chưa có quyết định Owner. Semantic RAG hiện chưa đạt và không được trình bày như PASS. `FINAL_INTEGRATION_ACCEPTANCE.md` ghi trạng thái đầy đủ.''',
'CONTINUATION_HANDOFF.md':'''# Continuation — full integration 03/11/2026

Trạng thái thật **DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY**, không Owner acceptance. Bắt đầu bằng `FINAL_INTEGRATION_ACCEPTANCE.md` và `integration-final/final-live-verification.json`; không dựa deployment statements lịch sử dưới đây. Gateway e9af/Core b5f/n8n053, OFF/active0, gate false, 484 receipts, #391 succeeded checkpoint39; không resume.

Còn làm: thiết kế candidate RAG có abstention + support citation và independent evaluation mới, không tune holdout đã niêm phong; giải quyết policy tool UI để chạy UAT, không bypass; kiểm WF14 failure path và cron WF12 current period an toàn; theo dõi WP385 DEAD như historical invisible source. 94 retries HTTP429 đã phục hồi; không reset quota/history. 138 MAIN receipts đối chiếu n8n success. Master-key hardening/DR deferred theo scope, Project5 read-only. Các PR chưa merge, Demo unmerged SHA01d765c.'''
}

for name,content in reports.items():
 path=ROOT/name;old=path.read_text(encoding='utf-8');block=START+'\n'+content+'\n'+END
 pattern=re.escape(START)+r'.*?'+re.escape(END)
 matches=len(re.findall(pattern,old,flags=re.S))
 if matches>1:raise ValueError('DUPLICATE_CURRENT_BLOCK:'+name)
 new=re.sub(pattern,lambda _:block,old,count=1,flags=re.S) if matches else block+'\n\n'+old
 path.write_text(new,encoding='utf-8')

arch=ROOT.parents[3]/'architecture.md'
old=arch.read_text(encoding='utf-8');astart='<!-- FULL_INTEGRATION_DEPLOYED_20261103 -->';aend='<!-- END_FULL_INTEGRATION_DEPLOYED_20261103 -->'
block=astart+'''\n## Full integration — deployed partial 03/11/2026

MAIN Gateway e9af9565/Core b5f3913a/n8n05376355; Github poll actor18/300s and six event branches activated. 138 Gateway receipts/n8n executions SUCCESS, one historical WP385 DEAD protected; WF01 P6 file actual, GitHub readback and WF16 post-recovery HEALTHY verified. RAG semantic acceptance failed and Computer Use UAT blocked: **NOT_FUNCTIONAL_DEMO_READY**, Owner acceptance pending. Native is business source, Gateway owns durable work/retry, n8n observes/calls fixed workflow contracts; no second coding scheduler. Project5 12 tables unchanged, user18 login timestamps only. Authoritative matrix/evidence: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_INTEGRATION_ACCEPTANCE.md`. Older blocks below reflect historical snapshots.\n'''+aend
pattern=re.escape(astart)+r'.*?'+re.escape(aend)
if len(re.findall(pattern,old,flags=re.S))>1:raise ValueError('DUPLICATE_ARCH_CURRENT_BLOCK')
arch.write_text(re.sub(pattern,lambda _:block,old,count=1,flags=re.S) if re.search(pattern,old,flags=re.S) else block+'\n\n'+old,encoding='utf-8')

result=ROOT/'FINAL_TEST_RESULTS.json';data=json.loads(result.read_text(encoding='utf-8'))
if 'pre_full_integration_summary' not in data:
 data['pre_full_integration_summary']={k:data.get(k) for k in ('snapshot_utc','overall_status','current_images','serving_source')}
data['snapshot_utc']='2026-11-03T13:03:04.305973+00:00';data['overall_status']='DEPLOYED_PARTIAL_NOT_FUNCTIONAL_DEMO_READY_OWNER_UAT_PENDING'
data['current_images']={'gateway':'sha256:e9af9565b3af52d2b2184bef144aa22cbdab019ecae15f2ccb0b48526f060ed7','core':'sha256:b5f3913ae8a74e4d37aaba9a5a6a12c14ddbe6d75d885359175a0a5d1f6a3db7','n8n':'sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269'}
data['serving_source']='integration-final/final-live-verification.json'
data['integration_final']={'status':'DEPLOYED_PARTIAL_NOT_FUNCTIONAL_DEMO_READY','qualification_windows':{'passed':74,'skipped':0,'evidence':'integration-final/github/qualification-tests.json'},'runtime_gateway_linux':{'passed':73,'skipped':1,'evidence':'integration-final/runtime-regression.json'},'n8n_receipts':{'success':138,'workflow_counts':{'WF02':33,'WF04':11,'WF11':10,'WF13':82,'WF15':2},'evidence':'integration-final/n8n/main-receipts-final.json','dead':1,'pending_retry_sending':0},'semantic_rag':'FAILED_NOT_DEPLOYED','ui_uat':'BLOCKED_ZERO_SCENARIOS','owner_acceptance':'PENDING','project5_integrity':'12_IDENTICAL_USER18_LOGIN_TIMESTAMPS_ONLY','evidence':'FINAL_INTEGRATION_ACCEPTANCE.md'}
result.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'updated_reports':list(reports),'architecture':str(arch),'json':str(result)}))
