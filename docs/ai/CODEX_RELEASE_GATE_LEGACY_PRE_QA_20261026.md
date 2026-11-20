# QLDAPM Main — release gate 2026-10-26T10:31:58.142709+07:00

**PARTIAL — chưa FULL GO.** Main Gateway `sha256:89777ef1ddf5c84f1758756bca620599fb49b906ae77cf961249bf1f2726f0fa`; Core Web `sha256:4495d944cd6ea5ab7a1fb50173310a787793f4398118f6b858333ac62a80a6a2`. Đây là runtime hiện hành; các rollout trước là lịch sử.

Dependency Native đã triển khai: proposal/hash ràng buộc scope và version, fresh authorization, Native follows/lag, atomic transaction/receipt, readback và multi-source RAG outbox. Clone thật đã kiểm tra Owner/PM, bốn role bị chặn, duplicate/cycle, derived Subtask→Task→Epic, mất reply chỉ một POST và rollback PostgreSQL sau Native save. Main đã kiểm tra read-only forms/policy; **chưa có dependency write hoặc human approval Main mới**. `depends_on` của WBS vẫn là sequencing; không tự tạo relation.

- Offline:489 Windows PASS;475 Linux PASS/14 platform skips;13 Ruby fixture programs PASS.
- Main:73 role checks,48 API contracts,13 read-only checks và24 dependency checks PASS;16workflow active/source-matched. Chỉ WF10 đổi version sang `7951e328-b410-47fb-a501-3187b98f97b8`;15workflow/8container khác giữ nguyên.
-338visible/375physical WP, #370v2 và original332 full rows giữ nguyên. ScenarioF consumed cùng61audit rows được bảo toàn, không replay.127provider receipts/132reservations/54proposals/12sync jobs giữ nguyên;28historical pending requests, không unknown mới.
- RAG373docs/1728chunks/1731points không scoped drift;3legacy points giữ/exclude. Credentials/password/TOTP/memberships bảo toàn. Automated QA375/v0 vẫn pending_qa,0human reviews. Không Staging hoặc model call mới.
- Recovery bổ sung: actual n8n online backup→isolated CLI export16workflows/decrypt4credentials và private restore2assets với exact hashes PASS. Đã bổ sung actual isolated restored n8n server: readiness200, anonymous401, workflow bodies/users/credentials/history nguyên vẹn; copied automations tắt. Chưa test restored workflow execution hoặc full cross-service DR.

Bằng chứng: [deployment](CODEX_NATIVE_DEPENDENCY_DEPLOYMENT_RESULT.json), [qualification](CODEX_NATIVE_DEPENDENCY_QUALIFICATION.json), [Main scope/roles](CODEX_NATIVE_DEPENDENCY_MAIN_RESULT.json), [final readback](CODEX_NATIVE_DEPENDENCY_FINAL_READBACK.json), [RAG](CODEX_NATIVE_DEPENDENCY_RAG_RESULT.json), [security/data](CODEX_NATIVE_DEPENDENCY_SECURITY_PRESERVATION.json), [n8n/assets recovery](CODEX_N8N_ASSETS_RECOVERY_RESULT.json).

Ma trận vẫn10business PASS/6PARTIAL. Còn human QA23→PM19, fresh exact approvals cho Main writes mới, full Bug/retest/release/child business closure, trusted physical-delete producer/recovery, hai unknown outcomes lịch sử, provenance của3legacy points và full vector restore bị policy chặn. External delivery chưa có recipient được chỉ định. Các phần quản trị AI chưa hỗ trợ vẫn NOT_IMPLEMENTED; không có UI giả hoặc auto-approval.

Rollback đúng rollout mới: Gateway về `sha256:f442384ebf72b23667032cff2bf3865016ee4f04f96fae6e5aabe7e2560ed32a`, Web về `sha256:edc9f2b23db00a25fa73acbbd3dafb1f609b17d37ea0790fde9db9778b37e8fa` và chỉ definition WF10 trước trong private `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\codex-autonomous-20261025\dependency-deployment`. Giữ mọi database/history mới; không restore DB cũ đè lên Main. Xem checkpoint để lấy manifest Main hiện hành; manifest trước rollout đã stale.

Lượt probe đầu khi tiếp tục sau khoảng gián đoạn6giờ bị401 do Bearer qualification1giờ hết hạn. Đã cấp lại bằng từng danh tính Native thật và chạy lại nguyên73checks PASS; không đổi Native credentials, TTL policy hoặc assertion.

## Tiếp tục quản trị Native và recovery — 2026-10-26T10:31:58.142709+07:00

Actual Native clone:21admin checks; extended29 bao gồm project-version create/dates/lock/close/readback và private-version ACL. Chỉ user/project test clone được tạo. Original credentials/TOTP/WP không đổi. Native tự reorder lft/rgt/updated_at của project cũ khi chèn root; exact derived changes và forest integrity đã verify. Main không có account/project write. Board API hiện hành GET404; browser route chưa qualified. Xem [kết quả](CODEX_NATIVE_ADMIN_RECOVERY_CONTINUATION_RESULT.json).

Main08:00 ngày26/10:5daily READY/5local receipts exact hash/trace;20provider-agent capability checks PASS. Mutable provider/Agent editors vẫn NOT_IMPLEMENTED.9host tests PASS cho bổ sung server restore;489Windows/475Linux+14skip/13Ruby là full baseline trước đó, không nhận là rerun toàn suite trong lượt host-only này.

Probe ban đầu bị500 do SQLite I/O tại WAL open. Synthetic cross-OS reopen tái hiện SQLITE_IOERR_SHMOPEN20/20 khi Windows reader còn mở. Đã sửa probe sang container query/online snapshot, không restart/restore Main;73roles/48contracts/13readonly và data/RAG/security hậu kiểm PASS. [Incident](CODEX_MAIN_STORAGE_IO_INCIDENT_RESULT.json) giữ nguyên failure evidence và giới hạn kết luận. Không có retry mù hoặc sửa status code để PASS.
