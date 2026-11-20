# Checkpoint Gemini reliability — 15/10/2026

## Hoàn tất trên staging 18091/18092

Đã sửa và nghiệm thu yêu cầu Gemini không tạo/sửa được, lỗi parent/workflow, quota local và kết quả bị gián đoạn. Live 8088/8090 và Jira không thay đổi. Không tự chạy lại các lượt nghiệp vụ lỗi cũ.

### Nguyên nhân và bản sửa

- BE/FE/QA/BA-PM thiếu `manage_subtasks`, nên native form từ chối trường parent. Đã backup và thêm duy nhất quyền này cho role13–16, chỉ đang dùng trong project3. PM12 giữ nguyên. Đã đối chiếu toàn bộ permissions; không đổi thành viên, admin hay quyền khác.
- Gateway trước đây bỏ mất lỗi native form. Nay giữ HTTP422, trường lỗi, mã và lý do bằng lời để Gemini/người dùng hiểu và sửa đúng.
- Model phải lồng JSON trong chuỗi `arguments_json`, gây JSONDecodeError. Business mode nay dùng9 typed function declarations; legacy metadata/code transport giữ nguyên.
- TPM trước đây lấy max(token count, UTF-8 bytes), làm hết ngân sách giả. Nay dùng countTokens (kể cả phần system/tool được serialize để đếm). List trả tóm tắt, get từng công việc vẫn đọc đầy đủ nghiệp vụ được phép.
- Trước khi gửi request mới, thiếu RPM/TPM theo phút sẽ ghi tiến độ chờ và tự tiếp tục trong run600s. Không lặp inference đã gửi hoặc native write chưa rõ kết quả. Quota ngày/Google cooldown vẫn áp dụng; không reset usage, đổi key/model/billing hay nâng quota.
- Worker/client/stale-run timeout đồng bộ600s; run bị gián đoạn vẫn giữ receipt/thao tác đã hoàn thành. Tham số update trống, ngày sai và role sai có validation rõ.

Workflow đã có đủ. Đối chiếu matrix trước/sau nguyên vẹn: PM69, BA-PM13, BE17, FE17, QA19 entries; không thêm transition hoặc bỏ gate. Không khôi phục giới hạn6 thao tác.

### Nghiệm thu thực tế

- Windows137 tests PASS; Linux76 tests PASS,1 kiểm tra chỉ dành cho Windows được skip. Log `artifacts/assistant-reliability-{unit-final,linux-final}.log`.
- Native đủ5 role: Epic→Task→Subtask, parent/assignee, sửa tên/mô tả/ưu tiên/hạn/người phụ trách, xóa hạn, comment, transition, replay một lần và stale version từ chối.
- Gemini thật đủ5 role: mỗi role tạo Subtask có parent, cập nhật, comment và chuyển trạng thái; đọc độc lập OpenProject khớp yêu cầu.
- Ca gốc: BE tạo PM review có parent và giao PM thành công; QA không được vượt assignee workflow, PM chuyển được.
- Preview thật: trước duyệt chưa ghi; duyệt đúng một lần; từ chối không ghi; đề xuất đã xử lý bị từ chối khi dùng lại.
- Tám comment riêng trong một yêu cầu qua Gemini thật: đúng8 native journals, không trùng. Đã chạy đủ9 business tools, gồm identity/list/analyze/get/options và4 write tools.
- Chờ quota local thật PM16s, FE3s, bulk11s và read-tools3s rồi tự hoàn tất, giữ receipt.
- Browser thật: đọc nghiệp vụ #58; bật checkbox + scope trống tạo đúng Subtask435/parent423/PM/description. Run `e205f43b-bd34-421c-b8a6-6dbc323b4fc9` đã done. Các run/report nằm trong `artifacts/assistant-reliability-stage.json`.
- Đã xóa chính xác14 fixtures422..435. Toàn bộ329 bản ghi nguồn giữ nguyên business fields/custom fields/parent/assignee/type/status/priority/lockVersion/updatedAt theo snapshot trước/sau. Role/workflow đối chiếu PASS.
- Gateway restart PASS: usage/circuit/recovery/requests/AI runs byte-content fingerprints giữ nguyên; config/key/proof/image lock giữ nguyên; receipt đọc lại done. Gemini authorized, expires:null;0 active runs/0 queued hoặc running jobs,0 provider blocks.

### Runtime và nguồn

Core: `sha256:da708dd80f4214c51b20d41d454cf4158ca7453e40d8970b68fcbe853fe4680a`
Gateway: `sha256:87a6549b48ce975bba8c388c0fb6df265a5f5b6dc5ea127b42936abd980e81e4`
Core fork: `b4fe82644e96f2a941ace41be0ef81599864fef9`, clean; không sửa core/hierarchy overlay trong lượt này.
Final candidate: source/image parity PASS; `artifacts/assistant-reliability-candidate-final.json`. Đây không phải production qualification/release approval.

Source thay đổi: gateway/__init__.py, native.py, service.py, presentation.py, ai_worker.py, store.py, catalog.py, gemini.py; exports mcp-tools.json/openapi.json đồng bộ; tests/test_reliability.py + callers/fixtures/test deadlines và tests/stage_reliability.py. architecture.md và BUSINESS_COMMANDS.md đã cập nhật.

### Quota và giới hạn còn lại

Ledger cuối318 reservations (đầu240; tăng78 từ10 lượt Gemini thật). Local rolling caps vẫn10RPM/175000TPM/350RPD; đếm countTokens và generate conservatively thành2 RPC. Cửa sổ24h hiện có296 reservations, còn54 local reservations tại thời điểm nghiệm thu; không đồng nghĩa54 yêu cầu chat. Ledger318 là toàn bộ lịch sử, gồm22 entries đã ngoài24h. Quota được phục hồi theo cửa sổ thời gian, không bị xóa khi restart. Quyền dùng Gemini liên tục không hết hạn, nhưng không tạo quota vô hạn hoặc bỏ quyền native. Không gọi Google thêm để kiểm tra restart.

### Rollback / tiếp tục nếu phiên bị ngắt

Không có migration/schema mới. Backup ngoài Git: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/reliability-20261015/` gồm roles-before.json, gateway-before-1792036270 và gateway-pre-final-* với state/lock. Rollback chỉ image gateway về bản cũ90f7a3cc… và lock tương ứng, giữ DB/ledger/receipt HIỆN TẠI; không restore usage cũ. Nếu cần rollback quyền, chỉ role13–16 từ permissions backup sau khi kiểm tra không có thay đổi mới. Core/live/Jira giữ nguyên.

Không chạy lại `native`, `google`, `extra`, `cleanup` của harness trên manifest đã hoàn tất: fixture đã bị xóa; các receipt vẫn là lịch sử nghiệm thu. Có thể đọc checkpoint/report/log hoặc kiểm tra trạng thái bằng HTTP. Không mở SQLite gateway đang chạy từ Windows; chỉ docker exec với SQLite mode=ro.

Ảnh kiểm thử: `artifacts/assistant-reliability-operations-browser.png`, `assistant-reliability-checkbox-browser.png`, `assistant-reliability-read-browser.png`.

Kiểm tra terminal: toàn bộ9run trong report done với đúng trạng thái dự kiến, không có tool error; report passed:true. Browser sau cleanup hiển thị329/authorized và để sẵn tab riêng2658 tại AI Assistant. Ảnh trạng thái cuối: artifacts/assistant-reliability-ready-browser.png.
