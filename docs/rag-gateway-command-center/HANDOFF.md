# Handoff — Phase 4

Source commits **`77176e5` + `854364d`**, branch `codex/agent-studio-v2-stabilization`; baseline `f3b713a`. Tổng scope gồm11product files,4test files và architecture/checkpoint. Một số modules đã tồn tại ở trạng thái untracked trước phase này; số file Git thêm mới không phải số chức năng được viết lại.

Đã triển khai Gateway `26bfcdbef5d2`, Core `113472c4ec1d`, Bot `828cfb8a73dc`; source/image parity được kiểm trong `final-integrity.json`. Có follow-up source commit cho read-only file transport và bắt buộc đọc mới trước khi trả lời tài liệu. Không push. Evidence/docs được lưu trên cùng branch; xem `git log`.

Lượt thật cuối: Web trả lời có trích dẫn/source pin readback; Owner Telegram41→42 có freshRAG trước model, sourcechecksum đầy đủ và trả lời đúng rằng fixture không chứng nhận Owner acceptance. Lượt39→40 lộ memoryreuse khôngfreshsource đã được giữ làm failure proof rồi sửa. Bản cuối67Bot testsPASS. Bucket20769 giữ20; UTC20770 tự nhiên dùng2/20, không reset cap/thay model.

466 Gateway tests chạy,22skip (444passed);67Bot testsPASS. Gold40,36retrieval thật:25/36, holdout19/28, không phải40Geminianswers. Negative503 đầu được giữ, sauproviderrecovery explicitquery mới actualABSTAIN/exactmodelPASS. FinalCorefile-read503/network không khóaUNKNOWN_WRITE, giữ pending/unknownwritekhác; NodeRED→GREEN và finalMAINvisiblefileUI/readPASS. RAG/Command Center/system **PARTIAL**, không FULL PASS.

Task398v10 chờ Owner, catalog14, PR15OPEN, SupervisorOFF/idle, n8n/pairing/outbox/gates giữ nguyên. Old620provider receipts bất biến;8receipts mới thuộc RAG actor18/runNone. Không newTask/run/replay/approval/merge/productPRdeployment/reindex/DBrestore.

Private rollback snapshots/manifests do guarded operator quản lý. Chỉ rollback image; không restore DB cũ hoặc xóa lịch sử/quota. Candidate contexts/private manifests/DB/cookies/cache/credentials không được stage. Kiểm bí mật dùng credential thật local, chỉ lưu số lượng và kết quả; không in giá trị.

Điểm bắt đầu cho lần sau: [Remaining issues](REMAINING_ISSUES.md), [Final report](FINAL_REPORT.md), [Evaluation](RAG_EVALUATION.md). Post-footer đã kiểm live, không inference lại chỉ để đọc tiến độ. Semantic recall/answer breadth còn PARTIAL; các mutation MAIN vẫn cần đúng quyền/preview riêng.
