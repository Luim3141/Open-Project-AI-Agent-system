# Portable encrypted recovery kit — old-key recovery only

**PORTABLE_KIT_LINUX_CLONE_VERIFIED_OLD_KEY_ONLY.** Kit đã được tạo ngoài repository tại:

`C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\portable-n8n-recovery-8a61c9795ada`

Ciphertext và verifier nằm trong `ciphertext/`; independent random256-bit recovery key nằm ở file `recovery-custody/recovery.key`. Không in nội dung key. Thư mục có protected DACL, files kế thừa DACL chỉ current Windows user và SYSTEM với FullControl; kiểm tra theo SID, fail trước secret write nếu không xác minh được. Hai subdirectories trên cùng máy chỉ là tách file, **chưa phải off-host backup hoặc Owner key custody độc lập**.

Ciphertext `n8n-recovery-v1.aesgcm`: **26,740,922 bytes**, SHA256 `47cab825e5e23a130bcbba298c0b1cbe344375d21c28753a74a3797fddcd4155`. Nó chứa byte-for-byte bản cold-volume tar gồm SQLite/WAL/SHM/config và preserved environment snapshot ngày01/11/2026 đã có; không phải snapshot MAIN mới. Provenance raw archive/env và DPAPI source hashes nằm trong [creation evidence](portable-recovery-creation-result.json). Không xóa hoặc ghi đè raw originals, DPAPI backups hoặc user artifacts.

Format: ASCII `QLDAPM-N8N-RECOVERY-V1\n` (đồng thời là AAD), random96-bit nonce, AES-256-GCM ciphertext, tag128-bit; authenticated plaintext là JSON schema `qldapm.n8n.recovery-payload.v1` chứa manifest và base64 của hai byte streams gốc. Mỗi kit generate key/nonce mới, chỉ encrypt một lần. Dùng `cryptography50.0.1` đã cài, không thêm dependency; đối chiếu [API chính thức50.0.1](https://cryptography.io/en/50.0.1/hazmat/primitives/aead/). Linux verifier dùng Node built-in `crypto`.

Tạo kit đã chạy bằng `python docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/n8n/portable_recovery_kit.py`. Lượt đầu dừng ở ACL gate vì Windows PowerShell không load được `Get-Acl` trong inherited module environment, trước khi tạo key/ciphertext; chuyển verifier sang PowerShell7 đã có và chạy lại. Thư mục rỗng của lần fail không chứa secret. Không hạ ACL gate.

Kiểm tra lại kit mà không đọc DPAPI source:

```powershell
python docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/n8n/portable_recovery_kit.py --verify 'C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\portable-n8n-recovery-8a61c9795ada'
```

Code cuối cùng được verify ngày02/11 từ `07:51:28.991574Z` đến `07:51:36.432315Z`; [evidence cuối](portable-recovery-verification-result-e382fdbaca42.json) ghi exact image, command và code hashes. Host wrapper SHA256 `6c5d41ba26cc16c98974bcb37f5e3bb50dadd86f0476bafa3a5d48c3dacdd537`; packaged Linux verifier SHA256 `f5cd2e4e6996796a61fe60d65038e005a248359143fc7dab17f52310d328e388`. HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e` đi kèm uncommitted file hashes; không lấy HEAD thay file provenance. Các report trước vẫn giữ nguyên, không cộng số lượt verify thành coverage mới.

Docker verifier chỉ mount thư mục **ciphertext** read-only; không mount repository, recovery-key directory, DPAPI source hoặc MAIN volume. Recovery key32 raw bytes được Python truyền qua stdin, không trong DockerEnv/args. Old instance key được n8n đọc từ original config chỉ trong Linux tmpfs, không truyền qua env/args. Networknone, root read-only, tmpfs mode0700; plaintext exports và decrypted tar/env chỉ ở RAM/tmpfs. Container remove sau test. Không lưu CLI credential output hoặc key vào logs/artifacts.

Kết quả: GCM tag hợp lệ; nguyên byte archive/env khớp manifest; host và Linux tampered-ciphertext rejection PASS; Linux wrong-key và wrong-AAD rejection PASS trước khi parse/extract; SQLite integrity `ok`, 4/4 credentials decrypt, 16 active/published workflows, 16 valid workflow-sharing links, 4 credential-sharing links, 1 owner. Image pinned n8n2.43.6 `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`; export command file hash được ghi riêng. Đây là chứng minh crypto portability/restore bằng identity Linux container không có DPAPI, **không phải physical-machine DR**, new-key migration, signed business ACK hay user acceptance.

Owner recovery custody còn PENDING: cần đưa ciphertext folder cùng verified restore tooling/pinned n8n image tới storage off-host được kiểm soát, và giữ recovery key bằng kênh/lưu trữ độc lập; kiểm tra quyền sau khi chuyển và diễn tập lại. Không đặt key cùng ciphertext ở cùng backup destination. Mất recovery key thì kit không thể giải mã; lộ cả key và kit thì snapshot có thể bị đọc. Không tự gửi key, upload cloud hoặc copy sang nơi chưa được cấp quyền.

MAIN key/retention giữ nguyên, master-key cutover vẫn BLOCKED. Kit làm giảm phụ thuộc DPAPI cho bản recovery này; không revoke key cũ, không scrub lịch sử và không xử lý các raw sensitive backups còn tồn tại.
