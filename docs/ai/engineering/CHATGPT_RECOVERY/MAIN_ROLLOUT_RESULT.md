# MAIN rollout 30218aff — đã áp dụng và xác minh

Trạng thái: **DEPLOYED_TO_MAIN_READ_SMOKE_VERIFIED_WITH_LIMITS**. Owner đã duyệt proposal SHA256 `30218aff60ff98c0c92c0858c6f0ca77c11e9f6e4b216176843069ed46de92d9`. Evidence: `rollout-20261101T110426Z/deployment-result.json`; thời điểm chốt `2026-11-01T14:58:00.485036+00:00`. Không coi approval triển khai là Owner UAT acceptance.

| Service | Serving image ID |
|---|---|
| gateway | `sha256:1c10248134b4f7973685433a9686f3d841ed96e5b767dd5b7d497adc0e3eceeb` |
| core | `sha256:c237e4a792608e5ff5b95a7c9c36d41dc0392ceb3ec07f451fbee0d96dca06c9` |
| n8n | `sha256:9e8d3393ca28a6603f3890218aeb3bb280952262c134e230b033380a2fd54e32` |


Đã thay đúng Gateway/Core/n8n và restart task QLDAPMEngineeringDelivery khi idle.15 file runtime khớp candidate hashes. AI_IMAGE, Core bridge image và image-lock được pin để Compose sau này giữ đúng version. Config chỉ thêm n8n_lifecycle với signing key private; provider/model/quota/Native credentials/TOTP/UI key không đổi. Worker mới có một process tree, heartbeat mới, run_id=null; engineering OFF, queue active0, provider receipts358.

WF04 `elfapV5D2PTnLiHW` đã publish version `b79f33b6-97d1-4340-b844-32b1cc2d030c`,8 nodes:4 cũ giữ nguyên và4 lifecycle adapter mới.16 workflows active;15 workflow còn lại không đổi graph/settings/version. Owner, encrypted credentials và sharing được đối chiếu giữ nguyên. Container n8n cũ được giữ stopped tại `qldapm-n8n-main-pre-30218aff-20261101T110426Z` để rollback, không xóa volume.

Kiểm tra dữ liệu: Project5=341WP/maxlock4, Project6=7WP/maxlock9;379status7/lock4;385absent;386status1/lock2. Full WorkPackage/relation rows, Native users/security/roles/membership/tokens/TOTP được đối chiếu với fresh backup theo các cột trong evidence.9 bảng history Gateway không thay đổi, gồm raw verdict cũ và Native request receipts. Không sửa verdict lịch sử hoặc replay unknown outcome.

Read smoke dùng Native identity/permission guards: Owner18 và PM20 đọc reports list/detail; sample IDs khớp và narrative nonempty,22reports hiện hữu. Owner RAG healthz truy xuất WP384. Actor19 vẫn DENIED đúng guard. Đây là Service read checks trên serving runtime, không phải browser/Owner UI UAT.

Live n8n negative canary execution `2886`: chữ ký sai → callback403/webhook500 đúng dự kiến; không admit AI run/outbox/observation hoặc ghi nghiệp vụ Native. Canary không xuất hiện trong execution storage/daemon log. Theo policy saveDataErrorExecution=none, bản ghi được tombstone/cleanup; cột status thô có thể còn running nhưng deletedAt khác null, không phải active execution. Test đầu đọc raw status chưa lọc tombstone đã được sửa; không sửa production status bằng SQL. Chưa thử positive ACK cho một business lifecycle event MAIN mới.

18 container ngoài phạm vi giữ nguyên ID/image. Stage quick tunnel có StartedAt thay đổi trong khoảng quan sát và RestartCount2; không có lệnh rollout nào nhắm tới container đó. Không khẳng định toàn bộ StartedAt ngoài phạm vi giữ nguyên. Gateway/Core healthy, n8n readiness200; worker idle. Demo18791 vẫn release cũ, health404/summary405; chưa deploy demo.

Fresh backup private: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\approved-rollout-20261101T110426Z` gồm PG/Gateway/knowledge/n8n/assets/config và cold n8n volume archive. Candidate đã giải mã credentials của fresh n8n backup trên clone; isolated restore/startup/rollback qualification của Phase2 vẫn được giữ. Hai khác biệt Docker default Dns=[]/null và OomKillDisable=null/false được ghi trong ledger, không thay policy.

**Source packaging correction:** phát hiện một legacy script chứa encryption key n8n hiện hữu; regex scan cũ bỏ sót literal hex. Snapshot/bundle27db được giữ private và đánh dấu sensitive, không được publish. Gói sạch mới `093b4194a8215f230f7417765ecb76f59c66f2e5` có586 source files, loại file credential-bearing; không đổi code đã triển khai hay rewrite shared history. Dùng clean bundle được ghi trong source-packaging-security-correction.json cho handoff/export. Key hiện hữu không được xoay trong approval này.

Còn giới hạn: semantic RAG VN/EN; actor19 admin guard; historical n8n secrets/rotation; WP385 replacement/audited correction; demo18791; fresh OpenClaw/provider/Native/GitHub business E2E; UI **PENDING OWNER MANUAL UAT**. Không Computer Use, không provider call mới do rollout, không xóa lịch sử/WP hoặc restore DB cũ lên MAIN.
