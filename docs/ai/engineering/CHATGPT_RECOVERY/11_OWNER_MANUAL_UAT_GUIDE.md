# Phase2 current — 01/11/2026

Phase2 status: PENDING OWNER MANUAL UAT. After approvedrollout owner must check reportdetail(nonempty/empty/error/stale), truthfulPR/test/rolebadges, actualNativeparentlock intake, RAG exactandsemanticlimitations, n8neditor/manualredaction andWF04eventexecution link. CLIcanary/NodeDOM/Rubycontracts are automated code evidence, not UI PASS. Do not triggernewbusinessrun before separateboundedscopeapproval.

---

# Owner Manual UAT — PENDING OWNER UAT

Chỉ dùng sau khi candidate được duyệt/triển khai và read-back; `r24` đang phục vụ chưa có các fixes này. Không coi hướng dẫn này là kết quả test GUI. Dùng tài khoản Owner hiện hữu, không gửi password/token vào chat.

1. Mở `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`, kiểm đúng Project6. Project5 chỉ được đọc; #379 tiếp tục IN PROGRESS.
2. Ghi thời gian VN đầy đủ và snapshot ban đầu mode/worker/backlog. Nếu service lỗi, tab GitHub phải hiển thị OFFLINE/UNKNOWN và không dựng PR lịch sử. Thiếu evidence phải rõ NOT VERIFIED.
3. Chỉ giao **một** yêu cầu kỹ thuật nhỏ, có acceptance rõ, mã unique do Owner chọn. Ghi Run ID thật từ phản hồi. Không dùng lại marker lịch sử hoặc xóa công việc để né409.
4. Quan sát PM/BA: BA STARTED→COMPLETED rồi PM STARTED→COMPLETED khi flow thực xảy ra; model/session/receipt đúng run hoặc thiếu evidence được ghi rõ. Một role chạy không làm mọi role RUNNING.
5. Kiểm plan/spec/AC và các WP thực được tạo trong Project6; lấy ID từ UI/API, không đoán WP tiếp theo. Nếu conflict/error, lưu mã lỗi và run hiện hành, không liên tục submit lại.
6. RUN ONCE cho unit ready: phải có run/claim thật, worker heartbeat và logs. AUTO chỉ chọn unit đủ dependency, hết backlog phải nêu lý do; không yêu cầu mọi AUTO/IDLE sinh model calls.
7. PAUSE/OFF phải chặn claim mới và fence/checkpoint run đang thực thi; CANCEL và RESUME là thao tác khác nhau. Không thử resume outcome UNKNOWN trước reconcile. Ghi trước/sau từ Run Inspector.
8. Bấm Run ID thật để mở Inspector. Route đã có: `/projects/ai-dev-demo/qldapm-ai/execution?run_id=<ID thật>&format=json`; DAG/timeline/tests/diff phải có evidence hoặc thiếu dữ liệu rõ ràng, không hardcode PASS.
9. Đối chiếu Dev OpenClaw session, Reviewer exact revision, QA command/exit/artifact. Receipt model success không tự chứng minh code/test PASS. Nếu review fail phải có rework thật và review/test lại revision cuối.
10. Mở PR URL thật từ run; kiểm head/base/commit. Không merge tự động. PR merged vào feature khác merged vào main; merged không đồng nghĩa deployed/Owner accepted.
11. Bấm Đồng bộ GitHub: ghi số PR thật, UPDATED/UNCHANGED/FAILED và thời gian; gây lỗi mạng chỉ trong clone/test environment. Nếu thất bại phải hiện lỗi, không success toast/5PR mặc định. Không retry unknown POST nếu chưa reconcile.
12. Tab Reports: tạo On-Demand Snapshot, ghi Report ID, mở “Xem toàn văn”. DB/list/get phải cùng narrative/metrics; thiếu metrics không hiện5/12/5. Route read thật: `/projects/ai-dev-demo/qldapm-ai/reports/<ID thật>`. Nếu trống, gửi Report ID/HTTP status và console error đã loại secrets; đây vẫn là lỗi chưa tái hiện trong batch.
13. Second Brain: thử từ khóa thật có trong WP mới, semantic VN/EN nhiều từ và negative `email` khi corpus không có email. Kiểm citation/native lockVersion/project scope. Không coi match nào đó là đúng chủ đề chỉ vì score cao.
14. n8n `http://127.0.0.1:5679`: đối chiếu đúng workflow, execution ID, response HTTP/business result và side effect. WF04 hiện là trace read; Gateway→n8n lifecycle publisher chưa được bổ sung trong batch. Workflow `success` nhưng body HTTP409 không được nghiệm thu thành công.
15. Nghiệm thu task chỉ sau Owner kiểm chức năng demo đang serve đúng commit. #379 không đóng tự động. Ghi PASS/FAIL/BLOCKED từng bước cùng actual IDs/timestamp/evidence.

Chưa kiểm: GUI clicks, fresh provider quota/retries, full coding E2E, live RAG relevance, actual post-rollout Sync. Không dùng Computer Use trong batch; các bước trên do Owner thực hiện hoặc một phiên được chỉ đạo riêng.
