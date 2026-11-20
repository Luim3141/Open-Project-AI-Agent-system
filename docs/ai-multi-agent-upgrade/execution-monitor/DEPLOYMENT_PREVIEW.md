# Preview triển khai Execution Monitor — CHƯA APPLY

Owner review target: `D:\AI project\QLDAPM chat`, Staging Compose project `qldapm-ai-stage`.

Thay đúng2image:

- `staging-gateway`: từ `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80` sang `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`.
- `staging-web`: từ `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` sang `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20`.
- Reload `local-backup` watcher hiện hữu theo provision `--application-only`; giữ nguyên backupimage và dữ liệu.

Tác động: OpenProject/AI Staging có thể gián đoạn khoảng2–5phút khi Core khởi động. Giữ nguyên QuickTunnel, db, n8n/n8n-editor, Main/CSDLDPT, dữ liệu/credentials/TOTP/RBAC/nativegates và Gemini FreeTier/model/key/billing. Không GoogleAPI smoke, không Nativebusinesswrite, không promoteMain. DockerDesktop và WSL không restart/di chuyển.

Đã qualify:196Windows/127Linux/25browser assertions;51Gateway/47Corefile hashes equal source/image/clone; Native migrations không đổi. Backup ac4c5ba9-7308-45c1-9ed4-794318b0d490 restored221PGtables/assets/config+3SQLite;oldGateway additiveSQLitecompat PASS.18servingcontainer IDs/images/starttimes giữ;221Nativefingerprints/372WP và ledger517 giữ. Runtime oldGateway/Core vẫn serving.

Sau approval, kiểm tra sourcehash/imageownership/image-lock/noactivejobs và saved privatepolicy/keyhashes, giữ snapshotmanifest/env/lock rồi lấy backupMỚI/coldrestore. Nếu drift hoặcactivejob thì dừng apply để đốisoát, không sửa dữliệu để vượtpreflight. Lệnh dự kiến (chưa chạy):

```powershell
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\provision_local_stage.py' --application-only --gateway-image 'sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b' --core-image 'sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20'
```

Sau apply: chờhealth, source/image/runtime parity, Nativecounts/privatehashes/FreeOnlypolicy, Playwright trên publicQuickTunnel bằng savedrolecredentials; mởhistoricalrun và runhistory/replay/ACLdeny, không modelcall. Chỉ COMPLETE_ON_STAGING sau proof.

Rollback: giữ postattemptstate/receipts; khôi phục snapshotmanifest/env/image-lock và chỉ2appservices về parentdigests phía trên; backupwatcher giữ qualifiedimage. Không restore/drop PostgreSQL, không xóa eventtable/ai_runs/knowledge hoặc quayvòng credentials. ParentGateway đã mở được additiveSQLite copy và giữ42events; Native schema không đổi. Không tựretry unknownmutation.

Giới hạn: telemetry lịch sử thiếu Revieweroutput/agenttiming đượcghi rõ; không backfill. DefaultDockeraddresspools đã đầy từhistoricalnetworks; qualification dùng checked-disjoint internal/28, không cleanup networkhiện hữu; deployment dùng networkđangcó.20usercapacityhoãn.

Approval cần theo **mụcXV “TRIỂN KHAI VÀ PHÊ DUYỆT” của attachmentowner a0e1ea9a**: “Trình kế hoạch ngắn gọn và xin tôi phê duyệt trước khi thay container.” Chỉ phê duyệt đúng phạm vi previewnày; chưa cấpapprovalMain/Tunnel/n8n restart/TOTP/billing.
