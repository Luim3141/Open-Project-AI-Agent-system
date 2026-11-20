# Triển khai và rollback

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

Candidate Gateway `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`; Core `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20`. ParentGateway40cb4806/Core3b09393d. Exact paths/hash manifest trong candidate-images.json;51Gatewayfiles/47Coreoverlayfiles; source-image-clone parity và immutable offline tests. Native db/migrate/fixtures hashes không đổi; chỉ additive GatewaySQLite event table/index.

Chưa deploy. User attachment mụcXV: build→migrations→backup/restore→parity→rollback→preview→approval trước thay serving Core.

Preview phạm vi: chỉ thay image staging-web/staging-gateway; provision application-only có reload local-backup watcher hiện hữu. Dự kiến gián đoạn2–5phút. Main/CSDLDPT, QuickTunnel, n8n/n8n-editor, database và credentials/RBAC/TOTP/model/billing không thuộc mutation. Không public Gateway mới.

Preflight sau approval: kiểm tra owner/labels/image locks/sourcehashes/noactivejobs; snapshot protected manifest/env/image-lock; backup mới và coldSQLite restore, giữ mọi backup; không bỏ qua preflight nếu serving drift. Dùng existing provision_local_stage.py --application-only với exact2image IDs; không chạy mặc định rộng. Sau apply verify health/lineage/filehash/Nativecount+privatehashes+FreeOnlypolicy; Playwright thật qua QuickTunnel mở storedrun, không Googlecall. Runtime config persisted vẫn tự phục hồi sau DockerDesktop manualstart, không cần nhập lại key.

Rollback: capture post-attempt state/receipts trước; restore saved private manifest/env/lock và recreate đúng2appservices với parentimages. Không restore/drop DB hay xóa eventtable/outputs/knowledge. Gateway40cb compatibility mở được SQLite thêm events, rows retained. Native không migration nên rollbackCore không cần DB reversal. Backup watcher giữ qualified image. Nếu rollback vì lỗi ACL của Monitor, khóa đường Monitor bằng oldCore+Gatewaypair và đối soát; không retry unknown businessmutation.

Fresh backup ac4c5ba9-7308-45c1-9ed4-794318b0d490 đã restore221PGtables/assets/config và3SQLite. Đây là qualification trước approval, phải lấy mới lại trước deploy thực. Docker default network pools đã đầy do nhiều historical networks; drill dùng explicit checked-disjoint internal/28 và chỉ cleanup labelledtemporaryresources. Không xóa network hiện hữu; deployment dùng network đã có.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.
