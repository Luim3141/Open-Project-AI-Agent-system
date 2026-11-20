"""Update existing handoff documents from verified runtime evidence; retain history."""
import datetime,json,re
from pathlib import Path
OUT=Path(__file__).parent;DOC=OUT.parent;ROOT=OUT.resolve().parents[4]
live=json.loads((OUT/'final-live-verification.json').read_text(encoding='utf-8'))
integrity=json.loads((OUT/'native-integrity-after.json').read_text());assert integrity['status']=='PASS'
uat=json.loads((OUT/'browser-uat.json').read_text());assert uat['report_daily_full'] and uat['report_audit_facts'] and uat['github_sync_no_changes_without_reload']
qualification=json.loads((OUT/'qualification-caption.json').read_text());assert qualification['status']=='PASS'
images={**live['images'],'n8n':live['n8n_image']};p=live['performance'];now=live['utc']
common=f'''Cập nhật {now} UTC (Asia/Bangkok,04/11/2026). **FUNCTIONAL_REPAIRS_VERIFIED — PERFORMANCE_GATE_OPEN**; chưa chứng nhận `AI_CONTROL_CENTER_DEMO_READY` hoặc FULL FUNCTIONAL PASS. Các block bên dưới là lịch sử.

MAIN: Gateway `{images['gateway']}`; Core `{images['core']}`; n8n `{images['n8n']}`. Images/source/pins được read-back; Gateway/Core healthy, n8n readiness200. Final PAUSED, queue0, workerALIVE, delegationOFF;21coding runs/531provider receipts giữ nguyên. Project5 scoped rows và global config/security tables bảo toàn; chỉ cho phép timestamp đăng nhập User thay đổi.

Native386/387/389/390/391/394 đã READY FOR RELEASE/v10 qua workflow thật và journal của principal25; không tự DONE.391/b7fd và394 vẫn SUCCEEDED, không replay. PR11MERGED/main, PR12OPEN; Demo artifact giữ nguyên. RAG algorithms đóng băng/FAILED; provider readiness riêng, không coi workerALIVE là inferenceREADY.

Report Reader đã sửa trên MAIN: CSP nonce, Turbo cache restore, timeout15s, không ghi đè response cũ; Daily6766ký tự/6sections/Raw Markdown, audit có facts/provenance thay vì trang trống. GitHub Sync hiển thị ACK→operation→COMPLETED — NO CHANGES/12checked/0changed mà không F5. Artifact caption ghi rõ metadata lịch sử; trạng thái merge hiện hành lấy từ bảng PR.

Gateway HTTP5samples: trước p50=9.8377s/samplep95(max)=18.9763s; sau p50={p['p50_seconds']}s/samplep95(max)={p['p95_seconds']}s. Mục tiêu initial usable<4s chưa đạt; warm UI paint<200ms chưa có phép đo riêng. Core observed GitHub Sync ACK1913.38ms là một mẫu, không phải p95. Gateway hiện1CPU/384MiB, có sample saturation~100% khi đo. Không tăng quota hay đổi nơi lưu DB để che giới hạn. Cần tiếp tục tối ưu/read-path load qualification trước chứng nhận Demo Ready.

Bằng chứng: [runtime](cc-stabilization/final-live-verification.json), [166 image regressions](cc-stabilization/image-regression-reports.json), [exact clone qualification](cc-stabilization/clone-qualification-caption.json), [browser](cc-stabilization/browser-uat.json), [Project5](cc-stabilization/native-integrity-after.json). Không đổi GitHub source/merge, Demo, RAG algorithms hoặc DR.
'''
answers='''
1. **Vì sao AI làm xong nhưng WP còn NEW?** Publication trước chỉ ghi delivery metadata/comment; không có bộ đối soát workflow Native. Worker success cũng không phải Native acceptance.
2. **WP nào đã sync?**386,387,389,390,391,394: NEW/v2→8cạnh hợp lệ→READY FOR RELEASE41/v10; API read-back và persisted move journal xác nhận.
3. **Mapping ra sao?** Stage→semantic state cấu hình từ role22/type1; form/allowedValues/lockVersion phải qua Native. Engineering SUCCEEDED cần Dev/test/reviewer/QA/PR evidence; Native chỉ tới READY FOR RELEASE. PR12OPEN tách khỏi391/các PR đã DEPLOYED_TO_DEMO nhưng còn pending acceptance. Không tự DONE.
4. **WP nào không tự chuyển?**379 là parent/partial anchor;395 là delegated Bug fixture IN ANALYSIS, không thuộc coding sync.385 đã xóa, không tái tạo. Legacy parent-referenced runs thiếu child-source binding không được suy diễn thành cập nhật Native; unsupported/human/source change/unknown write trở thành STATUS_SYNC_BLOCKED hoặc OUTCOME_UNKNOWN.
5. **Controls được test thế nào?** Clone: AUTO→PAUSED→OFF→PAUSED, desired/effective/revision, stale conflicts, queued/running cancel/fencing trong regression; terminal391 resume dedup và cancel no-op. MAIN: PAUSED read-back, RUN ONCE không có work trả NO_ELIGIBLE_WORK, GitHub operation thật. Không replay coding để thử nút.
6. **Còn nút im lặng?** Report full-view và transport sau Turbo restore đã sửa; report/status reads có bounded timeout/UNKNOWN feedback. Chưa chứng nhận mọi button trong mọi browser; không bấm Snapshot+AI hoặc giao task mới trong rehearsal.
7. **GitHub không F5?** Có: actual Owner click, persisted ACK/correlation, existing worker completes, UI hiển thị NO CHANGES/12checked/0changed. PR11MERGED,12OPEN.
8. **F5 về Home?** Actual trước sửa tái hiện; pathname/query/hash nay được giữ. F5 ở tabBacklog/GitHub/Reports vẫn AI Center; inline-handler regression có root base tag.
9. **Tab còn đơ?** Đã quan sát chuyển tab trong khi GitHub job pending và Back/Forward đúng; stale polls không overwrite. Toàn bộ page vẫn chịu initial data-load latency như mục10.
10. **Tốc độ?** Đọc số đo trước/sau ở phần trên và JSON runtime; chưa có browser-paint p50/p95, không dùng CUA wall time thay phép đo browser. Performance gate còn OPEN.
11. **Gateway/n8n nhận đúng?** UI→Core/Gateway command UUID/operation persisted; controls không bắt buộc gọi n8n. Existing integration/outbox/idempotency regressions PASS, n8n image/definitions không thay. WF05/06/09 MAIN business evidence9executions từ phiên trước được giữ; không nhận là một đợt16workflow business E2E mới. Historical385/old-plan DEAD không replay.
12. **Errors rõ?** NO_ELIGIBLE_WORK có thông báo riêng; JSON transport403/409/500/lostACK/stale-order/unknown được regression test. Report lỗi có thông báo và timeout15s; query20s; không auto-retry unknown writes.
13. **Clone hay MAIN?**166targeted tests trong immutable Gateway image; Rails login/session/CSRF/render/nonced report/audit endpoint trên private Main clone; exact Core component reuse được ghi. MAIN: actual UI report/Raw/sections/navigation/Sync/no-work, health/source/native/data read-back. Không gọi automated clone là human acceptance.
14. **Computer Use?** Có, IAB127.0.0.1, tài khoản Owner do người dùng tự đăng nhập/MFA. Đã tái hiện lỗi và thử lại UI thật; không lấy password/OTP/cookie.
15. **Project5?**341WP,344relations,968journals và13scopes được so sánh. Không có Project5/business/config/security changes trong phạm vi snapshot; User login timestamps là ngoại lệ ghi rõ.
16. **Images/source?** Full immutable hashes ở đầu và final-live-verification.json; local/image/runtime hashes, compose pins và protected config được kiểm.
17. **Final mode?** PAUSED, delegationOFF, queue0; worker heartbeat riêng với provider readiness.21coding runs và531receipts không tăng.
18. **Còn cản demo?** Initial/backend latency vượt mục tiêu; browser paint<200ms và200%zoom chưa được chứng nhận. Vì vậy không gắn AI_CONTROL_CENTER_DEMO_READY. SemanticRAG/whole-system qualification vẫn FAILED/open ngoài phạm vi đóng băng này. Report full-view đã có actual MAIN proof.
'''
demo='''
## Checklist demo5–10phút

1. Mở `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai`: Project6, PAUSED/queue0/workerALIVE; đọc timestamp và provider state riêng.
2. Backlog: tìm391 và394; đối chiếu Engineering SUCCEEDED, Native READY FOR RELEASE/v10, Delivery riêng.
3. Mở Native WP/activity: kiểm status thật và journal principal25; không bấm DONE/transition.
4. Mở existing b7fd Run Inspector, xem QA/test/PR evidence; không Resume run đã hoàn tất.
5. GitHub: PR11MERGED/main, PR12OPEN; Demo artifact là metadata của lần deploy đã lưu.
6. Bấm Sync GitHub một lần; xem ACK/request, operation, rồi completed/no changes. Chuyển tab khi chờ; không F5 để tạo cảm giác hoàn tất.
7. Reports: Daily→Xem toàn văn→6sections→thu gọn/mở rộng→Raw Markdown. Native NEW trong report08:00 là HISTORICAL snapshot, không phải status live.
8. Audit mới nhất→Xem toàn văn: facts/provenance/decision principals; không tự gọi narrativeAI.
9. Đóng modal, F5 và Back/Forward; vẫn ở AI Center/tab. Run Once khi no eligible chỉ nhận từ chối rõ.
10. Kết thúc PAUSED/delegationOFF/queue0. Không bấm Snapshot+AI, giao task, merge/deploy Demo, RAG experiment hoặc restore DB. Dự trù thời gian tải chậm đã ghi, chưa gọi đây là Demo Ready.
'''
marker='CC_STABILIZATION_CURRENT_20261104'
def prefix(path,title,body):
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'<!-- '+marker+r' -->.*?<!-- END_'+marker+r' -->\s*','',text,flags=re.S)
    block='<!-- '+marker+' -->\n# '+title+'\n\n'+body.strip()+'\n<!-- END_'+marker+' -->\n\n'
    path.write_text(block+text,encoding='utf-8')
files=['FINAL_SYSTEM_STATUS.md','FINAL_INTEGRATION_ACCEPTANCE.md','OWNER_MANUAL_UAT_GUIDE.md','OWNER_CONTROL_AND_LIVE_OBSERVABILITY_EVIDENCE.md','GITHUB_SYNC_VERIFICATION.md','REPORTS_AND_UI_CONTRACTS.md','DEPLOYMENT_AND_ROLLBACK.md','CONTINUATION_HANDOFF.md','FULL_DEFECT_REGISTER.md']
for name in files:
    extra=answers if name=='FINAL_INTEGRATION_ACCEPTANCE.md' else demo if name=='OWNER_MANUAL_UAT_GUIDE.md' else '\nChi tiết18câu trả lời: [FINAL_INTEGRATION_ACCEPTANCE.md](FINAL_INTEGRATION_ACCEPTANCE.md); checklist: [OWNER_MANUAL_UAT_GUIDE.md](OWNER_MANUAL_UAT_GUIDE.md).\n'
    prefix(DOC/name,'Control Center/Reports MAIN — functional repairs verified, performance open',common+extra)
prefix(ROOT/'architecture.md','Implemented Control Center repair and Report Reader',common+'\nNative sync consumes trusted persisted run evidence, journals each configured valid edge, reconciles unknown outcomes by own activity, and accepts only contiguous owned status-only changes in worker source checks. Existing background reconciliation remains the observer; idle ticks avoid SQLite writer locks. Fresh Native authorization is reused only within one sync-admission request and rechecked by the execution worker. Raw/sanitized reports preserve source data; structured audit fallback is a view, not a new report or model output.\n')
for name in ['README.md','CHECKPOINT.md']:
    prefix(ROOT/'openproject/ai'/name,'MAIN current — Control Center/Reports',common)
result_path=DOC/'FINAL_TEST_RESULTS.json';result=json.loads(result_path.read_text())
result.update(schema_version=max(9,result.get('schema_version',0)),snapshot_utc=now,overall_status=live['readiness'],current_images=images,serving_source='cc-stabilization/final-live-verification.json')
result['control_center_stabilization']={'test_count':166,'images':images,'runtime_evidence':'cc-stabilization/final-live-verification.json','clone_evidence':'cc-stabilization/clone-qualification-caption.json','browser_evidence':'cc-stabilization/browser-uat.json','data_integrity':'cc-stabilization/native-integrity-after.json','performance_gate':'OPEN','rag_algorithms':'UNCHANGED_FAILED_FROZEN','no_new_coding_runs':True,'provider_receipts':531,'final_mode':'PAUSED','delegation':'OFF'}
result_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
checkpoint_path=DOC/'CHECKPOINT.json';checkpoint=json.loads(checkpoint_path.read_text());checkpoint['current']={'at':now,'status':live['readiness'],'images':images,'evidence':'cc-stabilization/final-live-verification.json','next':'Performance gate remains open; do not replay coding or resume RAG/DR outside newest scope.'};checkpoint_path.write_text(json.dumps(checkpoint,indent=2)+'\n')
print(json.dumps({'updated_reports':len(files),'status':live['readiness'],'owner_answers':18,'main_images':images}))
