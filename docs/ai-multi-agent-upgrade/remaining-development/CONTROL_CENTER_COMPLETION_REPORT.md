> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# CONTROL CENTER COMPLETION REPORT

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

Core controller/ERB dùng API thật: registry local, current own runs/history, plan/dependencies/completed steps, outputs/native input links, approval/audit, errors. Không lấy checklist113DONE làm trạng thái live. Current page10mục; filter/sort ghi rõ trong trang; next/previous/refresh qua backend có ACL.

Trang run/proposal không tải lại toàn bộ dashboard/report; vẫn đọc kết quả bằng Native ACL/version và Control Center. Core8threads để5request UI còn chỗ cho Native callbacks;2threads đã gây deadlock trong clone và được sửa ở source stage.yml.

Quota/model lấy policy đã validate và ledger local: official limit tách local safety cap, RPM/inputTPM60s, RPD theo ngày Pacific; không coi historical peak AI Studio là usage hiện tại; không đoán remaining/output tokens/TPD hoặc client khác. Clone không copy provider key nên UNKNOWN là đúng. Không kiểm tra billing trực tiếp trong UI; G2 chờ owner.

Có empty/error/running state, actor-bound history và responsive390/1280. Nút/labels mới không dùng fake data. Output được escape/plain text; Markdown formatting còn hạn chế, không tạo raw HTML hoặc remote image fetch.

Bằng chứng: actual5-role browser UAT, browser-five-concurrent-results.json, control-center-uat.json + csrf-qualified.json (rerun đúng form action), core-package-parity.json. Lỗi thử CSRF trước đó dùng nhầm /command và nhận404 là lỗi harness; bản đúng /commands bị422. Pagination20/10 là lỗi thật đã sửa; Turbo DOM wait sửa ở test, không nới expected.

Baseline Native login có2HALError trước xác thực, không có lỗi Assistant sau xác thực; browser-error-diagnostic.json ghi riêng. Không báo console toàn bộ hệ thống sạch.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
