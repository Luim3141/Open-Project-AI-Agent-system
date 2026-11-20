# WBS QAG3 và kế hoạch nhập qua MCP

Cập nhật 2026-10-09 15:11 +07. [CSV v7](Jira_WBS_QAG3_v7_DRAFT.csv) đã được nhập qua **MCP Atlassian chính thức** thành backlog nháp QAG3: 11 Epic, 53 Task chức năng, 265 Subtask; tổng 329 mục. Người dùng duyệt ngoại lệ nhập trước workflow/gates: **“Duyệt nhập backlog nháp trước”**. Tất cả giữ To Do/DRAFT; không phải nghiệm thu WBS, workflow hoặc sản phẩm. Mỗi Task giữ nguyên câu User Story và hai Acceptance Criteria từ bản Word rút gọn. Không Burndown, không tạo Story trùng Task. Mục 7 là trạng thái hiện hành, thay các ghi chú “chưa nhập/chưa assignable” lịch sử bên dưới.

## 1. Phân rã và trách nhiệm

File v6 có 10 Epic, 10 Story, 10 Task tổng và 64 Subtask. V7 thay mô hình một Epic/một Task tổng bằng 4–6 Task chức năng độc lập/Epic. Ví dụ E01 có đăng ký, đăng nhập, đăng xuất, gán Role và kiểm soát quyền; E07 có xem Timeline, đặt lịch, quản lý phụ thuộc và nhận diện trễ/xung đột.

| Vai trò | Đầu ra Subtask | Email đề xuất |
| --- | --- | --- |
| BA | Mini-spec/AC, quyết định quyền/nghiệp vụ, dữ liệu mẫu và handoff; xác nhận UAT sau QA tại checklist Task. | hiepk40c@gmail.com |
| BE | Logic, dữ liệu/API, validation/authorization, unit/integration tests và code review độc lập. | nguyenduc6325@gmail.com |
| FE | Màn hình/thao tác nối dữ liệu, loading/empty/error, keyboard, safe rendering, kiểm tra UI/tích hợp. | ttheduy1401@gmail.com |
| QA | Test case từ AC, test execution, Fix Bug/retest evidence; không Done khi lỗi chưa xử lý/retest. | Duyhungls2005@gmail.com |
| PM | Điều phối Lead/BA/QA review, nghiệm thu, deploy Test/smoke và bàn giao. | 2101minhkhai@gmail.com |

Subtask có nội dung riêng cho từng chức năng: chống email trùng/phiên đăng nhập, Role theo Project, chuyển Sprint đồng thời, rollback kéo-thả, vòng phụ thuộc, vòng đời Bug, XSS/comment, thống kê không đếm trùng và notification dedupe/quyền lúc gửi. Không chỉ chia nút/ô nhập. Năm Subtask/Task là baseline của bài tập; Fix Bug phát sinh được tạo riêng dưới Task gốc, không trộn Bug mô phỏng vào baseline hiện tại.

BA hoàn tất phân tích trước Dev; dấu BA xác nhận ở Task sau kiểm thử không buộc Subtask phân tích chờ QA, tránh vòng chờ. PM yêu cầu **Subtask của các vai trò khác** hoàn tất trước khi hoàn tất Subtask bàn giao của mình; Task Done kiểm tra cả PM Subtask sau đó. Reviewer code độc lập do PM chỉ định theo chuyên môn, không tự approve code hoặc suy đoán reviewer đủ năng lực.

## 2. Trường CSV và ánh xạ

| Trường | Cách dùng |
| --- | --- |
| Project Key / Issue Type | QAG3; Epic, Task, Sub-task. Khi ghi MCP phải resolve project/type ID live, không fallback KAN. |
| Issue ID / Parent | ID tạm **trong file**, không phải Jira key/ID. MCP phải thay bằng key thật trả về sau tạo parent. |
| Source ID / Labels | E01, AUTH-01, AUTH-01-BA… và `source-<ID>` để trace/chống trùng trong đúng QAG3. Source KAN-01 không phải Jira KAN-1. |
| Issue Key / Assignee | Trống vì chưa tạo/gán thật; không gửi email như accountId đã xác minh. |
| Description / Acceptance Criteria / Checklist | Giữ Story, hai AC nguồn và đầu ra/bằng chứng/gate cần đạt. Checklist chưa hoàn thành; văn bản không thay hard gate. |
| Proposed Role / Proposed Assignee Email | Phân công đề xuất đúng năm người; không chứng minh membership, assignability hoặc role PM. |
| Reviewer Requirement | Trách nhiệm review cần resolve, không phải reviewer đã gán thật. |
| Status | NEW theo workflow yêu cầu, **không phải** trạng thái QAG3 đang áp dụng. Dừng import khi scheme chưa map; không tự đổi yêu cầu thành To Do. |
| Priority / Original Estimate | Trống cho tới refinement/PM duyệt. Proposed Priority là đề xuất High cho tài khoản/quyền, Medium phần còn lại. |
| Simulation Estimate Hours / Simulation Points | Đề xuất theo giả định năm Junior, 1 Point = 1 giờ Junior của bài tập; không phải worklog/Point đã nghiệm thu. |
| Proposed Sprint | S1–S5 là nhóm thực hiện chưa ngày/capacity/cam kết; không phải Sprint ID đã tạo. |
| Depends On Source IDs | Tiền đề triển khai/đầu ra hợp đồng cần sẵn sàng. Refinement xác định handoff, không mặc định toàn Task tiền đề phải Done hoặc tự tạo Jira link blocks. |
| Integration With Source IDs | Tích hợp cần nghiệm thu chung, không phải thứ tự cứng. Assignment/notification cùng S2, comment/mention/notification cùng S4. Không nghiệm thu AC notification bằng mock. |
| Approval | DRAFT. Duyệt phân rã khác duyệt lô ghi/admin và khác nghiệm thu chức năng. |

CSV UTF-8 BOM, quote trường xuống dòng/dấu phẩy/ngoặc kép. Đây là **nguồn dữ liệu cho nhập bằng MCP**; không cam kết importer UI Jira tự hiểu các cột đề xuất/tùy biến. Không dùng UI importer để bỏ qua yêu cầu MCP.

## 3. Ước lượng và capacity

| Vai trò | Giờ/Point Junior mô phỏng |
| --- | ---: |
| BA | 169 |
| BE | 392 |
| FE | 327 |
| QA | 295 |
| PM | 114 |
| Tổng | 1297 |

Task estimate bằng tổng năm Subtask. Báo cáo cộng Task **hoặc** Subtask, không cộng cả hai cấp; Epic không gán Point tổng lần nữa. Không chia đều Point giữa vai trò để làm đẹp số liệu.

Nếu dùng lại giả định lịch lớp 47 ngày × 8 giờ = 376 giờ/người, BE vượt quỹ lý thuyết 16 giờ, chưa có buffer bug/review/vắng mặt. Tổng quỹ nhóm dư không giải quyết nút thắt BE. Chốt capacity/lịch/buffer rồi cân đối thứ tự/release; chỉ chia sẻ phần BE khi xác minh chuyên môn và PM duyệt. Không tự cắt yêu cầu/giảm estimate cho vừa lịch.

Không tự bắt đầu/đóng Sprint. Estimate không chứng minh năng suất. Review thật theo AGENTS.md, dữ liệu thiếu không chấm zero; mô phỏng có nhãn riêng, không giả mạo worklog/changelog. Ví dụ nguồn 40/30 × 100 phải là **133,33%**, không phải 125–130%; chỉ so sánh khi cùng phạm vi đã nghiệm thu và điều kiện đã nêu. “Point = giờ Junior” và KPI Bug của lớp là quy ước thực hành, không mô tả là chuẩn chung ngành.

## 4. Quy trình nhập chuẩn ban đầu (lịch sử; ngoại lệ đã duyệt ở mục 7)

1. Preflight identity/site/QAG3; workflow/scheme/gates/quyền và tests cần thiết đạt trước import. Hiện **chưa đạt**.
2. Người dùng duyệt CSV/phân công/estimate và preview lô ghi. Bốn email chưa assignable cần xử lý membership/visibility rồi resolve accountId. hiepk40c assignable không chứng minh role PM.
3. Tìm `source-<ID>` đúng QAG3, đọc hết pagination: 0 match đề xuất create; 1 match đọc/diff xin duyệt update; nhiều match dừng. Không ghi KAN.
4. Preview mẫu E01 → AUTH-01 → năm Subtask. Mẫu đạt là một phần WBS, không nhập thêm lần nữa. Issue chỉ test dùng source/label riêng, loại khỏi performance.
5. Tạo Epic → lưu key/ID thật → tạo Task với Epic parent thật → tạo Subtask với Task parent thật. Không gửi nguyên toàn bộ cột CSV vào payload; resolve field/type/priority/assignee và đơn vị time tracking. Checklist text không thay validator.
6. Đối soát từng lô, sau timeout đọc lại bằng source trước retry. Lưu Source ID → key thật cùng parent/Story/AC/assignee/trạng thái và trace.
7. Chỉ nhập đủ 329 item sau mẫu đạt và lô đầy đủ được duyệt. Đối soát 11/53/265, 106 AC, unique source, đúng năm tài khoản và QAG3. Không tự start Sprint/Done/nghiệm thu.

Chưa có Jira write. Không xóa dự án/ticket để rollback; giữ mẫu/mapping và preview sửa. Bộ T01–T23 trong [jira-workflows.md](jira-workflows.md) vẫn **NOT RUN**.

## 5. Đối chiếu tại thời điểm lập WBS (lịch sử; xem kết quả mới ở mục 7)

| Nội dung yêu cầu | Kết quả hiện tại |
| --- | --- |
| Chọn nguồn mở, giới hạn nhóm, migration local | Hoãn theo người dùng, không triển khai đợt này. |
| AI phân tích và phân chia công việc theo vai trò | CSV 11/53/265 đã kiểm tra local; có đề xuất email, chưa phân công thật. |
| CSV và kết nối MCP | CSV đạt kiểm tra; local/hosted MCP xác thực và đọc QAG3. Chưa nhập. |
| Demo IDE nhận Task → review/test → notify | Có playbook/workflow yêu cầu, chưa demo E2E. Mock/read-only không tính hoàn tất. |
| Point/estimate từng Task/Subtask | Đề xuất mô phỏng riêng Subtask/rollup Task; chưa cấu hình/ghi field Jira. |
| Bug giả lập gán Dev gốc | Quy trình Fix Bug có trong checklist; chưa tạo Bug giả trên Jira, chờ lô demo được duyệt. |
| Performance Review / Sprint completion | Template riêng tư hiện có; chưa snapshot/kết quả mô phỏng hoặc export biểu đồ thật. |
| Workflow riêng Epic/Task/Subtask | Đặc tả 6/10/4, Inactive theo checkpoint; QAG3 live còn ba trạng thái mặc định, chưa scheme/gates/automation/test. |

## 6. Bằng chứng và nguồn

Builder/verifier độc lập đối chiếu **Word hiện tại**: từng Story và 106 AC trùng chính xác, đúng Epic cha; 329 Source ID/ID tạm duy nhất, năm vai trò/Task, Parent đúng cấp, không E11, tham chiếu tồn tại, prerequisite graph không chu trình, rollup 1297 khớp. CSV đọc lại bằng parser CSV độc lập và PowerShell Import-Csv. Preview cấu trúc từ Artifact Tool đã xem; CSV không giữ style preview. Chưa kiểm thử importer Jira hoặc chức năng sản phẩm.

- [User Story rút gọn](user-story-web-quan-ly-du-an-rut-gon.docx).
- Bài tập: `D:\ZALO file\Bao_Cao_Thuc_Hanh_3_Quan_Ly_Agile_AI_Va_Hieu_Suat.docx`.
- Workflow lớp: `D:\Download\Cap_Nhat_Quy_Trinh_Workflow_Task_Subtask_Agile.docx`.
- V6 đối chiếu: `D:\ZALO file\Jira_Import_WBS_Scrum_v6.csv`; không sửa nguồn.
- Hợp đồng: [jira-workflows.md](jira-workflows.md), [AGENTS.md](AGENTS.md).
- SHA-256 CSV: `49368cf812189fa981cf6021f00353dc906b2c5015adc80bddcbc1d449535577`.
- SHA-256 Word: `e9b975e379594991087b045ef6cd00c4598ae07c0b6093db456fa8fe34c818c1`.

Điểm chặn tại thời điểm lập WBS: MCP chưa expose admin workflow/scheme/automation, hard gate Epic–Task chưa chứng minh miễn phí, bốn người chưa assignable; approval WBS/import chờ. Trạng thái import/assignability đã thay đổi theo mục 7; không mua add-on/trial.

## 7. Nhập backlog nháp đã duyệt — 2026-10-09 15:11 +07

- Approval riêng cho 329 mục ở To Do/DRAFT, phân công năm tài khoản thật, checklist chưa hoàn tất. Chỉ thay thứ tự import; không bỏ hard gate, không duyệt activation hoặc coi WBS đã chốt Sprint/nghiệm thu. CSV nguồn giữ nguyên NEW/DRAFT và SHA-256 nêu trên; mapping To Do là ngoại lệ được duyệt, không sửa nguồn.
- Preflight official MCP: đúng owner/site/cloud/QAG3/10002/classic; project ban đầu rỗng, metadata Epic10000/Task10011/Sub-task10010 và toàn bộ năm assignee hợp lệ. Live chỉ To Do10008/In Progress3/Done10009. Không gửi field Epic Name hoặc estimate/Point/sprint chưa có căn cứ.
- Mẫu E01 → AUTH-01 → năm Subtask tạo thành QAG3-1 đến QAG3-7; đọc lại đạt trước nhập phần còn lại. Toàn bộ QAG3-1 đến QAG3-329 đã đọc lại qua bốn trang full tới isLast=true: đủ 11/53/265, Source ID duy nhất, đúng project/type/summary/Parent/assignee/labels và nội dung đầy đủ sau chuẩn hóa Markdown. Timetracking rỗng; checklist vẫn unchecked. 106 AC nguồn của 53 Task được bảo toàn trong nội dung đã đối chiếu.
- BA/BE/FE/Tester mỗi người 53 Subtask; PM 53 Subtask cùng 53 Task và 11 Epic để điều phối. Số issue trên nhiều cấp không dùng để cộng đôi workload hoặc chấm hiệu suất. Business role không phải Jira project role; accept lời mời chưa xác minh lại.
- Kế hoạch mô phỏng, ưu tiên, Sprint đề xuất và Depends On Source IDs nằm trong description; chưa phải field estimate/worklog/Point, Sprint thật hoặc issue link blocks. Không tạo Bug demo, không start/Done, không bật A01–A05; không sửa KAN/SAM1, bot, snapshot đã chốt hoặc lịch.
- MCP mất transport ở lệnh PRJ-03-QA; tra Source ID xác định QAG3-49 đã tồn tại, đọc lại và tiếp tục, không replay create. Truy vấn cuối lần đầu thiếu mục mới, lần đọc đầy đủ kế tiếp trả đủ329; không tạo lại để bù kết quả search chậm cập nhật.
- Mapping và audit riêng tư: `jira-bot/wbs-import-QAG3-2026-10-09.json`, trạng thái COMPLETED_DRAFT_IMPORT, verifiedAtUtc 2026-10-09 08:11:19 UTC. Không xóa để rollback; mọi sửa/xóa hoặc migration workflow cần preview tác động và approval riêng.
- QAG3 không còn rỗng: guard admin empty-project hiện không cho associate. Phải thiết kế migration/map trạng thái cho project có dữ liệu, không tự bypass guard hoặc dùng checklist text thay server-side validator. T01–T23 tổng thể vẫn NOT RUN; việc đối soát import không làm toàn bộ bộ test PASS.
