# Independent source review — Phase 3.1

Reviewer: `/root/release_review`, thực hiện read-only source/isolated fixtures; không production mutation. Root ghi lại báo cáo từ kết quả reviewer trong phiên này. Git HEAD không đại diện source untracked; release dùng image/source allowlist.

## Findings và xử lý

1. **Important:** `AGENT_FAILED` bị xem như successful end; completed Dev step cũ che failed rework. Đã sửa precedence theo failure của role hiện tại, successful end riêng; hai regression RED→GREEN.
2. **Important:** Resume đã queued rồi Owner OFF, Resume lần nữa tăng recovery dù chưa thực thi. Đã giữ marker pending-resume khi OFF và dùng cùng requeue path, không tăng count; giữ source/unknown-write/version guards. Fixture RED→GREEN, audit `queued-unpaused` được giữ tương thích.
3. **Important:** UI đọc `severity`, backend trả `level`; ERROR thành INFO. Partial nay fallback đúng `level`.
4. **Important:** Provider error tạo fence vĩnh viễn do chỉ xét receipt cũ. Chỉ cho manual continuation khi existing policy/key-bound readiness READY, thành công sau lỗi và trong 300 giây; vẫn giữ nguyên failure category lịch sử. Không gọi provider để làm health check. AUTO vẫn chỉ tiếp tục lỗi internal-budget đủ điều kiện.
5. Root finding được reviewer xác nhận: blocker note hardcode parent379. Đã ghi child theo run contract và giữ WP/run reference; regression RED→GREEN. Không sửa note lịch sử.

Reviewer re-read latest source và chạy Owner recovery **20/20**, health **3/3**, Node Owner UX/Reader PASS; không còn Critical/Important chưa xử lý trong phạm vi review. Sau review root thêm enrichment cho Execution Center `runs` (giữ result document), có regression missing-resume RED→GREEN; Inspector lấy Native business status qua Native client đã được cấp quyền; thêm notification bell count từ persisted count.

## Giới hạn

Reviewer không thực hiện Ruby sanitizer runtime, serving parity hoặc deployment. Root qualification thực hiện riêng: immutable Gateway tests, actual Core Rails/Native/session/CSRF clone, sanitized Markdown và production read-back. Không browser automation; responsive/pixel/text zoom/accessibility thao tác thật và Owner acceptance vẫn PENDING OWNER.

## Final follow-up review

Reviewer re-read final changes, Owner recovery **22/22 PASS**, Node Owner UX PASS. Root reproduced and fixed actual SQLite nested write-lock issue: readiness (whose existing Store provider_wait opens a transaction) now runs before resume BEGIN IMMEDIATE; an internal readiness snapshot is checked against latest failure after acquiring lock. Reviewer independently inserted a newer scoped429 between readiness and resume; the resume remained fenced. No Critical/Important remaining in this reviewed scope. Plan timestamp lookup now covers all returned plans, failed Resume resolves child reference, direct UUID links use existing Inspector handler, pipeline labels distinguish ten observed checkpoints from eight business reference steps. No production/provider/GUI actions by reviewer.
