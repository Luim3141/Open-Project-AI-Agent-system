> Current Main 2026-10-26T12:26:49.046792+00:00: Gatewayffe20cad/Core545e498a/WF10142d0a0d-0c12-4b6d-b1f5-c91033fc854e. Registered-only vector pruning and explicit WBS relations deployed/qualified.581Windows/566Linux+15skips;73roles/48contracts/13readonly/38hierarchy/6QAreads + unchanged canonical42 smoke PASS.1731points incl3legacy, Native/history unchanged. Full release PARTIAL; see CODEX_RAG_REGISTERED_PRUNING_FINAL_READBACK.json and CODEX_FINAL_REGRESSION_RELEASE_GATE.md. Older milestones below are historical.

CURRENT MAIN — 2026-10-26T08:04:33.762688+00:00: Gatewayb2f2db56/Coree0a840b5; trusted Native delete contract deployed with empty ledger. Fresh518Windows/503Linux+15skips/15Ruby;73roles/48contracts/13readonly/40new delete policy checks PASS.338visible/375physical/original332/#370v2/security/history preserved. No Main Native write/human decision/model call. Full release PARTIAL; read CODEX_FINAL_REGRESSION_RELEASE_GATE.md and CODEX_MAIN_CONTINUATION_CHECKPOINT.json. All sections below are historical evidence.

CURRENT MAIN WEB — 2026-10-25T03:13:28.471356+00:00: Core Web `sha256:1bbe160472068a64d3a965fe2bbbd280c2095d17ce285785a3ad0df40825a61f`, Gateway `sha256:c0f328216654478cb58dc01dad737958416882f0352c450a0ae5a80438ca6372`. Chỉ1controller file được bổ sung wbs_from_ba/QA capture/read/prepare vào route và selector theo role; Gateway cùng9container Main khác giữ nguyên ID/image/start. QA review vẫn là endpoint human review riêng, không có qa_review/qa_pass AI command.6Ruby programs PASS, gồm actual controller6roles,42valid/42wrong-role edges, ActionView/XSS và signed test receipts. Postdeploy48contracts/73roles/13read-only/Native375/oldtree/RAG/fullNative-security preservation PASS. Không thêm Native write hoặc model call. New visual selector human UAT PASS: người dùng xác nhận Owner thấy wbs_from_ba/qa_evidence_get/qa_transition_prepare và không thấy qa_evidence_capture; không chạy browser automation hoặc gửi lệnh. Evidence: CODEX_OWNER_NEW_TOOLS_HUMAN_UAT_RESULT.json. Current full release PARTIAL. Các image Core dcb60182 bên dưới là bằng chứng trước Web-only delta này.

CURRENT — 2026-10-24T22:17:45.531409+00:00: Gatewayc0f32821/Core dcb60182, Main338 (#375v0 exact approved create; old337 unchanged),433Windows/421image+12platform,48contracts/73roles/36QA/13read-only PASS. Overall PARTIAL. See CODEX_FINAL_BUSINESS_ACCEPTANCE_REPORT.md and current checkpoint. All sections below are historical unless explicitly current.

Cập nhật hiện hành 2026-10-24T14:33:05.542398+00:00: Gateway `sha256:21ad074d2b51a9332850986a1673ffc894a99d8a99707ecef1f1445996a0e724`, Core `sha256:dcb6018226280bde73fb8812e463bdcb5ef6896cbe9a1c65be7516d993f4a3d4`; Main337, original333 exact rows/#370v2 giữ nguyên. Owner supported access và actual3-level Native tree/RAG PASS; overall PARTIAL. 374Windows/367image+7Node skips;48contracts/73role/13finalread-only PASS. Xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json và CODEX_FINAL_REGRESSION_RELEASE_GATE.md trước các đoạn lịch sử bên dưới.

<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — Operations và recovery

**Status: PARTIAL.** Không restart Docker/WSL, Main Gateway/OpenProject/n8n/Qdrant hoặc Staging.

## Ollama

- Listener PID29476 đang chạy; `/api/tags` có BGE-M3; `/api/embed` trả1024 chiều (~7.07sprobe); Main Docker→host11434 trả200. `ollama ps` báo100%GPU; nvidia-smi khoảng1036MiB/4096MiB tại thời điểm probe. Không khởi động thêm daemon, pull model hoặc chạy reasoning LLM local.
- Sửa `Start-OllamaDaemon.ps1`: resolve executable theo LOCALAPPDATA; chấp nhận tags rỗng là server đang chạy; không start daemon mới nếu11434đã bị chiếm; mutex ngăn chạy đồng thời; không tự pull model khi thiếu.
- Đã đăng ký Windows task **QLDAPM-Ollama-Health**, current interactive user/RunLevelLimited, Hidden PowerShell, logon trigger + health mỗi5 phút, IgnoreNew, timeout2 phút. Script copy riêng tại `%LOCALAPPDATA%/QLDAPM/ollama-health/Start-OllamaDaemon.ps1`.
- Actual task invocation trả LastTaskResult0; PIDlistener trước/sau giữ nguyên. Task không phụ thuộc Codex/Antigravity để được scheduler gọi. **Chưa đóng terminal/app hoặc reboot để chứng minh outage recovery**. Không cam kết current manual daemon sống mãi khi terminal đóng; task có thể phục hồi ở lượt kiểm tra sau.
- Source VectorClient chia batch2(max4), nhưng chưa có global embedding semaphore và chưa có trong image Main. Không tuyên bố giới hạn concurrency toàn stack đã được bảo đảm.

Rollback task (chỉ nếu người dùng yêu cầu): disable đúng `QLDAPM-Ollama-Health`; không kill listener đang chạy hoặc xóa model. Giữ bản source-before trong snapshot.

Endpoint/model input được đối chiếu với [Ollama embed API](https://docs.ollama.com/api/embed); đặc tính Windows/GPU với [Ollama Windows](https://docs.ollama.com/windows). Khả năng phục hồi task ở trên là kết quả kiểm tra local riêng, không suy từ tài liệu hãng.

## Backup

Đã gọi SQLite backup API trong đúng Linux container đang sở hữu DB, sau đó stream snapshot binary ra private operator folder. Không mở live WAL từ Windows để backup và không dùng raw Copy-Item cho DB đang chạy.

| Backup | quick_check | Bytes |
|---|---|---|
| gateway-consistent.sqlite | ok | 3055616 |
| knowledge-consistent.sqlite | ok | 5140480 |
| n8n-consistent.sqlite | ok | 11317248 |

Hash manifest ở `consistent-backup-verification.json` riêng. ACL private snapshot chỉ LUIM/SYSTEM. `docker cp` không đọc được file trên Gateway tmpfs mặc dù file tồn tại; đã dùng `docker exec` stream file, không đổi volume/service để vượt lỗi.

`local_backup.py` hiện ghi target staging/project3. Không sửa hoặc chạy daemon đó để giả lập backup Main. Không restore vào live; chưa có full Main PostgreSQL/assets/Qdrant recovery rehearsal. Snapshot SQLite riêng không phải atomic snapshot ba service hoặc full DR proof.

## Rollout P0 đang chờ

Exact plan ở deploy preview. Trước apply: xác minh container/image/versions và candidate hashes chưa đổi, refresh backup, kiểm tra queue không running/unknown. Chặn mutation ingress trước credential changes. Native API tokens/password/TOTP và business volumes giữ nguyên. Sau deploy kiểm tra health, missing/old secret rejection, exposed token/session invalidation và BA isolation; chưa ghi test WP.

Rollback chỉ code/image; giữ token đã revoke và tắt mutation nếu chưa an toàn. Không copy đè gateway folder, không restore database cũ, không bật lại credential lộ. Root cause và operational approvals xem CODEX_01. Service health không thay thế full release acceptance.


## Durable operational reports candidate

`operational_reports` trong Gateway SQLite lưu report do server tạo, actor/project scope, Native ID/version references và SHA-256; nội dung/reference giống nhau dùng cùng report ID. WF15 API response sẽ có report_id/report_sha256 để đọc lại bằng `get_report`. Hash bị đổi thì không trả evidence; actor/project khác bị chặn; đổi vai trò hoặc mất Native visibility thì ẩn content; source set/version đổi được đánh dấu historical. Không có endpoint upload report arbitrary và không lấy report cũ làm trạng thái live. Đây là additive table riêng, không migration PostgreSQL/Native. Năm regression tests PASS; candidate chưa deploy. Rollback về Gateway image integrity `d006b57e...`, giữ bảng report/queue.


## Main online backup và isolated physical restore — 23/10/2026

Đã dùng pg_dump custom format trong MainDB (không stop/restart app), archive assets, backup privateconfiguration và native SQLite backup APIs trong đúng owningcontainer. PostgreSQL restore dùng chính image MainDB, clone duy nhất networknone/noports/noMainvolume, capdropall/read-onlyroot/512MB/1CPU; clone đã stop sau kiểm chứng. Cả220publictables khớp SHA256 của toàn bộ JSON rows đã canonical/sort, không bảng nào đổi giữa hai lần đọc bookend; WPtable khớp toàn bộ row chứ không chỉ count. Assets2files extract sang thư mục private riêng và khớp từngSHA256. Gateway21tables/Knowledge8/n8n156 đã restore file riêng, integrity_checkok và rowcounts khớp; n8nWF08active/name giữ đúng. MaincontainerID/image không đổi trong rehearsal. Không Staging.

Private manifest chứa checksum PG/assets/config/SQLite; không ghi credentials vào báo cáo public. Backup online nhất quán từngDB, chưa phải atomic snapshot xuyênPG/assets/Gateway/n8n/Qdrant; chưa boot application trên clone, chưa failover/reboot. Qdrant snapshot mới/current1712points đang được kiểm tra restore riêng; không lấy old snapshot trướcRAGrepair làm chứng minh trạng thái hiện tại. Evidence: CODEX_MAIN_DR_RESTORE_RESULT.json. Hai lỗi preflight đã dừng an toàn trước dump (POSTGRES_USER mặc định cầnpostgres; Windowscommandline quá dài nên chuyểnSQL sangstdin), không gây mutation Main.


## Qdrant native snapshot restore FAILED; logical recovery chưa chạy

Newrawsnapshot621149184bytes/SHA256c3d02d34cd36ca2ddf91e6303fbf3c849690834351c65901a6c4625b15ed47b3 tải khớpserver nhưng failrestore trong cùngimage1.20.0/Linuxvolume/networknone. GNU sparseentry0/wal/first-index chỉ có17bytehole; MainfileJSONhợp lệ. Supplement riêngmetadata vào derivedartifact không đủ:segmentversion.info cònzero hóa. Repacking sparsearchive quaPAX cũng không tương thích; các thử nghiệm chỉownclones, khôngMainvolume/ports. Không xóa/sửa/restart MainQdrant. Chưa quy kết nguyên nhânvendor/filesystem; bindmountMain đang ởWindows là observedcontext.

validate_qdrant_snapshot.py làread-onlypreflight, phát hiệninvalidWAL nhưngkhôngtựnhậnfullrestorePASS;3regressionsPASS. Logicalbackup9,457,354bytes/SHA256d483b34865c8b4a5252b36b594c88438f57ec7558d304eefc62df1f16e522c2c chứa1712pointIDs/vectors/payloads vàcollectionconfig, đãdecompress/readbackkhớp. Automatic approval review đã từ chối lệnh logicalrestorevàoisolatedcontainer, chỉtrảblockedbypolicy; lệnhchưachạy, khôngretryđườngkhácđểvượtgate. Nativearchive khôngđượccoilàbackupusable; releasegatevẫnPARTIAL. Xem CODEX_MAIN_DR_RESTORE_RESULT.json và CODEX_QDRANT_SNAPSHOT_VALIDATION.json.
