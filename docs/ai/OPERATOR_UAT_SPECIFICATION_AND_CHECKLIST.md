> Automation engineering đã cập nhật29/10: [report](CODEX_AUTOMATION_STABILITY_20261029_RESULT.md). WF07 thêmbusiness-final guard, published/readbackPASS;9clonecyclesmỗiWF07/WF12/WF16 vàcontrolledrestarts/recoveryđãtest. UserDockerrestartcóMainrecoveryproofriêng. Humancheckbox/sign-offvẫnpending; realcontinuouscloneGemini/physicalreboot/fullDRchưaqualify. KhôngmanualtriggerMAINđểthayproofschedule.

> Browser acceptance mới29/10: [evidence và21gate](CODEX_FINAL_STABILIZATION_20261029.json). Owner đã được automation kiểm tra Assistant/count57/search/citation/livePM+Reviewer/Monitor/QA pending/WBS draft/permissions/freshness/n8n UI. Những checkbox và chữ ký bên dưới vẫn dành cho con người; không suy ra fresh5role/provider-outage/login/reboot PASS. Hai host tasks đã sửa battery flags, không thay product images hoặc workflow definitions.

# Operator UAT — QLDAPM MAIN, bản hiện hành 28/10/2026

Trạng thái **PENDING_OPERATOR_SIGN_OFF**. Readiness kỹ thuật **READY_FOR_OPERATOR_UAT** có giới hạn; các checkbox dưới đây chưa được con người xác nhận. Kết quả automation và clone không là human approval.

Nguồn hiện hành: [Kết quả engineering](CODEX_TAKEOVER_20261028_RESULT.md), [evidence đã lọc](CODEX_TAKEOVER_20261028_EVIDENCE.json), [operator guide](CODEX_FULL_PROJECT_OPERATOR_GUIDE.md). Bản checklist này thay thế các kỳ vọng cache counts, execution IDs, nguồn file và hướng dẫn DR cũ không còn đúng.

## Tiền điều kiện

MAIN Project5 `qldapm-local`: Core18088, Gateway18089, n8n5679, Qdrant6333, Ollama11434; tất cả127.0.0.1. Dùng tài khoản của chính người kiểm tra. Không đồng nhất admin với PM19; actual Native identity mới quyết định quyền. Không gửi password/TOTP/token qua chat.

Preflight đã chạy PASS lúc23:38 ICT; để lấy snapshot mới, từ repo root:

```powershell
$env:PYTHONPATH='openproject/ai'
& 'openproject/ai/.venv/Scripts/python.exe' -m automation.operator_uat_preflight
```

Script đọc live SQLite trong container sở hữu, kiểm tra registered provenance thay vì hardcode document/point counts, xét PM token expiry, exact legacy IDs và published workflow. Preflight không là business E2E, human UAT, physical reboot hoặc fullDR. Protected-record checks phản ánh baseline tiếp quản; nếu sau này có thay đổi nghiệp vụ hợp lệ, operator phải review baseline chứ không sửa DB để có PASS.

## 14 kịch bản của người vận hành

MAIN chỉ đọc. Các thao tác approval/rejection/QA transition/delete, fault injection và permission revoke đã được automation kiểm thử trong clone riêng. Không bấm approve một đề xuất/evidence thật để chạy checklist này; nếu muốn nghiệm thu tương tác ghi, dùng clone được cấu hình riêng và ghi rõ fixture, không dùng session/token MAIN.

| # | Thực hiện | Kỳ vọng / bằng chứng ghi lại | Operator |
|---|---|---|---|
|01|Đăng nhập MAIN18088, chọn Project5|Đúng identity/role/project; snapshot hiện hành339visible; số lượng có thể đổi sau legitimate business change|[ ] PASS [ ] FAIL [ ] BLOCKED|
|02|Mở Assistant, gửi yêu cầu phân tích chỉ đọc về376|Render câu trả lời/links/error/loading phù hợp; ghi run_id; không tạo Native write|[ ] PASS [ ] FAIL [ ] BLOCKED|
|03|Gửi “Hiện tại có bao nhiêu công việc loại Task chưa hoàn thành? Chỉ đọc số liệu, không tạo đề xuất.”|Snapshot57Task, model0; đối chiếu Native filter hiện hành. Hỏi tổngWP riêng để tránh câu ghép chưa qualify|[ ] PASS [ ] FAIL [ ] BLOCKED|
|04|Second Brain search test2|Nguồn376, test2, Subtask/parent49, v0NEW, citation đúng; không giả định search là unique exact match|[ ] PASS [ ] FAIL [ ] BLOCKED|
|05|Xem một run model có RAG đã lưu, ví dụ17054b69…|PM+Reviewer, document/source/version/provenance khớp; nội dung là draft, không chứng nhận tất cả facts|[ ] PASS [ ] FAIL [ ] BLOCKED|
|06|Xem WBS/proposal preview sẵn có và scope/hash của chính actor|DRAFT/preview không là Native task đã tạo; không auto follows relation/approval. Mutation UI interaction chỉ nghiệm thu trên clone|[ ] PASS [ ] FAIL [ ] BLOCKED|
|07|Gửi phân tích rủi ro với “chỉ đọc, không tạo đề xuất, không sửa công việc”|Không Native mutation; không ngầm cấp write scope; ghi run/error nếu có|[ ] PASS [ ] FAIL [ ] BLOCKED|
|08|Mở QA inbox/detail fc0479a8-b30a-5e88-9e4a-10748cb30415|pending_qa, đúngtarget/hash/version; người tạo không tự review. Bug371v4IN ANALYSIS giữ nguyên. Không bấm review/accept|[ ] PASS [ ] FAIL [ ] BLOCKED|
|09|Mở execution monitor/history/usage|Đúng actor/run/source; phân biệt model và localReviewer; historical error hiển thị trung thực, không đòi mọi agent luôn xanh|[ ] PASS [ ] FAIL [ ] BLOCKED|
|10|Xem16workflow trong n8n5679|Active/published; WF11 default Native QA read, WF12Friday17:00Bangkok; lỗi validation có thể có execution error hợp lệ. Không dùng execution IDs lịch sử làm expected mới|[ ] PASS [ ] FAIL [ ] BLOCKED|
|11|Xem integrity/status Second Brain|Registered corpus không missing/stale/payload/FTS drift. Snapshot441docs/2027chunks/2030points; PARTIAL_UNMATCHED_POINTS chỉ đúng3protectedlegacyIDs là expected limitation|[ ] PASS [ ] FAIL [ ] BLOCKED|
|12|Đăng nhập actor nghiệp vụ khác, xem tool/UI scope|Ẩn hoặc server-deny thao tác ngoài quyền; không tiết lộ Ownercomment/privateartifact. Không dùng proposal thật để thử approval|[ ] PASS [ ] FAIL [ ] BLOCKED|
|13|Xem validation error đã lưu hoặc thử payload đọc sai schema trong clone|Thông báo rõ, không secrets/stacktrace; malformed input không tự biến thành lệnh ghi|[ ] PASS [ ] FAIL [ ] BLOCKED|
|14|Xem TaskScheduler và private backup manifests|Hai task enabled/Ready, recentresult0, last-success cóPG/SQLite/n8n/assets/config; không lặpDR hoặc restartMAIN. Qdrant/fullreboot chưa qualify|[ ] PASS [ ] FAIL [ ] BLOCKED|

## Expected exceptions và giới hạn

- WP376test2/v0NEW, Bug371/v4IN ANALYSIS, pendingQA và29historical unresolvedrequests được bảo toàn; không phải dữ liệu cần dọn để có checklist sạch.
- Three unregistered points:2d5e7bdf-b4e0-52c6-b360-f45c1fbd74bf,59e1f1a4-b659-5c3d-ab23-ebb309481dc7,b838195a-5afd-5f40-a70d-23c2ca9007bc. Không xóa; registered canonical42 có revision riêng nên không đếm legacy bằng source label.
- Latest20comment/750chars; fullhash kiểm freshness, edit/clear sweep có thể11phút. File ingestion là server-pinned MD/DOCX/PDF, không OCR/arbitrary upload/allattachments.
- Weekly summary dùng rolling7days/as_of_date; Monday key chỉ dedupe. Source status history thiếu thì data_quality/limitation phải hiện, không bịa completed-throughput.
- External email/chat chưa cấu hình; local metadata delivery không phải external notification.
- Không có một run fresh clone-change→liveGemini liên tục; hai đoạn pipeline được qualify riêng. Không copy key hoặc bỏ quota guard để nghiệm thu.
- Physical reboot/pre-login, Qdrantfullrestore/cross-serviceDR và human approve MAIN chưa được thực hiện. Không gọi UAT checklist là release approval tự động.

## Sign-off của con người

- [ ] Operator đã hoàn tất các ca phù hợp, chấp nhận các giới hạn và đính kèm evidence thực tế.
- [ ] Có lỗi cần sửa; ghi số ca, actor, run/correlation ID, actual/expected và thời điểm.

Người kiểm tra: ____________________  Ngày: ____________________

Phạm vi chấp nhận / giới hạn: ___________________________________

Ký checklist không tự cấp quyền deploy public, gửi thông báo, delete dữ liệu hoặc approve QA/PM thật. `UAT_PASSED` và go-live gates chỉ cập nhật sau xác nhận rõ ràng của operator; agent không tự điền chữ ký.
