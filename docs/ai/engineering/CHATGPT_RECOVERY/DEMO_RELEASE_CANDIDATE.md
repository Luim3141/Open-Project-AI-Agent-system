# Mini Task Manager — exact release candidate

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

Candidate commit `0498ceeda97cd3e856a975129129e71f6c94a3dd`, đã có trong local Git objects, export exact tree bằng git archive; không merge/push/checkout branch của user. Parent chain có health/summary cùng CRUD/search/UI trước đó; remote PR1–6 snapshotPhase1 không thay bằng localbranch assumption.

Application thực là FastAPI/Uvicorn (không dùng giả định Flask từ yêu cầu). Live18791 vẫn release `def9d0a8852af42a407bd42fb0051615a2de9331`, PID/cwd/server command đã đọc ởWSL. GET/healthz404, GET/tasks/summary405 vẫn khớp read-back cuối; PR merged-to-feature không phải deployed.

Candidate:15pytest testsPASS với pinned installed venv + actual Node binary, không skip. Actual HTTP server cổng loopback tạm: health200/summary200, CRUD/search/422/404 và total invariant đạt. Copy SQLite live bằng read-only backup vào private clone, schema/rows giữ sau fixtureCRUD; dữ liệu nguồn hiện0rows nên không chứng minh upgrade một corpus lớn. Persistence được kiểm trong suite, actual HTTP compatibility trong demo-http-compat-result.log. Không đổi server18791/data thật.

Approval boundary riêng: backup demo SQLite/current release manifest; launch candidate on temporary port first; preserve live DB schema/data; switch exact release path/command to chosenSHA only after owner approval; validate health/summary/CRUD read, X-QLDAPM-Revision and persisted row fingerprint; rollback command/release to def9 while preserving data. Không auto-merge PR4–6/force-push; phải recheck selectedSHA/base/dependency chain ở thời điểm cutover. No paid dependency/provider changes.
