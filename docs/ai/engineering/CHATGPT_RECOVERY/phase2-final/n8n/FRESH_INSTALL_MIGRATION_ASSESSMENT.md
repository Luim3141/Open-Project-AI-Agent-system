# Supported fresh-install entities path — assessed, BLOCKED

Ngày02/11/2026, kiểm tra đúng n8n2.43.6 image `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`. [CLI/source evidence](fresh-entities-assessment-result.json) chứa UTC/commands, actual help output, Git HEAD và SHA256 các file vendor đã đọc. Chỉ chạy help/source trong disposable networknone containers không mount data; không export/import vào MAIN hoặc custom-update clone DB. Mỗi container khám phá có memory/swap cap768MiB và chạy tuần tự.

Đường đã xét: `export:entities` có execution history → `import:entities` vào installation mới có instance key mới, giữ user/project/workflow/history/sharing, sau đó import plaintext credentials. Đường này bị chặn ở capability gate: không có supported control đã quan sát để loại riêng persisted deployment-key artifacts và migrate các inner encrypted resources một cách nhất quán.

| Actual command | Exposed flags ngoài `--help` |
| --- | --- |
| `n8n export:entities --help` | `--outputDir`, `--includeExecutionHistoryDataTables`, `--includeDataTableRows`, `--keyFile` |
| `n8n import:entities --help` | `--inputDir`, `--truncateTables`, `--keyFile`, `--skipMigrationChecks`, `--skipTogglingForeignKeyConstraints` |

Không có exposed `--excludeTables`, `--includeTables` hoặc deployment-key exclusion. Export command chỉ tạo excluded set cố định cho5 execution tables khi không bật history; service nhận excluded-set nội bộ không đồng nghĩa CLI cung cấp quyền chọn arbitrary tables. Không gọi internal service tùy biến để giả là supported CLI. Giữ migration/foreign-key checks; không dùng skip flags để ép PASS.

Source pinned image:

- `export.service.js` đọc `SELECT` raw column values, serialize từng entity thành JSONL, rồi gọi `Cipher.encryptV2` cho **khối export**. `--keyFile` chỉ là custom encryption key của lớp envelope này. Không decrypt/re-encrypt từng secret nằm trong column values.
- `import.service.js` decrypt khối JSONL bằng custom key rồi normalize JSON columns và `INSERT` các entity values. Không tự rewrap deployment keys hoặc đổi các inner ciphertext theo instance key mới.
- `getImportMetadata` nhận mọi recognized entity JSONL; không có key-metadata migration hook đã quan sát. Trên DB được bootstrap, `--truncateTables` xử lý empty-table constraint nhưng không biến old wrapped values thành new-key values.

[Tài liệu CLI chính thức](https://docs.n8n.io/hosting/cli-commands/) mô tả entities để chuyển database type, cần empty destination và history flag nếu muốn execution history. Nó không cam kết instance master-key cutover. Source2.43.6 còn đánh dấu entities feature under development. Không suy rằng custom export transport key là instance master-key rotation.

## Resources thật có trong snapshot

[Read-only clone inventory](encrypted-resource-inventory.json) phục hồi portable kit vào networknone Linux tmpfs, memory768MiB, không DPAPI, không MAIN mount; 4/4 credential decrypt và published/sharing16 vẫn đạt. Inventory chỉ phát số lượng/types/column names/source methods và file hashes, không values.

`deployment_key` có **8 rows**:

| Type | Algorithm | Rows |
| --- | --- | --- |
| `data_encryption` | `aes-256-cbc` | 1 |
| `data_encryption` | `aes-256-gcm` | 1 |
| `instance.id` | null | 1 |
| `jwe.private-key` | `RSA-OAEP-256` | 1 |
| `oauth-server.signing-key` | `ES256` | 1 |
| `signing.binary_data` | `aes-256-gcm` | 1 |
| `signing.hmac` | `aes-256-gcm` | 1 |
| `signing.jwt` | `aes-256-gcm` | 1 |

Row algorithm không tự chứng minh encryption/wrapping của mọi inner value; `instance.id` là identifier, không được tự xóa như secret. Không chỉ có4 credentials. Source inventory tìm78 Cipher callsites, bao gồm MFA, SSO/LDAP, OAuth/JWE/signing, runtime/dynamic credentials, trusted-source store, external secrets, source-control preferences và credential overwrites. Các feature có code không đồng nghĩa MAIN đã cấu hình/sử dụng. Candidate-column scan ghi45 columns; các foreign keys, flags và password hash không được suy là instance-encrypted data. Generic `settings.value`, credential `data` hoặc embedded secrets đòi hỏi schema/source-aware classification; không tuyên bố audit này bao phủ mọi secret. Nhận diện giới hạn là lý do không cho full-resource migration PASS.

Plaintext credential import không migrate các deployment/auth/signing resources còn lại. Root-cause clone trước đã chứng minh2 existing DEK wrappers không unwrap bằng new key và vendor credential export thất bại dù import4/ciphertext4 đổi; xem [RESULT](RESULT.md). `--keyFile` transport wrapper không thay đổi kết luận đó.

Không sửa archive JSONL để xóa key rows, không chỉnh SQLite, không manual-rewrap keys, không truncate/skip checks rồi tự coi là supported migration. Không chạy một fresh-install mutation sau capability gate fail, vì nó không thể chứng minh yêu cầu bảo toàn toàn bộ users/history/shares/encrypted resources chỉ với exposed controls đã thấy.

**Smallest next plan:** giữ MAIN/key hiện hành; dùng portable old-key kit cho recovery. Cần vendor-supported full-instance master-key migration hoặc vendor xác nhận chính xác resource list/rewrap sequence cho2.43.6 trước khi thử clone mới. Phương án fresh-install chỉ workflows/credentials là phạm vi hẹp hơn, cần owner/sharing/history/auth cutover plan riêng và chưa được xem là thay thế tương đương. Khi có supported path, kiểm tra exact owner/shares/16 published/webhooks, mọi encrypted resource, new-key restart/decrypt4, signed ACK và old-key rollback rồi mới xét MAIN gate.

Trạng thái: **BLOCKED_NO_SUPPORTED_DEPLOYMENT_KEY_EXCLUSION_OR_INNER_RESOURCE_REENCRYPTION**. New-key full-install restore/restart/business verification NOT_RUN; old-key restore proof trước được giữ nguyên. Không có MAIN mutation hoặc key rotation.
