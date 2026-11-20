# QLDAPM recovery implementation plan — 01/11/2026

> Execution: superpowers:executing-plans; user đã yêu cầu triển khai liên tục, không dừng ở kế hoạch. Các audit độc lập dùng superpowers:dispatching-parallel-agents.

**Goal:** sửa các lỗi được tái hiện, lưu evidence và bảo toàn dữ liệu; không suy test logic thành Human UAT.
**Architecture:** giữ Gateway/Store là coordinator, OpenClaw là runner, n8n là automation. Sửa tại chỗ; không thêm runtime/dependency.
**Tech stack:** Python/unittest, Rails/ERB, SQLite/PostgreSQL, Docker/WSL, GitHub plugin.
**Spec:** bản bàn giao người dùng tại attachment `787c58f5-737f-48c6-93cb-0b5d58fc157a/Pasted text.txt`.

## Constraints

- Không Computer Use; không gọi Gemini mới khi deterministic tests đủ.
- Project5 read-only; không xóa WP/DB/volumes; #379 tiếp tục IN PROGRESS.
- Không merge, force-push, đổi provider/model/quota; giữ nguyên staging.
- Snapshot trước sửa vì phần lớn source untracked. Deploy có pin image và rollback riêng; không restore DB cũ.

## Review focus

- AUTO phải sống qua subprocess polling; OFF/PAUSE/CANCEL vẫn chặn.
- GitHub failure/partial không được báo SUCCESS; failed item phải retry được.
- PR mapping phải lấy child WP từ receipt, đúng project6/repository; không ghi parent379/Project5.
- Cache không trộn repository và force refresh phải fetch thật, kể cả empty response.
- Report/RAG không chứa dữ liệu giả; kết quả thiếu bằng chứng phải ghi rõ.

## Tasks

1. **Discovery và protection** (root): ghi Git/container/image/DB baseline và SHA256 parity; snapshot source trước thay đổi. Lưu dưới run directory từ CURRENT_RUN.txt.
2. **GitHub reconciliation** (root): `gateway/engineering_github_sync.py`, matching tests, Rails command controller và GitHub status bar. Viết regressions cho table join/child mapping/scope, API failure/partial/retry/counts, cache. Chạy red, sửa tối thiểu, chạy green. Giữ distinct PR merge vs deployment/acceptance; không auto-transition Done.
3. **Core lifecycle** (core agent): isolated tests → tái hiện AUTO worker fence → snapshot → patch worker → regression. Không live admission.
4. **n8n audit** (n8n agent): read-only published workflow graph/executions; kiểm tra event wiring và business side effects, không trigger live jobs.
5. **Reports/RAG** (rag agent): isolated tests và read-only persisted reports; sửa lỗi đã chứng minh, ghi rõ limits.
6. **Integration/deployment** (root): review tất cả patch; offline regression, Linux checks; build only changed source onto pinned r24 images; verify no active run before deploy. User's final production approval boundary applies: candidate/test and rollout instructions concrete before requesting any required approval.
7. **Handoff** (root): defect register, architecture update, source diff/snapshots, test matrix với exit code/log/read-back; WP385 forensic evidence; UAT guide based on actual endpoints. Chưa đạt gate nào giữ NOT VERIFIED/PENDING OWNER UAT.

## Scope after this batch

Đây là batch phục hồi đầu tiên trong takeover lớn; không tuyên bố hoàn thành toàn bộ milestones khi chưa chạy controlled fresh E2E, recovery và Owner UAT.
