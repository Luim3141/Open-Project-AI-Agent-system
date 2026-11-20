# Phase 2 — n8n security, 2026-11-02

**MASTER_KEY_CUTOVER_BLOCKED · WF04_RETENTION_BLOCKED · CLONE ROOT CAUSE AND OLD-KEY RESTORE VERIFIED.** Không đổi master key, credentials, retention, workflows hoặc lịch sử MAIN. Không Computer Use, không provider call, không Project 5 write.

Addendum07:51Z: đã tạo [portable AES-256-GCM recovery kit](PORTABLE_RECOVERY_KIT.md), Linux clone decrypt/restore4credentials, published/sharing16, tamper/wrong-key/AAD rejection đạt; recovery không dùng DPAPI ở verify branch/container. Kit là old-key cold snapshot, off-host storage/Owner custody vẫn PENDING, không phải physical-machine DR. [Fresh-install entities path](FRESH_INSTALL_MIGRATION_ASSESSMENT.md) đã kiểm tra actual CLI/source2.43.6 và8 deployment-key rows; không có supported key-metadata exclusion/inner-resource re-encryption được quan sát. Master-key cutover vẫn BLOCKED.

## Bằng chứng đúng revision

[clone-key-diagnostic-result.json](clone-key-diagnostic-result.json) ghi UTC bắt đầu/kết thúc, command, Git HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`, SHA256 của hai harness và các file thực thi trong image. Working tree có thay đổi chưa commit; HEAD không được dùng thay cho file hash. MAIN read-only `docker inspect` vẫn trả image `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`, n8n `2.43.6`. Diagnostic cuối chạy `2026-11-02T03:42:16.088160+00:00` → `03:44:37.681059+00:00`.

```powershell
python docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/n8n/clone_key_diagnostic.py
```

Hai container tên random chỉ có `--network none`, root filesystem read-only, `/tmp` là tmpfs mode0700/uid1000 và mount thư mục harness read-only. Không mount MAIN volume. DPAPI CurrentUser tar/env được giải mã trong RAM rồi stream qua stdin; tar gồm SQLite/WAL/SHM/config. Decrypted credential exports chỉ ở tmpfs; không xuất giá trị, CLI logs hoặc key ra artifact. Container đã bị remove, tmpfs đã hủy. Rollback dùng bản encrypted snapshot nguyên gốc ở một container độc lập. Đây là restore cùng Windows profile, chưa phải DR khác máy/tài khoản.

## Nguyên nhân migration FAILED đã được tái hiện

| Kiểm tra trên cùng DB clone | Quan sát |
| --- | --- |
| Old master key credential export | 4/4 decrypt |
| Persisted `deployment_key.type='data_encryption'` | 2 rows: CBC và GCM |
| DEK unwrap dưới old master key | 2/2 |
| DEK unwrap dưới newly generated master key | 0/2 |
| CLI plaintext `import:credentials` dưới new key | Exit0, báo import4, ciphertext đổi4 |
| Decrypt4 ciphertext mới trực tiếp bằng new instance key, so với dữ liệu gốc trong RAM | 4/4 giống nhau |
| Vendor `export:credentials --decrypted` dưới new key | Exit1, decrypt error; không có output file |
| Persisted DEKs sau import | Không đổi |
| Workflow definition fingerprint trước/sau | Giống nhau |

Source thực trong image giải thích causal chain:

1. `dist/commands/import/credentials.js::readCredentials` chỉ gọi `Cipher.encryptV2` cho `credential.data` dạng object. Nó không migrate toàn bộ deployment secrets.
2. `n8n-core/dist/encryption/cipher.js::encryptV2` lấy active descriptor; khi rotation OFF, `KeyManagerService.getActiveKey` trả `instanceKeyLegacyInfo()` của instance key hiện tại. Ciphertext import mới vì vậy được mã hóa dưới new instance key.
3. Cùng `Cipher.decryptV2`, ciphertext không có key-id prefix đi qua `getLegacyKey()`. `KeyManagerService.getLegacyKey` ưu tiên CBC descriptor **đã lưu trong DB**; descriptor đó vẫn wrapped bằng old instance key. Key mới không unwrap được. Đây không phải lỗi owner, credential type, số lượng import, hoặc key file/environment mismatch: config/env đã được assert bằng nhau trước import, và direct cryptographic control decrypt cả4 dữ liệu mới thành công.
4. Chỉ rewrap legacy descriptor cũng không tự migrate mọi ciphertext cũ/mới: descriptor legacy vốn trỏ tới old key, trong khi credential vừa import dùng new instance key. Những resources không nằm trong credential export vẫn phải được kiểm kê/migrate nhất quán.

Các SHA256 then chốt nằm trong JSON: import command `baa6edaf…1818f3`, key manager `347a8bd3…ed3a4c`, Cipher `e7cb7b46…f0bd56`. Harness đầu phiên dùng nhầm literal `data-encryption` khi query nên đọc0 rows; đã sửa thành source-defined `data_encryption`, thêm assert nonempty, chạy lại. Chỉ kết quả cuối có DEK2/old2/new0 được dùng làm chứng cứ.

[Tài liệu CLI chính thức](https://docs.n8n.io/hosting/cli-commands/) mô tả decrypted export để chuyển credentials sang **installation khác** có secret key khác; không mô tả việc đổi master key tại chỗ trên restored database chứa deployment keys. [Tài liệu rotation](https://docs.n8n.io/deploy/host-n8n/configure-n8n/security/rotate-encryption-keys.md) phân biệt instance master key và data encryption keys. DEK rotation giữ instance key, nên không xử lý việc master key cũ từng lộ. Các tài liệu là bản live đã đọc ngày02/11; semantics 2.43.6 được đối chiếu source pinned image, không suy từ docs phiên bản mới.

Source inventory còn thấy sử dụng Cipher trong SSO/LDAP, runtime/dynamic credentials, external secrets, OAuth JWE và deployment signing secrets. Không kết luận những tính năng đó đang có dữ liệu tại MAIN chỉ vì module tồn tại. Chưa có migration tool chính thức đã được chứng minh bao phủ tất cả resources hiện hữu, lịch sử, user identities và credential ownership. Không chạy SQL sửa deployment-key rows, không xóa key rows để ép reseed, không custom rewrap MAIN.

**Đường được vendor mô tả:** export decrypted credentials rồi import vào installation mới; cần một migration plan riêng để bảo toàn owners/shares/history và các encrypted resources khác. Chưa thực hiện full fresh-install migration. Vì credential decrypt new-key gate đã fail trên clone hiện tại, new-key server restart/webhook/signed ACK/execution không được gắn PASS hoặc dùng old-key business ACK để thay thế.

## Rollback/restore và restart — giới hạn rõ ràng

Fresh restore của encrypted snapshot: SQLite integrity `ok`; 16 active entities, 16 published history links, 16 valid workflow-sharing links, 4 credential-sharing links, 1 owner. Definition fingerprint được giữ. Independent CLI process restart vẫn decrypt4/4 và object exports bằng nhau.

Hai lần khởi động/dừng **server process** n8n trên old-key rollback clone đều trả readiness HTTP200, không thấy key-bootstrap-error, và export sau restart decrypt4/4 giống dữ liệu gốc. Database registry có17 webhook rows, trong đó1 POST `qldapm-lifecycle`. Trong cửa sổ quan sát30s sau readiness mỗi lần, log activation count=0; không dùng readiness/registry rows làm bằng chứng16 workflows thực thi business thành công. Không gọi webhook ghi nghiệp vụ; không có signed ACK trong diagnostic này. Container restart không được kiểm chứng bằng cách giữ tmpfs qua restart; restore sang container độc lập là phép thử khác đã ghi riêng.

## Strict payload policy — vẫn BLOCKED, không mở retention

[security-probes.json](security-probes.json) ghi thời gian UTC từng test, exact command/image/test-source hashes và output tổng hợp synthetic. Hai test redaction/overwrite hiện hữu PASS trong image pinned; overwrite dùng stub storage, chưa chứng minh filesystem thực. Canary arbitrary payload **tái hiện lỗi**: header marker bị che, nested/free-text markers còn nguyên. Exit0 của canary chỉ xác nhận reproduction đúng, không phải security PASS.

Metadata-only retry probe gọi `ExecutionService.retry` thật với storage/runner stubs: thiếu `data.executionData` bị `AbortedExecutionRetryError`; control có execution state chuyển input tới runner. Không thêm regex hoặc triển khai metadata-only patch gây mất replay state. N8n persistence ghi cả webhook input/headers và workflow snapshot trước khi node projection chạy; strict projection trong Code/Set node không bao phủ create/partial/full overwrite/error/manual/retry, cũng không chứng minh transient execution storage an toàn khi retentionOFF.

Gateway `n8n_lifecycle_outbox.enqueue` hiện đã project event keys và publisher chỉ lưu error code cố định; `observe` đối chiếu HMAC, expiry, outbox và durable source event rồi lưu ACK metadata. Đây là giảm rủi ro của lifecycle path hợp lệ, không phải bằng chứng arbitrary webhook input an toàn. Header/signature redaction vẫn cần thiết, nhưng không thay thế strict event value schema và trusted projection.

Muốn bật retention phải chứng minh đồng thời: chỉ approved identifiers/enums/numbers được persist; raw headers, unrestricted body, workflow credentials/parameters và free-form errors bị loại **trước mọi storage write**; replay/recovery không phụ thuộc dữ liệu đã loại hoặc có replay source được xác thực từ durable Gateway; bounded size/retention; real DB/filesystem, partial/full overwrite, manual/error/retry/concurrency/restart tests. Hiện chưa có implementation đã chứng minh toàn bộ điều kiện đó. Giữ `saveDataSuccessExecution=none`, `saveDataErrorExecution=none`, `saveManualExecutions=false`, `saveExecutionProgress=false`. Clone snapshot đọc đúng4 setting này. Không có runtime patch hoặc rollout n8n mới trong subtask này.

## Historical secret / backup inventory

[private-inventory.json](private-inventory.json) là inventory read-only giới hạn của thư mục private `operator/post30218-n8n-redaction`. Key trong encrypted environment snapshot khớp MAIN environment bằng so sánh RAM boolean; không in key. Vẫn tồn tại unencrypted cold-volume tar (20,054,528 bytes) và `preserved.env` (689 bytes), bên cạnh các bản DPAPI đã dùng restore thành công. ACL hiện quan sát chỉ SYSTEM và current Windows account có inherited full control. Không đổi ACL, không xóa/ghi đè bản gốc; không tuyên bố secrets đã revoked hoặc lịch sử được scrub.

Rủi ro còn lại: key đang dùng đã từng ở legacy source; raw backups còn nhạy cảm dù ACL hạn chế; execution history/source snapshots ngoài inventory có thể chứa secrets. Chưa scan toàn bộ Git history/logs/cold archives, chưa kiểm chứng DR ngoài profile. Remediation tiếp theo phải có manifest các artifact, backup mã hóa có recovery độc lập, migration cho tất cả encrypted resources và rollback gate rồi mới cutover/revoke key và xử lý lịch sử có audit. Không xóa lịch sử nghiệp vụ để chữa lỗi.

**Đã bỏ qua:** không viết thêm abstraction/dependency hoặc dormant production patch; không đổi key, retention hay scrub MAIN vì clone migration chưa đạt. **Rủi ro cần giữ OPEN:** master-key exposure, historical plaintext backup và arbitrary-payload persistence; Human UAT và full new-key migration acceptance chưa có.
