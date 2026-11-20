# Owner-only off-host recovery procedure

Trạng thái: **TOOLING_TESTED_LOCAL · OFFHOST_CUSTODY_PENDING · PHYSICAL_MACHINE_DR_PENDING**. Không có upload/copy off-host trong Phase3. Đây là kit old-key snapshot ngày01/11/2026, không phải backup MAIN mới hoặc master-key migration.

## Chuẩn bị và custody

1. Owner chọn storage off-host riêng được kiểm soát, xác nhận quyền đọc/ghi và dung lượng. Không dùng public share, GitHub, email, chat hay destination do agent suy đoán. Ghi nhận tên thiết bị/storage và người giữ trong hồ sơ riêng; không ghi recovery key.
2. Chỉ chuyển nội dung **ciphertext/** của kit `portable-n8n-recovery-8a61c9795ada` bằng công cụ Owner đã chọn. Ba file đúng là `n8n-recovery-v1.aesgcm`, `portable_recovery_restore.js`, `FORMAT.json`. Không chuyển cả thư mục kit, `recovery-custody/`, raw tar/env, DPAPI snapshots hoặc plaintext exports vào cùng destination.
3. Recovery key gốc nằm trong `recovery-custody/recovery.key` ngoài repo. Owner tự chuyển/giao custody qua phương tiện độc lập; giữ key tách biệt với ciphertext theo thiết bị, quyền truy cập và vị trí vật lý. Không mở/in key, không dán vào terminal, argument, environment, chat, log, GitHub hoặc email. Agent không đọc hoặc chuyển key trong Phase3.
4. Kiểm tra quyền trên destination bằng công cụ storage/OS của Owner. ACL Windows của bản gốc không tự chứng minh quyền trên USB/NAS/cloud; phương tiện không hỗ trợ ACL cần kiểm soát mã hóa/truy cập riêng. Agent không tự cấp quyền hoặc đổi ACL.

## Xác minh bản ciphertext đã chuyển

Dùng checker từ workspace tin cậy, không chạy script lấy từ bản copy trước khi kiểm tra hash. Owner điền đường dẫn tới **ciphertext directory** trên destination đã chọn:

```powershell
$CiphertextCopy = Read-Host 'Duong dan ciphertext directory tren storage Owner da chon'
python 'D:\AI project\QLDAPM chat\docs\ai\engineering\CHATGPT_RECOVERY\phase3-owner\n8n\verify_ciphertext_copy.py' --ciphertext-dir $CiphertextCopy
```

Lệnh chỉ đọc ba file đã pin SHA256; không nhận key, không decrypt, không thực thi bản verifier và không tạo/copy/upload file. File thiếu/thừa (kể cả `recovery.key`), symlink/reparse point, file vượt32MiB hoặc hash sai đều fail closed. Pins riêng cho đúng snapshot này; không thay pins để chấp nhận một bản copy lỗi.

`CIPHERTEXT_COPY_BYTES_VERIFIED` chỉ chứng minh byte identity. Các trường `offhost_custody=OWNER_ATTESTATION_PENDING`, `destination_acl=OWNER_CHECK_REQUIRED`, `physical_restore=NOT_TESTED` vẫn giữ nguyên kể cả khi đường dẫn là ổ khác. Owner ghi nhận ciphertext hash, thời điểm, destination identity, quyền và custody hoàn thành trong hồ sơ riêng. Không coi drive letter khác là bằng chứng off-host.

## Diễn tập trên máy vật lý độc lập — chưa thực hiện

Chuẩn bị offline pinned n8n image `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795` bằng kênh backup riêng Owner duyệt; kiểm tra image ID sau load. Giữ image và tooling ở chế độ private. Không dùng latest hoặc tự pull phiên bản khác thay thế. Check hashes của ba file trước execution.

Người vận hành dùng recovery key qua stdin binary32bytes, không env/args và không console output; mount **ciphertext/** read-only vào disposable Linux clone, networknone, rootread-only, plaintext chỉ trong tmpfs0700. Không mount MAIN data volume hoặc key directory. Quy trình kỹ thuật đã chạy trên Linux container trong [Phase2 PORTABLE_RECOVERY_KIT](../../phase2-final/n8n/PORTABLE_RECOVERY_KIT.md); wrapper Phase2 chỉ chấp nhận operator root của máy hiện tại nên **không dùng nguyên lệnh đó để tuyên bố restore trên máy mới**. Cần operator chuẩn bị launcher đã review cho exact paths trên máy khôi phục trước diễn tập; không tự sửa đường dẫn để lấy PASS.

Gate restore: GCM auth/tamper/wrong-key/wrong-AAD rejection; SQLite integrityok; credentials4/4decrypt; active/published/share16/16; credential-share4; owner1. Sau đó cần restart/business integration/webhook checks trong clone isolated theo phạm vi được duyệt. Không gọi readinessHTTP200 là businessPASS. Hủy clone/tmpfs sau test; chỉ lưu kết quả sanitized, UTC, exact image/tool hashes. Không restore MAIN hoặc xóa backup gốc/cũ.

## Tiêu chí hoàn tất DR

Chỉ đóng off-host custody sau Owner xác nhận destination độc lập, ciphertext byte-check và custody key riêng. Chỉ đóng physical-machine DR sau restore thực trên máy khác và kiểm tra nghiệp vụ được ghi nhận. Master-key migration vẫn **BLOCKED** theo Phase2 persisted-DEK evidence. Mất key không thể giải mã kit; lộ đồng thời key và ciphertext làm lộ old-key snapshot. Snapshot hiện tại không bao phủ thay đổi MAIN sau01/11.
