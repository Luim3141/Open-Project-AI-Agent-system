# OPEN ISSUES AND PRIORITIES

Updated: 2026-10-18T17:23:52.679063+07:00

**STAGING_DEPLOYED_VERIFIED. Serving approval/apply/recovery đã hoàn tất; G2 vẫn ownerblocked.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

- Không còn P0/P1 được phát hiện chưa xử lý trong phạm vi candidate đã nghiệm thu. Owner gates và giới hạn dưới đây vẫn mở.
- RESOLVED: owner-approved app-only Staging rollout + backup watcher reload, power-loss recovery và5realrole UI/Supervisor PASS; xem STAGING_DEPLOYMENT_REPORT.md. Main chưa được promote.
- BLOCKED_OWNER_VERIFICATION: G2/live Gemini billing/free tier nghiệm thu; phiên này0Google calls, key/policy cũ giữ nguyên.
- NOT_APPROVED_DO_NOT_ROTATE: TOTP của người thật. Giữ kết quả recheck take-over; không đánh dấu DEF-08 fixed dựa vào báo cáo Wave6.
- DEFERRED_BY_OWNER:20-user capacity/G7.
- P2 upstream Native login: preauth HALError;5login/TOTP vẫn thành công, Assistant postauth không lỗi. Không sửa Angular/vendor vì ngoài phần thay đổi.
- P3 presentation: agent Markdown hiển thị dạng text escape; giới hạn formatting được giữ để không mở raw HTML/remote image. Báo cáo/citations/plan vẫn dùng được.
- Limitation: Core cũ chưa boot-test như cặp rollback; Gateway copy rollback và full Native/SQLite restore đã có proof.
- Limitation: arbitrary file/PDF/URL ingestion không thuộc endpoint mới; Native Work Package là source-of-truth của phạm vi này.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
