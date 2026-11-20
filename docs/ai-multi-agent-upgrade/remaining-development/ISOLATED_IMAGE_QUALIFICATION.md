> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# ISOLATED IMAGE QUALIFICATION

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

Clone riêng: qldapm-rd-db/core/gateway-20261018; localhost18095/18096, mạng nội bộ + loopback bridge10.254.236.0/28. Không public tunnel mới, không Docker Desktop restart, không Main DB. Private state trong operator/remaining-qualification-20261018. Credentials mới chỉ lưu private.

Khôi phục full Staging backup vào DB mới, rồi tạo5synthetic fixture users13PM,14BA-PM,24BE,25FE,26QA; đây không phải real stage-owner. FixtureTOTP chỉ cho các tài khoản mới trong clone. Work Package448 tạo bằng canonical UI và449 ở project mới để kiểm thử ACL. Không sửa dữ liệu copied business cũ.

Gateway384MiB, Core2GiB/8threads, PostgreSQL512MiB, n8n CLI clone512MiB. Chỉ đo5user; không gọi20-user in-memory simulation là capacity. Benchmark5trình duyệt kết quả giảm từ49–57s còn3.3–4.5s nhờ scoped Native reads; timing là snapshot local, không SLO tổng quát.

Backup thật `2c70757d-586c-4c20-b876-7d464778e9ba`:3SQLite restore logical hashes khớp; PostgreSQL restore vào rd_restore_1792317071 trên owned DB:221fingerprint (gồm sequences),372Work Package khớp. qldapm_knowledge2bảng legacy trống;4SQLite knowledge document hiện hữu giữ nguyên.

Rollback Gateway cũ006b9c6c trên copy post-candidate: native read/history/integrity PASS, không thay state gốc. Candidate restored Gateway search5roles PASS. Core image cũ giữ lại, không boot-test như một cặp rollback; no migration giảm rủi ro, không coi đó là proof runtime.

n8n: workflow status và daily thật chạy CLI với credentials mới, daily ready5/model_calls0; gateway workflow_error HMAC contract dùng execution900001 tổng hợp, không tuyên bố ErrorTrigger fault injection mới. Source/operator/Python tests tách biệt live Native/Edge UAT.

Deployment đang BLOCKED_OWNER_APPROVAL. Dùng preview app-only; chưa chạy trên serving stack. Các artifact ghi image riêng; final parity và final browser phải khớp current candidate-images.json.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
