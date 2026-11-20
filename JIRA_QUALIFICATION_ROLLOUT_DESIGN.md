# QAG3 — mô phỏng và đường triển khai thử

Trạng thái: **PROPOSED, chưa triển khai**. Không phải bằng chứng activation, migration hoặc E2E. Thiết kế này không thay giới hạn MCP hiện tại.

## 1. Tách nguồn dữ liệu

| Nguồn | Mục đích | Không được dùng để |
|---|---|---|
| SIMULATION | Tiến độ/worklog/điểm và kịch bản học tập giả định | Chứng minh gate hoặc cấp quyền rollout |
| LOCAL_TEST | Kiểm tra code/predicate bằng fixture | Chứng minh transition/automation thật trên Jira |
| JIRA_E2E | Test thao tác thật, actor/issue/readback/audit | Mặc nhiên chứng minh tính năng sản phẩm đã lập trình |

Không ghi đè lịch sử; không ghi số liệu mô phỏng vào rollout-evidence.json. User cho phép thiết kế lại, nhưng approval này không thay exact-hash approval hoặc yêu cầu recorded gate tests của công cụ.

## 2. Demo offline

Dùng WBS329 và dữ liệu mô phỏng hiện có để trình bày Epic6/Task10/Subtask7. Kịch bản có kết quả giả định ghi SIMULATED, không jira-e2e. Fixtures là kiểm thử local, không tạo email/thông báo hoặc giả author của thành viên. Demo không đòi migration và không chứng minh Jira đã active.

## 3. Đường qualification đề xuất

Mục tiêu: khu vực kiểm thử cách ly, bản sao workflow và issue thử, không đưa329mục vào chỉ để có nơi chạy test. Chưa chọn/tạo project mới. Trước lựa chọn cần xác minh Free/quyền/API/tool thật.

Capability triển khai thử hợp lệ cần:

- Preview target, cấu hình trước/sau, giới hạn issue thử, workflow version/fingerprint, scope rule và rollback.
- Human approval đúng hash, không lấy quyền từ ticket hoặc generic approval.
- Giữ rollout_blockers() của migration QAG3, không sửa evidence để vượt chặn.
- Không bỏ validator/PM/QA hoặc impersonate actor. Test quyền bằng danh tính được xác thực.
- Bằng chứng từng test có ID, actor, issue, thao tác, expected/actual, readback và audit. Không chạy giữ NOT RUN/BLOCKED.

Nếu tool vẫn yêu cầu gate tests trước mọi activation, đường này chưa khả dụng. Không dùng shell/API/UI khác để vòng qua hạn chế; cần capability/policy thử nghiệm được cung cấp hợp lệ. Tài liệu này không tự cấp capability.

## 4. Thứ tự thử

1. Preview sửa Resolution của Cancel Epic, reason của Reanalyse/Return; giữ before snapshot.
2. Kiểm tra field/screen/gate và hai nhánh Subtask.
3. Tạo A01–A05 DISABLED bằng phương thức quản trị được hỗ trợ; đọc lại actor/scope/nội dung/ID. Không đoán JSON import hoặc schema API.
4. Chạy gate negative/positive, Parent change, replay/concurrency và rule errors trên đường thử hợp lệ.
5. Không tự chuyển PASS của workflow bản sao sang QAG3: đối soát cấu hình và chạy target smoke bằng cơ chế được phép.

## 5. Automation

- A01: Task bắt đầu → Epic READY sang IN PROGRESS.
- A02: Không rỗng và mọi Task Done → Epic REVIEW, không tự DONE.
- A03: Thêm/reopen Task hợp lệ → Epic REVIEW/DONE sang IN PROGRESS, reason/audit/clear Resolution.
- A04: Parent đổi → đối soát Epic cũ/mới, không tự nghiệm thu/restore CANCELLED.
- A05: Reviewer notification một lần mỗi event vào bước review; thử với đích kiểm thử để tránh spam.

Scope chỉ target đã xác minh, fail-closed khi thiếu trang/quyền/Parent cũ. KAN/SAM1 không đổi; monitor vẫn PAUSED.

## 6. Migration và rollback

Sau bằng chứng đúng hợp đồng và exact-hash approval: switch QAG3/10002 từ10003→10004. Giữ InProgress3/Done10009; ToDo10008 nếu có phải preview mappingNEW10010. Đọc hiện trạng mới, không dùng số lượng/status lịch sử thay snapshot.

Poll async task và đối soát association/mappings/329issue key/type/Parent/assignee/nội dung/thời gian. UNKNOWN không retry mù. Rollback cần preview mapping ngược giữ dữ liệu, không xóa issue/worklog hoặc uninstall app đang dùng.

## 7. Trạng thái thực hiện

Lượt này chỉ tạo thiết kế local. Chưa sửa gateway/gates, tạo project/rule, ghi Jira hoặc migration. Chưa có qualification capability được triển khai. Kết quả đã chạy giữ trong JIRA_TEST_RESULTS_2026-10-11_2219.md; không ghi E2E PASS mới.
