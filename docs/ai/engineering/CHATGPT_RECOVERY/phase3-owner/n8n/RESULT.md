# Phase3 n8n — kết quả có giới hạn

**SOURCE TOOLING TESTED · WF07/WF12 PARTIAL · RETENTION BLOCKED · MASTER_KEY_CUTOVER BLOCKED · OFFHOST OWNER ACTION PENDING.** Không đổi MAIN workflow, credentials, config, quyền, retention, key hoặc Project5. Không GUI, provider call, upload, history deletion hay migration mới.

## Principal/business contract

Fresh Native HTTPGET + SQLite`mode=ro` tại [principal-readback.json](principal-readback.json), command `python docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/n8n/read_principals.py`, xác nhận:

|Actor|Native login/admin|Registry và actual resolved role|Collector|
|---|---|---|---|
|18|op-owner/true|AI_SYSTEM_OWNER, exact privileged identity proof|Không thuộc5 business targets|
|19|ba-pm/true|RegistryPM, Native.identity DENIED|Target giữ nguyên, không READY giả|
|20|pm/null|RegistryBA, actualBA|READY, tên login không cấp quyềnPM|
|21/22/23|be/fe/qa, nonadmin|BE/FE/QA, registry khớp|READY|

Latest receipts daily`3f90801a-ada9-4e86-9715-e9888c446181` và weekly`4149212b-18c2-4463-937c-59f5d397db28`: COMPLETED/PARTIAL, targets5/ready4/unavailable1. Đây là receipt cũ được đọc lại, không execution mới.

Read-only n8n metadata tại [n8n-readback.json](n8n-readback.json), command `python docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/n8n/read_n8n_state.py`:16workflow có published links; WF04 đọc lại đúng successnone/errornone/manualfalse/progressfalse. Chỉ xuất approved settings metadata và graph hash, không credential hoặc execution body. Publication count không phải16businessE2EPASS.

Source collector định nghĩa mọi configured business user, loại AI_SYSTEM_OWNER; scheduled workflow gửi machine kind, không chọn actor19 thành Owner. Guard Native chỉ cấp owner exception cho18/loginop-owner/statusactive/project5or6 cộng server capability. Evidence không hỗ trợ đổi19→18 hoặc19→20: sẽ đổi recipient/role, làm mất PM target hoặc trùngBA, và không còn all5 contract. Không có wrong-token bằng chứng để sửa credential. Đề xuất giữ DENIED/PARTIAL; nếu Owner muốn19 là businessPM thì cần account policy rõ về global-admin status hoặc một PM principal nonadmin có membership/credential thật. Thay quyền global/identity không nằm trong repair mapping an toàn hiện đã chứng minh, nên không mutate. Không giảm target count hoặc replay existing idempotency receipts.

4 offline tests mới kiểm tra actual Native.identity và daily/weekly collectors:19admin bị deny trước membership lookup;20loginpm vẫnBA; cả hai collectors giữ19–23/all5 và19DENIED/othersREADY. Không giả claim Native live bằng mocks.

## Retention canary mới: real filesystem boundary

[persistence_filesystem_canary.js](persistence_filesystem_canary.js) dùng actual pinned-image `ExecutionPersistence`, `ExecutionDataJsonStore`, `FsByteStore`. Dữ liệu synthetic ghi/đọc file qua OS trong tmpfs của clone networknone/rootread-only, không MAIN mount. Chỉ execution-entity transaction được stub. Sáu routes: successcreate, errorcreate, retrycreate, fulloverwrite, partialdata, partialworkflow. Mỗi route: header marker bị redact, arbitrarynested và free-text marker còn trong bytes thật. `EXPECTED_BLOCKER_REPRODUCED_NOT_SECURITY_PASS` là kết quả đúng, không securityPASS. Retrycreate là persistence của retry record, không server retry E2E; metadata-only retry compatibility fail Phase2 vẫn áp dụng. Không thêm generic regex hoặc metadata-only patch đã biết phá retry.

Đây mở rộng Phase2 storage stubs bằng vendor file stores thật, không chứng minh physical-disk/restart/concurrency hoặc fullDB/serverexecution. Bởi6 routes còn leak, không tiếp tục experiments không cần thiết và không bật retention. WF04 vẫn giữ successnone/errornone/manualfalse/progressfalse; Gateway durable observations là trace fallback hiện hành.

Lượt harness đầu lỗi synthetic `executionData.nodeExecutionStack[].data` sai connection shape; sửa fixture về `main:[[json]]`, không đổi vendor code. Kết quả cuối có source hashes/UTC/command trong [checks.json](checks.json). Generic transient persistence không thể được bảo vệ đầy đủ bằng projection node chạy sau initial write; một fix được deploy phải bao phủ storage boundary và retry/recovery contract trước khi cho retentionON.

## DR improvement đã kiểm tra

[verify_ciphertext_copy.py](verify_ciphertext_copy.py) là read-only, ciphertext-only checker cho đúng3files của portable kit. Pins lấy từ Phase2 ciphertext/verifier evidence và read-only FORMAT.json hash; không tin manifest từ destination. Không mở key, không decrypt/execute/copy/upload. Fail closed: unexpectedkey/file, missingfile, directory-instead-of-file, oversizedfile, symlink/reparse, tamper. Unit suite11tests:10PASS,1SKIP do Windows thiếu symlink privilege; Windows reparse branch có mock test riêng PASS. Exact original local ciphertext directory đã byte-check đạt; chưa kiểm tra off-host destination vì Owner chưa chọn/copy.

Hướng dẫn [OFFHOST_OWNER_PROCEDURE.md](OFFHOST_OWNER_PROCEDURE.md) tách Owner custody, destination permission attestation và physical-machine restore gate; không giả địa chỉ upload, không yêu cầu key vào chat/args/env. Phase2 wrapper chỉ nhận exact local operator parent; checker mới cho phép verify một ciphertext copy bất kỳ bằng pins tin cậy mà không chạm key. Không tuyên bố tooling này hoàn tất physical-machine DR hoặc cold snapshot đã cập nhật MAIN hiện tại.

## Provenance và lệnh kiểm tra

```powershell
python docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/n8n/record_evidence.py
```

[checks.json](checks.json) ghi3bounded commands, UTC từng command, exact per-file source SHA256, Python3.14.3 và n8n image pin. Principal readback ghi cả Gateway/Core/n8n images và collector/native source hashes. Default Docker pipe ban đầu unavailable; root khởi động Docker Desktop qua CLI, sau readiness read-only probe và isolated tests mới chạy. Không che failed attempt bằng source-only success.

Master-key migration không lặp lại capability-failed Phase2 experiments. [Phase2 assessment](../../phase2-final/n8n/FRESH_INSTALL_MIGRATION_ASSESSMENT.md) vẫn là blocker: persisted DEK wrappers và signing/auth resources chưa có vendor-supported full-instance re-encryption/metadata migration đã kiểm chứng. Không thay MAIN N8N_ENCRYPTION_KEY.

Bỏ qua: không đổi principals/RBAC, không retention patch hoặc migration mới khi security/retry gates chưa đạt; không đoán storage off-host.
Rủi ro còn mở: old exposed master key, historical sensitive backups, arbitrary-payload filesystem persistence, physical-machine restore/custody và OWNER UAT chưa đạt.
