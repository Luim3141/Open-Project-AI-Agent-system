<!-- FINAL_DEMO_CURRENT -->
# Final Demo Owner disposition — 2026-11-02T21:53:26.525639+00:00

`MASTER_KEY_ROTATION = DEFERRED_BY_OWNER_FOR_LOCAL_DEMO`. Không đổi instance masterkey và không nhầm data-encryption-keyrotation thành masterkeyrotation. `CURRENT_CREDENTIAL_FUNCTIONALITY = VERIFIED` ở phạm vi4/4decrypt, retained4credentials/usersunchanged vàactualworkflows auth/business. Existingkey cần để restore, chỉ lưu trongprivateencryptedkit/custody.

Historical execution secrets/legacy source/enterprisehardening = PRODUCTION_HARDENING_DEFERRED, không phải PASS và chưa được clean triệt để. WF04 mới chỉ minimalcanonicalevent/ACK, persistenceprojection chặnnestedarbitrarypayload; giữgenericredactor vàauthredaction. Cloneactualsuccess/error/retry/restart/nested +6storagepaths; không khẳng địnhmọiworkflowsecret đã loại bỏ.

Providerprivateendpoint córoot-sharedtoken+claimbinding; noBrowserAuthorization/Origin/query; cap/lease/mode enforced; settlementafterOFF chỉghiusageknownreservation, không phátrequest. No model fallback, key/quota bypass hoặc paid service. Private portablearchive vàrecoverykey hai thưmụctách trêncùngmáy chưa phảioffhostcustody. Owner cầncopyriêng tư; physicalDR chưa thử.
<!-- END_FINAL_DEMO_CURRENT -->

# Security và credential — post-30218aff

- n8n 2.43.6 trước hotfix có nhánh full-overwrite bypass hook redaction. Clone với retention bật đã tái hiện canary ở execution data; candidate `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795` đã được deploy MAIN, cold volume backup và container cũ được giữ. Clone SQLite: 3 success, 1 error, không thấy canary trong execution tables/log; review độc lập không thấy blocker Critical/High. Filesystem persistence mới được thử qua fixture.
- Redaction mới chỉ bao phủ header và định dạng Bearer/Basic đã thiết kế, không bảo đảm loại mọi bí mật nằm tự do trong payload. Nó không xóa dữ liệu lịch sử; WF04 success/error retention vẫn tắt. Scan thực tế sau rollout trước đó chỉ quan sát hai workflow phát sinh execution, không đại diện toàn bộ 16 workflow.

Canary độc lập trong image n8n hiện hành xác nhận marker synthetic ở nested field và free text vẫn lọt qua redactor (`stabilization-n8n/WF04_ARBITRARY_PAYLOAD_CANARY.md`). Đây là thử trực tiếp redactor, chưa phải toàn bộ persistence; kết quả đủ để tiếp tục giữ WF04 retention OFF, không tuyên bố an toàn cho arbitrary payload.
- Encryption key hiện hành từng có trong script legacy và còn trong source snapshot cũ. Đã loại literal khỏi script workspace và cho script fail closed trước khi có thể recreate image cũ hoặc prune; bản gốc được sao lưu bằng Windows DPAPI CurrentUser và kiểm tra giải mã khớp. Cold n8n volume tar và environment snapshot có bản DPAPI đã kiểm tra decrypt byte-for-byte; bản không mã hóa trước đó vẫn tồn tại. Clone network-none, tmpfs đã restore tar kèm WAL/SHM, SQLite integrity `ok`, 16 active workflows/16 published versions/16 liên kết sharing hợp lệ, 1 owner và CLI giải mã 4/4 credential. Đây là restore cùng Windows profile; chưa kiểm tra đầy đủ ownership, webhook/restart hay disaster recovery trên tài khoản/máy khác. Không công bố source snapshot cũ. Chưa xoay key, chưa scrub lịch sử và chưa chứng minh credential vẫn giải mã sau rotation. Không coi vấn đề này là đã xử lý.
- Không ghi token hoặc key vào báo cáo. Cần quy trình key rotation được vendor hỗ trợ, thử clone với credential thật và encrypted backup có thể khôi phục trước khi áp dụng; bảo toàn dữ liệu, không xóa lịch sử để che lỗi.

n8n hiện mô tả [data encryption key rotation](https://docs.n8n.io/deploy/host-n8n/configure-n8n/security/rotate-encryption-keys.md) cho self-hosted, có feature flag trên 2.x và yêu cầu staging/full backup. Tuy nhiên tính năng này **không đổi instance master key** (`N8N_ENCRYPTION_KEY`); bản thân nó không khắc phục việc master key cũ đã lộ trong source. Không bật flag chỉ để tuyên bố rủi ro master key đã được xử lý.

Thử export/import credentials dưới master key mới chỉ trong clone tmpfs: import báo 4 và 4 ciphertext thay đổi, nhưng export giải mã lại thất bại với lỗi liên quan decrypt. **Master-key cutover BLOCKED**, chưa xác định chính xác cơ chế lỗi; không áp dụng phép thử này lên MAIN. Xem `stabilization-n8n/migration-result-ciphertext.json` và `RESULT.md`.

Evidence: `post30218-n8n-overwrite-20261101/n8n-clone-result.json`, `post30218-20261101T1540Z/n8n-redaction-deployment.json`, `post30218-20261101T1540Z/n8n-main-exposure-scan.json`.

Command Center Inspector trước đây đưa output/event và toast chưa tin cậy vào innerHTML. Đã escape các trường động và giới hạn toast class trong Core `00f1e372…`; Node VM test payload HTML và Rails ERB compile PASS, clone Native API PASS. Chưa thực hiện browser/human UAT. WF04 payload tùy ý và lịch sử secret vẫn là rủi ro riêng, retention vẫn OFF.

## Phase2-final security evidence

Exact n8n2.43.6 source/clone diagnostic confirms2persisted deployment DEKs unwrap with old master2/2 and new master0/2. Reimported4credential ciphertexts directly decrypt with new instance key, but vendor decryptV2 resolves the legacy persisted DEK and fails. Import count/ciphertext change is not a migration. Old-key encrypted restore integrity/decrypt4/4, published/sharing16/16 and2server starts passed; new-key business ACK/full migration and DR across profile/machine remain unproved. MASTER_KEY_CUTOVER_BLOCKED; MAIN key unchanged.

Arbitrary nested/free-text canary still leaks through generic redactor. Metadata-only storage loses executionData and vendor retry aborts; no unsafe retention patch deployed. WF04 retentionOFF; Gateway observations provide limited durable lifecycle visibility. Sensitive raw historical backup/source copies remain with restricted local ACL; DPAPI CurrentUser is not portable DR. See `phase2-final/n8n/RESULT.md` and `private-inventory.json`; no plaintext credential/key in reports.

Engineering publication now checks claim identity at Gateway transactions and knowledge/vector writes, with a single host process holding the shared runtime lock through cleanup. Independent review2Important issues were fixed/tested before deploy (`phase2-final/REVIEW.md`). Requests already sent to external systems remain a reconciliation concern, never a reason to replay unknown POST.

## Portable recovery mitigation — independently verified

Bộ AES-256-GCM nằm ngoài repo tại private operator `portable-n8n-recovery-8a61c9795ada`; recovery key 32 bytes ở thư mục riêng, ACL chỉ current user và SYSTEM. Ciphertext SHA256 `47cab825e5e23a130bcbba298c0b1cbe344375d21c28753a74a3797fddcd4155`. Đã giải mã/restore từ Linux network-none tmpfs không dùng DPAPI: integrity ok, credentials 4/4, published/sharing 16/16; ciphertext sửa đổi, sai key và sai AAD đều bị từ chối. Root đã chạy lại độc lập `--verify`; xem `phase2-final/n8n/portable-root-verify.json`.

Đây là kit của cold snapshot hiện có, không phải snapshot mới của mọi service. Chưa có off-host copy, Owner custody riêng hoặc physical-machine DR. Raw backups gốc vẫn được giữ. Không coi việc tạo kit là revoke master key cũ hoặc scrub lịch sử.

Actual n8n 2.43.6 export/import entities không có supported table exclusion cho deployment keys; --keyFile chỉ mã hóa outer export envelope, không chuyển inner ciphertext. Snapshot có 8 deployment-key rows và nhiều loại signing resources. Fresh-install migration được chặn trước khi ghi DB mới thay vì thử xóa/rewrap tùy tiện. Xem FRESH_INSTALL_MIGRATION_ASSESSMENT.md và encrypted-resource-inventory.json. MAIN key/retention/history không thay đổi.

## Phase3 — no unsafe cutover; durable owner command safety

Owner control endpoint keeps authenticated Rails session/CSRF and exact Owner18 mapping; invalidCSRF denied before Gateway in actual Rails clone. Clone password/TOTP/settings were synthetic and disposable, MAIN MFA unchanged. Signed Rails→Gateway MAIN calls preserve NativeOwner authorization; no browser bearer or wider RBAC added. New durable owner6 request namespace binds actor/project/action/arguments; unknown external outcomes not replayed. Telemetry projects bounded IDs/codes/artifact hashes, no raw private prompts/auth headers.

N8n arbitrary nested/free-text leakage reproduced on actual vendor file stores across6routes; no retention enablement or claim new leakage fixed globally. Master-key wrapper/vendor migration blocker unchanged; no key rotation/rewrap/decrypt on MAIN. WF07/12admin19deny is designed, requires Owner account decision outside Project5read-only mandate. Ciphertext-only offhost verifier reads only3pinnedfiles, rejects extra key files/tamper/reparse. No offhost copy or key custody performed. Existing sensitive backups kept private, not deleted/publicized. Evidence phase3-owner/n8n/RESULT.md and OFFHOST_OWNER_PROCEDURE.md.
