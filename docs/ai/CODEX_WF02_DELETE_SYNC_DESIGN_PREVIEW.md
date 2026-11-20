# WF02 deletion — design preview, chưa triển khai

Main hiện không có nguồn chứng minh permanent deletion. API404, mất visibility hoặc một inventory thiếu trang không phân biệt được deletion với ACL/revoke/race. Chúng không cho phép physical delete SQLite/Qdrant. Existing incremental cursor/outbox giữ dữ liệu, chặn retrieval bằng Native ACL/version và khôi phục visibility khi nguồn trở lại.

Qualification cô lập `test_native_incremental_sync`: 9 tests, gồm create/update/hash/retry/restart, complete inventory, withdrawal/reappearance và forged delete proof. Không xóa nguồn hay vector Main. Bằng chứng external event Main hiện có là các Native derived parent updates372/373 đã được machine worker phát hiện; không gọi đó là một external client mutation mới.

Muốn hỗ trợ permanent deletion cần một producer server-side trong transaction Native delete, tạo durable outbox chứa project/resource/previous version/source hash, authenticated actor, operation ID và commit identity. Gateway chỉ nhận producer được xác thực, deduplicate event ID, kiểm tra phạm vi/ownership và retry cache-only. Không nhận actor/approved/signature do caller tự khai làm bằng chứng. Producer/migration này chưa tồn tại; chưa được duyệt triển khai Core/schema và chưa có recovery hoàn chỉnh cho vector deletion.

Trước khi apply cần preview migration tương thích, isolated transaction/rollback/restart/duplicate/forgery qualification, backup có restore proof, exact Main delete scope và human approval riêng. Không có Native delete proposal trong phiên này. Status: **BLOCKED_TRUSTED_DELETE_PRODUCER_AND_RECOVERY**, existing safe withdrawal **PASS_POLICY_ENFORCED**.
