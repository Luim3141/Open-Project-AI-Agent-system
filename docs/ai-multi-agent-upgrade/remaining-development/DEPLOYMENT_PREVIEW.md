# Preview triển khai Staging — CHƯA THỰC HIỆN

Approval SHA-256: `265ab363875b7ec0610e4ec90fb945382630356118ae46331e46c48609b3020f`.

Chỉ thay **staging-web** bằng `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` và **staging-gateway** bằng `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`; Core8threads. Reload existing **local-backup** watcher để nhận optional knowledge snapshot. Không restart/tạo lại db,n8n,n8n-editor,Quick Tunnel; không Main, tài khoản/TOTP/RBAC, migration hoặc native business write. Gemini key/policy đã lưu giữ nguyên, không yêu cầu nhập lại. Không smoke Google; G2 vẫn ownerblocked.

Tác động: public OpenProject Staging có thể tạm không truy cập được trong lúc Core khởi động (dự kiến2–5phút, cần đo thực tế); Quick Tunnel container giữ nguyên. Main/CSDLDPT không thuộc thao tác.

Trước apply: xác minh lại labels/image-lock/no active-or-unknown jobs, backup Staging mới; bản `2c70757d-586c-4c20-b876-7d464778e9ba` đã có proof221fingerprint/372WP và3SQLite restore. Giữ nguyên bản backup cũ. Không sửa/xóa data để vượt qua preflight.

Sau khi owner duyệt đúng scope, lệnh chuẩn bị là:

```powershell
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\provision_local_stage.py' --application-only --gateway-image 'sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea' --core-image 'sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99'
```

`--application-only` đã có21focused tests, nằm trong520frozen regression; read-only Compose config + lineage PASS trong deployment-readonly-preview.json. Không dùng provision rộng mặc định vì có thể chọn tunnel/n8n.

Sau apply: chờhealth, kiểm tra source/image hashes và Native/read-only UI cho5real roles, actor/RBAC/citations, key/config hashes và restart policies. Không tạo fixture trên serving Staging và không sửa Work Package hiện hữu. Không dùng clone synthetic credentials cho serving.

Recovery: trước rollback giữ thêm copy post-attempt state/receipts; khôi phục private runtime manifest/env/image-lock phù hợp rồi chỉ thay lại2appimages cũ (Gateway006b9c6c,Core8a42c7ef). Không restore/drop database, không xóa knowledge/AgentRun và không quay vòng credentials. Nếu phải về Gateway cũ sau khi có local runs, fence AI bằng maintenance trong lúc đối soát; không coi backward-compatible schema là proof fresh-ACL của tính năng mới trên binary cũ. Native OpenProject data/keys được giữ. Gateway copy rollback và fullDB restore đã kiểm thử; cặp Core+Gateway cũ chưa boot-test như cặp.

Owner approval cần vì mụcII trong request quy định phải hỏi trước restart/deploy container đang phục vụ. Phê duyệt này không bao gồm Main, public tunnel restart/fault, Native fixture writes, TOTP hoặc billing.
