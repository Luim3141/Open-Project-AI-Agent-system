"""Concise Vietnamese handoff; all figures are read from verified artifacts."""
from pathlib import Path
import hashlib,json
RUN=Path(__file__).parent;DOC=RUN.parent
m=json.loads((RUN/'source-candidate-final-manifest.json').read_text())
proposal_hash=hashlib.sha256((RUN/'rollout-proposal.json').read_bytes()).hexdigest()
images=m['images'];commit=m['qualification_source_commit']
table='| Service | Candidate | Image ID |\n|---|---|---|\n'+''.join(f"| {k} | `{v['tag']}` | `{v['id']}` |\n" for k,v in images.items())
(DOC/'FINAL_PRE_ROLLOUT_ACCEPTANCE.md').write_text(f'''# Nghiệm thu candidate Phase2 — chưa triển khai MAIN

**CANDIDATE_TESTED_WITH_LIMITS / AWAITING_OWNER_APPROVAL.** Hồ sơ hiện hành: `{RUN.name}/`. Chưa có full live acceptance hoặc Owner UAT.

{table}

Source qualification commit private: `{commit}`. Có587 file theo allowlist, Git archive khớp byte từng file, bundle đã verify; một test có chuỗi giống credential được quarantine. Root repository vẫn giữ nguyên2 tracked files và không có remote. Không dùng root HEAD đại diện source untracked.

Images được build từ snapshot307503c; commit qualification mới chỉ thay host delivery/adapter/tests/architecture và bảo toàn byte Git. Toàn bộ15 file đóng gói vẫn khớp host/snapshot/image. Exact worker/adapter hashes và changed-file list nằm trong `source-candidate-final-manifest.json` / `changed-source-files.json`; diff đối chiếu r24 và host snapshots là `recovery-final.patch`.

| Milestone | Bằng chứng và giới hạn |
|---|---|
| M1 — Source/restore | Private Git/bundle, Docker build, restore221 bảng PostgreSQL và2 SQLite đạt. |
| M2 — n8n | Gateway ASGI thật và Service background publisher → WF04 → signed observation → ACK đạt trên clone. Canary success/error/CLI không còn trong execution storage/log. MAIN chưa cập nhật. |
| M3 — GitHub |10 journal tests dùng Native HTTP localhost thật: crash, lost response, pagination, concurrent1POST và unknown no-replay đạt. Chưa ghi GitHub/Native thật. |
| M4 — Integrity | Proposal WP thay thế được tạo/read-back trên clone qua Native API; quan hệ follows384 đúng. Original385 chưa được phục hồi; correction MAIN chờ duyệt. |
| M5 — Reports/RAG | Reader/controller contracts đạt. Corpus135 vector points: exact term/ACL/fallback/index-delete đạt;2 truy vấn semantic VN/EN chưa đạt. UI chờ Owner. |
| M6 — Worker |7 full DeliveryJournal tests với Store/lifecycle thật, external fixtures;2 tests dùng child process thật. Rework/resume/unknown/treefence và giữ original diff đạt. Chưa có phiên OpenClaw/provider thật mới. |
| M7 — Demo | Exact commit0498ceed:15 pytest tests và actual HTTP temporary server đạt. Live18791 chưa thay. |
| M8 — Qualification |182 Linux affected tests, Ruby syntax/ERB/controller/JS,15 file parity, Compose preview và candidate startup đạt; Core/Gateway rollback startup đạt. Chưa traffic cutover. |
| M9 — MAIN/UAT | Chưa chạy; cần Owner approval. |

182 là tổng suite cuối, **đã bao gồm130 tests baseline**. Không cộng thành312. Logs RED, lỗi fixture và các lần chạy trước được giữ riêng; không tính thành PASS. n8n manual đã thử bằng CLI; editor/browser/manual UI vẫn **PENDING OWNER MANUAL UAT**.

RAG còn open P1: WP384 cosine tối đa0.569523 cho VN và0.512619 cho EN; query không liên quan về backup có score0.520300. Hạ threshold0.65 chỉ để đạt hai positive fixtures có thể tăng false positives. Giữ policy và ghi đúng recall gap; cần corpus gán nhãn rộng hơn trước khi đổi threshold/model/chunking. Actor19 vẫn DENIED vì admin=true; guard không bị hạ.

Một đề xuất code/integration rollout tại `{RUN.name}/rollout-proposal.json`, SHA256 `{proposal_hash}`. Phạm vi:3 images, đúng host worker/delivery versions, thêm4 nodes cho WF04 và private lifecycle config. Các services phải gián đoạn khi recreate; downtime live chưa đo. Fresh backup và OFF/active0 là điều kiện bắt buộc. Xem10_DEPLOYMENT_AND_ROLLBACK.md trước khi apply.

WP385/data correction, demo18791, historical secret cleanup/rotation và fresh business E2E có provider/GitHub/Native writes cần phạm vi phê duyệt riêng. Yêu cầu duyệt production xuất phát trực tiếp từ mụcA2 của chỉ thị Owner, không phải approval bổ sung của skill.

Read-only MAIN snapshot10:47:37UTC ngày01/11: Project5=341WP/maxlock4; Project6=7WP/maxlock9;379status7/lock4;385absent; OFF/active0/provider receipts358. IDs/images serving giữ nguyên so với Phase1. Gateway/n8n/Qdrant/Ollama health200; demo health404/summary405. Không restart MAIN/worker hoặc gọi provider trong Phase2.
''',encoding='utf-8')
(DOC/'12_CONTINUATION_HANDOFF.md').write_text(f'''# Bàn giao continuation Phase2

**Đã hoàn tất batch sửa source và kiểm thử candidate; chưa rollout MAIN.** Evidence nằm trong `{RUN.name}/`; qualification commit private `{commit}`. Đọc FINAL_PRE_ROLLOUT_ACCEPTANCE.md và09_TEST_EXECUTION_RESULTS.json để phân biệt kết quả từng scope.

Đã sửa durable GitHub journal; transactional n8n outbox và signed observation; n8n storage redaction; Report Reader/controller; projection phát hiện verdict mâu thuẫn; UI hardcoded claims/lock fallback; worker resume sau rework và bảo toàn original reviewed diff. Architecture và callers/tests tương ứng đã cập nhật.

Kiểm chứng cuối:182 Linux affected tests, Ruby/ERB/controller/Node contracts,15 file image parity; actual Gateway ASGI→n8n ACK/canary; restore221 PG tables+2 SQLite; candidate và rollback startup. Native clone đã tạo WP thay thế mới/read-back/dependency, không ghi MAIN. Demo commit0498ceed đạt15tests và actual HTTP với clone SQLite; live18791 giữ nguyên.

587 source files được version trong private local Git, archive khớp byte và bundle verify; private runtime base archive hỗ trợ rebuild. Root repository/remote không đổi. Các dump tạm do Native harness tạo trong evidence đã được chuyển sang private operator directory, script đã sửa và kiểm tra workspace không còn DB artifact của run. Không DB/env/credential nào nằm trong source bundle.

Còn giới hạn: semantic recall VN/EN của RAG; actor19 admin bị DENIED đúng guard; chưa fresh OpenClaw/provider execution; UI/editor/manual UAT chưa thực hiện; MAIN n8n history còn secret retention cũ. WP385 original/history không được khôi phục, audited correction và replacement MAIN chưa áp dụng.

Bước tiếp theo là Owner xem và duyệt một code/integration rollout proposal SHA256 `{proposal_hash}` theo10_DEPLOYMENT_AND_ROLLBACK.md. Proposal chỉ gồm3 services, idle worker, targeted WF04/private config; không mặc nhiên bao gồm demo/data repair/provider business E2E. Sau duyệt phải chụp backup mới và kiểm lại exact images/source/active workflow version/OFF/queue0 trước apply.

Read-back cuối: serving r24 không đổi ID/image; Project5=341/maxlock4,379status7/lock4,OFF/active0,provider receipts358. CURRENT_RUN.txt trỏ Phase2. Không replay jobs hoặc chạy lại các script lịch sử chỉ vì tiêu đề COMPLETE/PASS cũ.
''',encoding='utf-8')
review=DOC/'REVIEW.md'
review.write_text('''# Independent review Phase2 — hiện hành

Reviewer độc lập đọc journal/outbox/routes/n8n persistence và full delivery resume. Findings đã tái hiện và sửa: header name/value + Basic redaction gap; ACK timeout không bao trùm headers/body; resume sau rework lấy stale review; partial resume ghi đè original reviewed diff. RED/GREEN và re-review lưu trong runPhase2.

Kết quả cuối: outbox8/8 và delivery7/7 được reviewer chạy độc lập; journal10/10 đã kiểm trước đó. Root chạy182 affected Linux tests và các candidate/clone checks sau các thay đổi cuối. Không còn finding Medium/High đã biết trong phạm vi review này. Đây không phải live OpenClaw/provider hoặc Owner acceptance; RAG semantic gap và các production boundaries được ghi riêng.

---

'''+review.read_text(encoding='utf-8'),encoding='utf-8')
backup=DOC/'BACKUP_RESTORE_DRILL.md'
backup.write_text(backup.read_text(encoding='utf-8')+'\nArtifact hygiene:9 file Native clone tạm (gồm dump) đã được chuyển khỏi workspace sang private operator root; manifest chỉ lưu path/hash/size ở private-native-artifacts.json. Không có DB file trong source Git bundle. native_recovery_drill.py hiện luôn đặt clone output ở private root.\n',encoding='utf-8')
print('Vietnamese handoff and review updated; production unchanged')
