# Main live readiness — 2026-10-25T03:43:23.174862+00:00

**PARTIAL — chưa cấp full release GO.** Main hiện chạy với Gateway `sha256:8c91c1c0ae3edf754615b302575d093fa45b5257ffa0b86f84d7872830a3c3ec` và Core Web `sha256:175c337834cabb5e56689432cbb913e5dc4ef622d77b7e3e49d16333cdab85e2`. Đã triển khai human QA review và nút điều hướng trong AI Control Center; user xác nhận trang QA có ID/read controls. Owner dùng danh tính18; PM/BA/BE/FE/QA giữ quyền cũ. Source/runtime,434Windows/422Linux(+12platform Windows)/8Ruby,73role checks/48API contracts/13read-only/10signed-policy checks PASS. Đây không phải tuyên bố mọi business workflow đã hoàn tất.

**Dữ liệu:**338WP Main và375physical rows giữ nguyên,370v2, ScenarioF consumed+61audit events/original report và history đều nguyên vẹn. RAG373docs/1728chunks/1731points, zero scoped drift,3legacy points retained/excluded. Không có Native write, proposal, QA review hoặc model call mới trong gói này. Credentials/password/TOTP/membership không đổi; không thao tác Staging hoặc gửi external notification.

**Còn chặn full release:**

- WF09/WF11: genuine QA producer/artifact và fix/retest/review/closure chưa có Main E2E. QA23 có comment link nhưng không quảng bá attachment upload; V1 cần attachment chính QA tạo. Inline-log alternative chỉ là design preview. Task371 còn thiếu story/AC/scope evidence/approval theo Core; không nhảy NEW→REVIEW hoặc tự điền PASS.
- WF10: versioned Native dependency/derived schedule contract và broader model-produced full tree chưa nghiệm thu.
- WF02: chưa có trusted permanent-delete producer; không xóa theo404/visibility.
- WF14/WF15: unknown outcomes tiếp tục hold; full Qdrant restore vẫn bị automatic tool review chặn, không dùng đường vòng;3legacy point producer chưa proven.
- WF07/WF16: external delivery BLOCKED_CONFIGURATION; không tự chọn recipient. Administration chưa có implementation tiếp tục báo NOT_IMPLEMENTED.

**Rollback:** chỉ image/config đúng service mới, theo CODEX_QA_REVIEW_UI_DEPLOYMENT_RESULT.json, CODEX_QA_REVIEW_NAVIGATION_DEPLOYMENT_RESULT.json và CODEX_QA_REVIEW_INPUT_FIX_DEPLOYMENT_RESULT.json; không restore DB cũ đè dữ liệu hoặc rollback các bản sửa trước. Bằng chứng chính: CODEX_QA_REVIEW_UI_QUALIFICATION.json, CODEX_QA_REVIEW_UI_FINAL_READBACK.json, CODEX_MAIN_CONTINUATION_CHECKPOINT.json. Mọi Native write tiếp theo vẫn cần preview/exact hash/approval mới; approval cũ đã consumed.
