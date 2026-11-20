> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# MULTI AGENT E2E REPORT

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

Luồng thực: Core session/TOTP → HMAC bridge → Gateway native identity/project/role → durable queue → isolated Python worker → Supervisor/DAG → specialist + reviewer → structured AgentResult/report → polling UI + trace/audit. Dùng dispatcher/store/worker có sẵn; không thêm distributed queue.

`engine=supervisor` là phân tích/dự thảo deterministic local, model_used=false; không phải smoke Gemini. Chọn tối đa10ID cụ thể; từng ID qua Native.package/ACL, cùng project và lockVersion. Không có ID thì đọc tập Native được phép rồi giới hạn10mục phân tích. Lượt đọc lại kiểm tra Native ACL/version; không hiển thị narrative cũ khi nguồn/quyền thay đổi. Bản cũ không có source_ids vẫn được kiểm tra theo fingerprint cũ.

Một worker thực thi có deadline600s, task TTL600s, dependencies tuần tự và progress bền vững. Không tự retry mutation. Cancellation chỉ áp dụng local run của chính actor; queued intent bị hủy, executing read-only lease giữ tới khi worker kết thúc; receipt cancelled=true và trạng thái terminal FAILED. Không khẳng định đã undo việc ghi.

Native business mode chặn list_code/read_code/write_code/request_test/propose_operation ở REST, perform và MCP catalog. Strict sandbox cũ giữ riêng. Local handler không có operator/shell/docker tools. Client actor/project/conversation không cấp quyền.

Report/draft được dùng thật trong UI. Draft ghi chỉ ở REVIEW, không tự tạo hoặc thực thi native mutation. Proposal nghiệp vụ thật đi luồng canonical preview → HMAC confirm → native readback; non-PM vẫn không được tạo/sửa/transition. Input references là provenance, không có nghĩa nội dung đã được con người nghiệm thu.

Bằng chứng: browser-uat-*.json (phải chọn bản có hai image hiện tại và passed=true), final-image-uat.json, api-uat-1792315548.json, control-center-uat.json, frozen regression, qualified result screenshots. Các failure đầu phiên được giữ; không dùng mock PASS làm live Gemini PASS.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
