# Preview sửa UAT-01 — chưa triển khai

Approval SHA256: `af53a2f8f8ce29096e111901877a3bfdc47bc1ed2b4a63c8dc48f46bf678db1f`.

Lỗi: “chỉ đọc; không ghi thay đổi” bị keyword planner phân loại thành đề xuất chờ PM. Sửa chỉ bỏ qua động từ ghi bị phủ định ngay tại chỗ; một yêu cầu ghi khác vẫn là PROPOSAL_WRITE/REVIEW. Native RBAC, consent, PM-only-write và no-model Supervisor không thay đổi.

Candidate Gateway `sha256:47751dc25b5d8a091946a5371452a07f599f02f15357d2a8ba40626a8b452219`; parent đang phục vụ `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. 41Windows +41Linux targeted tests PASS; UI thật trên clone PM read-only COMPLETED và FE mixed-write REVIEW/no Native change PASS. Operator --gateway-only có19tests PASS; Compose dry-run chỉ thay staging-gateway,18serving ID/start/restart giữ nguyên. Cảnh báo orphan Radmin là container cũ, không remove-orphans.

Thao tác cần duyệt: backup Staging mới, rồi thay riêng staging-gateway; Core3b, database, n8n, local-backup, Quick Tunnel, Main/CSDLDPT không restart. Không gọi Google; không đổi key/account/TOTP/RBAC hoặc migrate/ghi Native. AI Assistant có thể báo chưa sẵn sàng trong lúc Gateway khởi động (ước tính vài chục giây; chưa đo downtime của lần sửa này).

Lệnh sau approval:

```powershell
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\provision_local_stage.py' --gateway-only --gateway-image 'sha256:47751dc25b5d8a091946a5371452a07f599f02f15357d2a8ba40626a8b452219'
```

Guard: exact operator SHA `bd933bc9a61c43084964465a5569121efa829bfab0577ed5e4aa4bbca3dbfb81`, staging lease/labels/lock/images, no active-or-unknown job, saved FreeOnly config checks, fresh full backup + SQLite restore. Không retry khi kết quả apply chưa rõ; đối soát receipts/container/image-lock trước.

Sau apply: health, hash/planner UI regression, key/ledger/data/other18container preservation. Recovery: giữ post-attempt state trước, trở về Gateway6afb bằng targeted service selection và private before-provision manifest/lock, không restore/drop database hoặc xóa SQLite/index. Schema/AgentModels không đổi; rollback không cần migration. G2liveGemini vẫn ownerblocked và Main chưa được promote.
