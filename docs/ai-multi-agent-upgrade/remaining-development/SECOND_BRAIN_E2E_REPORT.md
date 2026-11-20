> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# SECOND BRAIN E2E REPORT

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

Phạm vi UI/API: tài liệu nghiệp vụ trong Native Work Package (subject + description). Chỉ nhận native ID; không đọc file/URL, không nhận content/actor/project/role tùy ý từ client. Source identity `actor:<id>:wp:<id>`; actor/project từ phiên và cấu hình backend.

FTS5 thật, normalized query, bounded ranking/chunks, role/project filter và actor metadata. Trước snippet/citation phải Native.package lại cùng project và lockVersion. Actor thuộc hai project đã được kiểm thử thật: Native đọc được fixture project khác, Gateway read/ingest vẫn403. Không chia sẻ index của actor khác.

Update cùng source thay revision/chunks/FTS trong transaction, chống revision cũ ghi đè; dedup, metadata change, deindex riêng actor. Deindex không xóa Work Package. Nguồn bị đổi/revoke bị ẩn; không dùng index làm nguồn sự thật.

Runtime store là `/state/knowledge.sqlite`, WAL/foreign_keys/busy_timeout, đóng connection khi lỗi/corruption. Không tự xóa/recreate file hỏng. Schema PostgreSQL qldapm_knowledge tồn tại hai bảng legacy trống (đã đếm trên bản restore), không phải runtime backend và không tự đồng bộ/pgvector.

Có online backup riêng và tích hợp optional knowledge.sqlite vào local_backup.py; check_backup_sqlite.py kiểm tra cả gateway/knowledge/n8n. Backup thật `2c70757d-586c-4c20-b876-7d464778e9ba` đã phục hồi kiểm tra logical hashes. Cold copy4document hiện hữu mở được trên candidate, không mất bản ghi. Không mở SQLite/WAL đang chạy từ Windows; dùng in-container hoặc cold backup.

`api-uat-1792315548.json`:5actor ingest/search, stale-hide/reindex/deindex/actor isolation, real cross-project denial,5docs/5chunks physical backup, restart persistence. `rollback-qualification.json`:5actor search qua Gateway khôi phục từ snapshot. `existing-knowledge-compatibility.json`, `predeployment-backup-sqlite-restore.log`, `predeployment-native-restore.json` bổ sung kiểm tra dữ liệu hiện hữu. Source storage tests không thay cho các hành trình này.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
