# Trạng thái sau Owner approval — MAIN đã đổi

Proposal30218aff đã được duyệt và áp dụng. Xem [MAIN_ROLLOUT_RESULT.md](MAIN_ROLLOUT_RESULT.md) và `rollout-20261101T110426Z/deployment-result.json`. Các đoạn NOT_DEPLOYED/AWAITING_OWNER_APPROVAL phía dưới là pre-rollout snapshot, không phải trạng thái hiện tại. Chưa human acceptance/full business E2E.

---

# Nghiệm thu candidate Phase2 — chưa triển khai MAIN

**CANDIDATE_TESTED_WITH_LIMITS / AWAITING_OWNER_APPROVAL.** Hồ sơ hiện hành: `phase2-20261101T050128Z/`. Chưa có full live acceptance hoặc Owner UAT.

| Service | Candidate | Image ID |
|---|---|---|
| gateway | `qldapm-ai:recovery-phase2-20261101-r2` | `sha256:1c10248134b4f7973685433a9686f3d841ed96e5b767dd5b7d497adc0e3eceeb` |
| core | `qldapm-core:recovery-phase2-20261101-r1` | `sha256:c237e4a792608e5ff5b95a7c9c36d41dc0392ceb3ec07f451fbee0d96dca06c9` |
| n8n | `qldapm-n8n:recovery-phase2-redacted-r2` | `sha256:9e8d3393ca28a6603f3890218aeb3bb280952262c134e230b033380a2fd54e32` |


Source qualification commit private: `27db752d686d86b9683e7e7a6b15f6a223f48939`. Có587 file theo allowlist, Git archive khớp byte từng file, bundle đã verify; một test có chuỗi giống credential được quarantine. Root repository vẫn giữ nguyên2 tracked files và không có remote. Không dùng root HEAD đại diện source untracked.

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

Một đề xuất code/integration rollout tại `phase2-20261101T050128Z/rollout-proposal.json`, SHA256 `30218aff60ff98c0c92c0858c6f0ca77c11e9f6e4b216176843069ed46de92d9`. Phạm vi:3 images, đúng host worker/delivery versions, thêm4 nodes cho WF04 và private lifecycle config. Các services phải gián đoạn khi recreate; downtime live chưa đo. Fresh backup và OFF/active0 là điều kiện bắt buộc. Xem10_DEPLOYMENT_AND_ROLLBACK.md trước khi apply.

WP385/data correction, demo18791, historical secret cleanup/rotation và fresh business E2E có provider/GitHub/Native writes cần phạm vi phê duyệt riêng. Yêu cầu duyệt production xuất phát trực tiếp từ mụcA2 của chỉ thị Owner, không phải approval bổ sung của skill.

Read-only MAIN snapshot10:47:37UTC ngày01/11: Project5=341WP/maxlock4; Project6=7WP/maxlock9;379status7/lock4;385absent; OFF/active0/provider receipts358. IDs/images serving giữ nguyên so với Phase1. Gateway/n8n/Qdrant/Ollama health200; demo health404/summary405. Không restart MAIN/worker hoặc gọi provider trong Phase2.
