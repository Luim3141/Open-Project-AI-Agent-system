# CODEX — QLDAPM MAIN PHASE 2 CONTINUATION
## FEATURE COMPLETION FIRST — IMPLEMENTATION MODE — UAT DEFERRED

**MỨC ƯU TIÊN: HOÀN THIỆN TOÀN BỘ CHỨC NĂNG TRƯỚC KHI CHUYỂN SANG KIỂM THỬ NGHIỆM THU.**

**Ngôn ngữ làm việc: Tiếng Việt.**

---

# 1. CHỈ ĐẠO MỚI CỦA NGƯỜI DÙNG

Tôi đã nhận được báo cáo của bạn với trạng thái:

`READY_FOR_USER_UAT`

Tuy nhiên, **TÔI CHƯA MUỐN THỰC HIỆN UAT VÀ CHƯA CHẤP NHẬN KẾT LUẬN TRIỂN KHAI ĐÃ HOÀN TẤT.**

Tôi muốn bạn tiếp tục phát triển, hoàn thiện và tích hợp đầy đủ toàn bộ chức năng đã yêu cầu trong Phase 2.

Mục tiêu hiện tại là:

**FEATURE-COMPLETE IMPLEMENTATION FIRST — UAT LATER.**

Các kết quả trước đó gồm:

- OpenClaw và Gemini API đã được thiết lập.
- Supervisor đã chạy chuỗi Agent.
- Mini Task Manager đã được triển khai.
- 86 targeted tests PASS.
- 15 final checks PASS.
- 17 application tests PASS.
- Project 5 được bảo toàn.
- 16 workflow n8n hoạt động.
- PR #1 và #2 đã được tạo.
- Gemini handoff được cập nhật.

Hãy coi đây là **baseline đã đạt**, không phải lý do để dừng phát triển.

Số lượng test PASS không đồng nghĩa toàn bộ chức năng đã đầy đủ.

**NHIỆM VỤ CỦA BẠN LÀ TIẾP TỤC TRIỂN KHAI, KHÔNG CHỈ ĐỀ XUẤT HOẶC BÁO CÁO.**

---

# 2. THAY ĐỔI ƯU TIÊN KIỂM THỬ

Trong giai đoạn này:

**KHÔNG thực hiện User Acceptance Testing.**

**KHÔNG yêu cầu tôi tự mở trình duyệt để nghiệm thu.**

**KHÔNG chạy lại toàn bộ E2E, regression và các bộ test lớn chỉ để tạo thêm bằng chứng PASS.**

**KHÔNG dành phần lớn thời gian hoặc quota cho test coverage, báo cáo kiểm thử hay audit không cần thiết.**

Ưu tiên tài nguyên cho:

1. Hoàn thiện chức năng.
2. Bổ sung phần còn thiếu.
3. Sửa các luồng tích hợp chưa đầy đủ.
4. Cải thiện khả năng Agent tự thực thi công việc.
5. Hoàn thiện giao diện điều khiển.
6. Đồng bộ giữa OpenProject, n8n, OpenClaw, GitHub và Second Brain.
7. Đảm bảo source được triển khai nhất quán.
8. Duy trì Gemini handoff.

Chỉ thực hiện các bước kiểm tra kỹ thuật tối thiểu, có mục tiêu, khi cần xác nhận thay đổi mới không làm hỏng startup hoặc luồng liên quan trực tiếp.

Không bỏ qua lỗi phát hiện trong quá trình triển khai, nhưng không khởi động một chiến dịch kiểm thử tổng thể mới.

**UAT và kiểm thử nghiệm thu cuối sẽ được tiến hành khi tôi yêu cầu riêng.**

---

# 3. KHÔNG TRIỂN KHAI LẠI TỪ ĐẦU

Workspace:

`D:\AI project\QLDAPM chat`

Demo repository:

`D:\AI project\QLDAPM-demo\mini-task-manager`

OpenProject:

`http://127.0.0.1:18088`

Engineering Project:

`Project ID 6 — ai-dev-demo`

Work Package:

`#379 — Develop Mini Task Manager Application`

AI Gateway:

`http://127.0.0.1:18089`

Mini Task Manager:

`http://127.0.0.1:18791`

Trước khi thực hiện thay đổi, đọc:

- `docs/ai/engineering/HANDOFF_GEMINI_LATEST.md`
- `docs/ai/engineering/IMPLEMENTATION_STATE.json`
- `docs/ai/engineering/IMPLEMENTATION_JOURNAL.md`
- `docs/ai/engineering/OPERATIONS_RUNBOOK.md`
- `docs/ai/engineering/E2E_EVIDENCE.md`
- `docs/ai/engineering/GEMINI_CONTINUE_PROMPT.md`

Đối chiếu với source và runtime hiện tại.

Không giả định checkpoint là trạng thái thực tế nếu source/runtime đã thay đổi.

Bảo toàn mọi công việc đã hoàn thành.

Báo cáo trước cho biết QLDAPM MAIN còn các thay đổi chưa commit và có snapshot SHA256 của 39 file. Không được reset hoặc overwrite những thay đổi này.

Không nghiên cứu lại Paperclip, Agency Agents hoặc Superpowers từ đầu.

Tận dụng kết quả Phase 1.

---

# 4. KIỂM TRA FEATURE COMPLETENESS THAY VÌ TEST COVERAGE

Trước tiên, kiểm kê chức năng thực tế của QLDAPM Phase 2.

Đối chiếu toàn bộ yêu cầu đã giao với source hiện tại.

Lập bảng nội bộ:

`Feature | Requirement | Existing Implementation | Missing Behavior | Target Module | Implementation Priority`

Phân loại:

- COMPLETE.
- PARTIAL.
- MISSING.
- INTEGRATION_INCOMPLETE.
- NOT_APPLICABLE.

Một chức năng không được coi là COMPLETE chỉ vì:

- Có tên trong Agent Registry.
- Có prompt mô tả chức năng.
- Có API endpoint nhưng chưa nối vào UI.
- Có UI nhưng button chưa gọi backend.
- Có workflow nhưng chưa xử lý kết quả thực tế.
- Có skill Markdown nhưng Agent chưa sử dụng.
- Có test mock PASS nhưng chức năng runtime chưa nối.
- Có báo cáo PASS từ một lần chạy lịch sử.

**Không chỉ dừng ở bảng đánh giá.**

Sau khi xác định gap, tiếp tục triển khai những phần còn thiếu theo mức độ ưu tiên.

Không viết lại chức năng đã thực sự hoàn chỉnh.

---

# 5. HOÀN THIỆN HỆ THỐNG AI AGENTS

## 5.1. AI Supervisor

Supervisor phải có đủ khả năng:

- Nhận công việc từ OpenProject.
- Xác định project, actor, Work Package.
- Lựa chọn engineering unit phù hợp.
- Phân tích dependency.
- Lựa chọn Agent.
- Phân công công việc.
- Truyền context và acceptance criteria.
- Theo dõi trạng thái.
- Tiếp nhận kết quả.
- Quyết định chuyển bước.
- Xử lý Agent bị lỗi hoặc bị chặn.
- Thực hiện rework.
- Ghi durable execution state.
- Đồng bộ tiến độ.
- Cho phép tiếp tục công việc chưa hoàn thành.
- Kết thúc run chính xác.

Tận dụng cơ chế Paperclip đã nghiên cứu:

- Task ownership.
- Task claim.
- Agent delegation.
- Handoff.
- Wake/deduplication.
- Execution lifecycle.
- Retry/recovery.
- Budget management.

Không cài Paperclip server.

Không tạo Supervisor thứ hai trong OpenClaw.

## 5.2. PM Agent

Phải thực sự có khả năng:

- Phân tích yêu cầu dự án.
- Lập kế hoạch.
- Chia Epic/Task/Subtask phù hợp.
- Xác định dependencies.
- Ưu tiên backlog.
- Giao việc dựa trên khả năng Agent.
- Theo dõi tiến độ.
- Nhận diện blocker.
- Đề xuất bước tiếp theo.
- Cập nhật dữ liệu OpenProject Project 6 khi được phép.

Không chỉ tạo nội dung kế hoạch rồi bỏ đó.

## 5.3. BA Agent

Phải thực sự có khả năng:

- Phân tích yêu cầu.
- Xác định phạm vi.
- Tạo functional specification.
- Viết acceptance criteria.
- Xác định API behavior.
- Ghi nhận edge cases.
- Gắn yêu cầu với engineering units.
- Bàn giao đặc tả cho Dev.
- Cập nhật yêu cầu khi có feedback.

## 5.4. Dev Agent — OpenClaw + Gemini API

Phải có quyền và công cụ thực thi thật:

- Đọc source.
- Tạo file.
- Sửa file.
- Xóa file code cần thiết.
- Chạy terminal.
- Cài dependencies.
- Thực hiện Git operations.
- Viết backend/frontend.
- Chạy build.
- Phân tích traceback.
- Debug.
- Sửa lỗi.
- Thực hiện lại bước bị lỗi.
- Bàn giao code và artifacts.

Dev Agent không được chỉ trả một đoạn code trong Markdown.

## 5.5. Reviewer Agent

Phải có khả năng:

- Đọc Git diff thật.
- Đối chiếu implementation với specification.
- Đánh giá logic và kiến trúc.
- Phát hiện lỗi trong code.
- Đưa feedback cụ thể.
- Yêu cầu Dev sửa lỗi.
- Tiếp tục review sau thay đổi.

Giữ session Reviewer độc lập với Dev.

## 5.6. QA Agent

Phải có khả năng:

- Nhận acceptance criteria.
- Thực thi các công cụ kiểm tra cần thiết.
- Thu thập kết quả thật.
- Ghi nhận lỗi.
- Chuyển lỗi cho Dev.
- Xác nhận kết quả sau khi sửa.

Trong phiên hiện tại, ưu tiên hoàn thiện capability và integration của QA, không mở chiến dịch UAT hoặc chạy lại toàn bộ test suite.

---

# 6. AGENCY AGENTS + SUPERPOWERS PHẢI ĐƯỢC TÍCH HỢP THỰC CHẤT

## Agency Agents

Kiểm tra các persona đã chọn có thực sự được áp dụng trong:

- Supervisor.
- PM.
- BA.
- Dev.
- Reviewer.
- QA.

Mỗi Agent phải có:

- Role.
- Responsibilities.
- Skills.
- Tools.
- Permissions.
- Input contract.
- Output contract.
- Deliverables.
- Handoff conditions.

Không tạo thêm hàng chục Agent không cần thiết.

## Superpowers

Hoàn thiện các skills phù hợp:

- Brainstorming.
- Writing Plans.
- Git Worktrees.
- Test-Driven Development.
- Systematic Debugging.
- Code Review.
- Receiving Review Feedback.
- Verification Before Completion.
- Finishing Development Branches.

Đảm bảo skill được gắn đúng Agent, được nạp vào phiên OpenClaw khi cần và có công cụ thực tế để thực hiện.

Không coi việc tồn tại file `SKILL.md` là đủ để tuyên bố triển khai xong.

---

# 7. OPENCLAW + GEMINI API — HOÀN THIỆN RUNTIME

Giữ kiến trúc:

**QLDAPM Supervisor → OpenClaw Engineering Runtime → Gemini API.**

Kiểm tra và hoàn thiện:

- Agent registration.
- Model selection.
- Session lifecycle.
- Workspace management.
- Tool execution.
- Persistent execution references.
- Agent cancellation.
- Retry/recovery.
- Result callbacks hoặc polling phù hợp.
- Error propagation.
- Cost/usage reporting.
- Output artifact contracts.

PM/BA có thể tiếp tục dùng Gemini thông qua Gateway QLDAPM.

Dev/Reviewer/QA dùng OpenClaw cho thao tác kỹ thuật.

Không bắt buộc mọi Agent đều phải chạy trong OpenClaw.

Không tạo hệ thống model routing mới.

Không dùng 9Router.

Không phụ thuộc ChatGPT Plus hoặc OpenAI API.

Không tạo inference loop không giới hạn.

---

# 8. N8N — GIỮ VÀ HOÀN THIỆN AUTOMATION

Giữ toàn bộ 16 workflow hiện hữu.

Kiểm tra các điểm kết nối của Phase 2:

- OpenProject event.
- Gateway dispatch.
- Engineering run status.
- OpenClaw completion.
- Work Package progress.
- Knowledge ingestion.
- Error/retry.
- Notification/monitoring khi có.

Nếu một tính năng đã có backend nhưng chưa nối đúng vào automation, hãy hoàn thiện.

Không tạo thêm một orchestration engine trùng với n8n.

Không biến n8n thành bộ điều khiển từng lệnh lập trình.

Không sửa những workflow đang hoạt động nếu không liên quan tới gap thực tế.

---

# 9. SECOND BRAIN + RAG — PHẢI ĐƯỢC SỬ DỤNG THẬT

Giữ:

- SQLite knowledge database.
- FTS5.
- Qdrant.
- Ollama BGE-M3.
- Existing ingestion.
- Existing RAG/citation mechanisms.

Hoàn thiện khả năng phục vụ Project 6.

Agent cần có khả năng:

1. Tìm kiến thức dự án.
2. Truy xuất yêu cầu và acceptance criteria.
3. Lấy architectural context.
4. Sử dụng thông tin có nguồn trích dẫn.
5. Bàn giao context giữa PM/BA/Dev/Reviewer/QA.
6. Ghi nhận quyết định và tài liệu mới.
7. Đồng bộ metadata commit/PR.
8. Truy xuất lại tri thức đã ghi.
9. Duy trì project context đúng.

Không tạo Second Brain thứ hai bên trong OpenClaw.

OpenClaw memory chỉ phục vụ working context/session.

**RAG QLDAPM vẫn là shared project knowledge system.**

---

# 10. RUN ONCE / OFF / PAUSE — HOÀN THIỆN TOÀN BỘ

Phải có các chức năng thực sự hoạt động:

## OFF

- Không nhận engineering runs mới.
- Không gọi Gemini định kỳ cho engineering.
- Giữ tiến độ và artifacts.
- Không tắt các dịch vụ QLDAPM chung.

## RUN ONCE

- Chọn project và Task.
- Supervisor nhận một đơn vị công việc.
- Phân công các Agent.
- Agent thực hiện thật.
- Cập nhật tiến độ.
- Kết thúc run.
- Tự quay về OFF.

## PAUSE

- Không giao bước mới.
- Lưu execution state.
- Xử lý công việc đang chạy ở ranh giới phù hợp.
- Có thể tiếp tục mà không chạy trùng.

## CANCEL

- Hủy lượt thực thi phù hợp.
- Dừng công việc đang chạy.
- Lưu kết quả đã tạo.
- Không báo giả rằng công việc đã hoàn thành.

## RESUME / RECOVERY

- Đọc trạng thái thực tế.
- Tiếp tục phần chưa hoàn thành.
- Không code lại những phần đã hoàn tất.
- Không tạo duplicate commits/PRs/Task.
- Không mất handoff context.

Nếu hiện tại mới có một phần các chức năng này, hãy hoàn thiện những phần còn thiếu.

---

# 11. OPENPROJECT — HOÀN THIỆN TƯƠNG TÁC AGENT

Project 6 phải hỗ trợ Agent thực hiện công việc thật:

- Đọc Task.
- Phân tích Task.
- Tạo Subtask.
- Cập nhật mô tả.
- Ghi comments.
- Giao việc.
- Theo dõi dependencies.
- Cập nhật tiến độ.
- Ghi blocker.
- Gắn GitHub links.
- Ghi nhận review/test artifacts.
- Theo dõi trạng thái delivery.

Tận dụng Native API hiện tại.

Không phải mọi mutation đều cần người dùng duyệt thủ công trong phạm vi demo đã được cho phép.

Tuy nhiên, vẫn giữ project context và identity chính xác.

**Project 5 phải giữ nguyên.**

Không đánh dấu toàn bộ WP #379 DONE chỉ vì một vài engineering unit hoàn thành.

---

# 12. GITHUB — HOÀN THIỆN SOURCE LIFECYCLE

Repository:

`Luim3141/mini-task-manager`

Hai PR hiện tại:

- PR #1: `codex/openclaw-create-list-persistence-v1` → `main`
- PR #2: `codex/openclaw-crud-search-web-v1` → branch PR #1

Đây là hai Pull Requests dạng stacked.

Yêu cầu:

1. Xác minh trạng thái GitHub thực tế.
2. Đối chiếu source đang chạy với exact Git revision.
3. Không mặc định code trên `main` đã có toàn bộ chức năng.
4. Không phát triển nhầm từ branch cũ.
5. Không tạo PR trùng lặp.
6. Hoàn thiện cơ chế quản lý branch, commit, PR và delivery artifacts.
7. Duy trì liên kết với WP #379.
8. Ghi nhận chính xác source revision đang được triển khai.

Chưa cần merge PR chỉ để phục vụ UAT.

Không force push hoặc reset làm mất lịch sử.

---

# 13. MINI TASK MANAGER — HOÀN THIỆN SẢN PHẨM

Ứng dụng hiện được báo cáo đã có:

- Create Task.
- List Tasks.
- Edit Task.
- Delete Task.
- Change Status.
- Search.
- Filter.
- SQLite persistence.
- Web UI.

Không viết lại những tính năng đã hoàn thành.

Hãy kiểm tra mức độ hoàn chỉnh của implementation và tích hợp.

Nếu còn chức năng được yêu cầu nhưng mới có API, chưa nối với UI hoặc còn hành vi chưa xử lý, hãy hoàn thiện.

Ưu tiên:

- Frontend/backend nhất quán.
- Trạng thái hiển thị chính xác.
- Chỉnh sửa/xóa/tìm kiếm/lọc vận hành đầy đủ.
- Thông báo lỗi rõ ràng.
- SQLite persistence đúng đường dẫn cấu hình.
- Ứng dụng chạy được sau restart.
- Không phụ thuộc phiên Codex đang mở.

Không tự mở rộng ứng dụng thành hệ thống SaaS phức tạp ngoài phạm vi WP #379.

---

# 14. HOÀN THIỆN AI CONTROL CENTER

Tận dụng giao diện QLDAPM hiện có.

Đối với Project 6, cần hoàn thiện trải nghiệm:

- Chọn Task.
- Xem engineering backlog.
- Chọn engineering unit.
- RUN ONCE.
- OFF.
- PAUSE.
- CANCEL.
- RESUME nếu được hỗ trợ.
- Xem Agent đang làm việc.
- Xem bước hiện tại.
- Xem nhiệm vụ đã hoàn tất.
- Xem nhiệm vụ còn lại.
- Xem progress.
- Xem lỗi/blocker.
- Xem GitHub commit/PR.
- Xem review findings.
- Xem QA evidence.
- Xem usage/quota khi có.
- Xem knowledge references.

Các nút điều khiển phải được kết nối đến backend thực tế.

Không tạo những nút hoặc trạng thái chỉ để trang trí.

Không cần xây dashboard mới nếu AI Control Center hiện tại có thể mở rộng.

---

# 15. TRIỂN KHAI LIÊN TỤC, KHÔNG DỪNG SAU MỘT FEATURE

Một mục tiêu quan trọng là tránh tình trạng:

- Agent hoàn thành một Task nhỏ.
- Các test PASS.
- Hệ thống báo READY_FOR_USER_UAT.
- Phần chức năng hoặc tích hợp còn lại chưa hoàn thiện.

Trong giai đoạn này, sau khi một engineering unit hoàn thành:

1. Cập nhật checkpoint.
2. Đối chiếu feature completeness matrix.
3. Chọn chức năng còn thiếu tiếp theo.
4. Tiếp tục triển khai.
5. Không gọi các model để kiểm tra lặp vô ích.
6. Không đánh dấu hệ thống hoàn tất sớm.

Bạn có thể chia công việc thành các engineering units để quản lý, nhưng không được tự dừng toàn bộ Phase 2 chỉ vì một unit PASS.

**Lưu ý:** `RUN ONCE` là hành vi sản phẩm khi người dùng vận hành, không phải giới hạn buộc Codex chỉ được triển khai một tính năng trong phiên lập trình hiện tại.

---

# 16. BẢO TOÀN HỆ THỐNG HIỆN CÓ

Tôi cho phép bạn tiếp tục:

- Sửa source.
- Tạo module.
- Cài dependency.
- Sửa config.
- Build.
- Deploy.
- Hoàn thiện UI.
- Tích hợp API.
- Sửa lỗi.

Không cần hỏi lại từng thao tác kỹ thuật thông thường.

Nhưng phải giữ:

- OpenProject Project 5.
- Dữ liệu QLDAPM MAIN.
- 16 workflow n8n.
- Second Brain.
- Qdrant.
- Knowledge SQLite.
- Existing AI features.
- Existing execution receipts.
- Existing rollback/handoff information.

Không reset DB.

Không xóa Docker volumes.

Không làm mất Git working tree.

Không tự tạo một hệ thống AI Gateway thứ hai thay cho Gateway hiện tại.

---

# 17. BẮT BUỘC DUY TRÌ GEMINI HANDOFF

Sau mỗi phần triển khai có ý nghĩa, cập nhật:

`docs/ai/engineering/HANDOFF_GEMINI_LATEST.md`

`docs/ai/engineering/IMPLEMENTATION_STATE.json`

`docs/ai/engineering/IMPLEMENTATION_JOURNAL.md`

`docs/ai/engineering/GEMINI_CONTINUE_PROMPT.md`

`docs/ai/engineering/OPERATIONS_RUNBOOK.md`

Đặc biệt cập nhật:

- Các chức năng COMPLETE.
- Các chức năng PARTIAL/MISSING.
- File đã sửa.
- Git status/commit.
- Runtime version.
- Deployment state.
- OpenClaw sessions/runs nếu đang hoạt động.
- Bugs hiện tại.
- Exact next implementation action.
- Các bước Gemini cần làm nếu tiếp quản.

Gemini phải có thể tiếp tục từ source/runtime thực tế mà không cần đọc lịch sử ChatGPT/Codex.

Không được để handoff chỉ chứa báo cáo các test PASS cũ trong khi source đã thay đổi.

---

# 18. ĐIỀU KIỆN DỪNG MỚI

**KHÔNG sử dụng `READY_FOR_USER_UAT` làm điều kiện dừng hiện tại.**

Chỉ xem xét kết thúc đợt triển khai khi:

1. Đã đối chiếu đầy đủ các yêu cầu Phase 2.
2. Các chức năng bắt buộc đều có implementation thực tế.
3. Những phần `PARTIAL/MISSING` đã được xử lý hoặc có blocker cụ thể.
4. Agent có đủ tool và skill cần thiết.
5. OpenClaw/Gemini integration hoàn chỉnh.
6. Supervisor có orchestration và durable handoff.
7. OpenProject/GitHub/Second Brain/n8n được kết nối đầy đủ.
8. AI Control Center có các điều khiển và trạng thái cần thiết.
9. Các chức năng ứng dụng Mini Task Manager được triển khai đầy đủ.
10. Source đang phục vụ và Git revisions được ghi nhận.
11. Có hướng dẫn vận hành và tài liệu bàn giao Gemini cập nhật.

Sau khi đủ chức năng, báo cáo:

`FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED`

Đây chỉ là **kết luận hoàn thành triển khai chức năng**, không phải chứng nhận UAT PASS hoặc production go-live.

Nếu còn blocker thực tế, báo đúng:

`FEATURE_IMPLEMENTATION_PARTIAL — BLOCKED`

Không báo hoàn thành khi còn tính năng bắt buộc chưa được triển khai.

---

# 19. CÁCH BÁO CÁO TRONG PHIÊN NÀY

Tập trung báo cáo kết quả triển khai:

- Đã hoàn thiện tính năng nào.
- Đã sửa hoặc bổ sung module nào.
- Còn thiếu tính năng nào.
- Đã deploy những thành phần nào.
- Có blocker thực tế nào.
- Next implementation action là gì.
- Handoff Gemini đã cập nhật ở đâu.

Không cần viết báo cáo kiểm thử dài.

Không cần yêu cầu tôi UAT.

Không cần hỏi tôi có muốn tiếp tục mỗi khi hoàn thành một module.

Nếu công việc còn trong phạm vi Phase 2 đã được cấp quyền, hãy chủ động tiếp tục.

---

# FINAL DIRECTIVE

**TIẾP TỤC LẬP TRÌNH.**

**TIẾP TỤC HOÀN THIỆN TOÀN BỘ CHỨC NĂNG.**

**KHÔNG CHUYỂN SANG UAT.**

**KHÔNG DỪNG CHỈ VÌ TEST PASS.**

**KHÔNG DÀNH PHẦN LỚN QUOTA CHO KIỂM THỬ LẶP LẠI.**

**KHÔNG VIẾT LẠI NHỮNG THÀNH PHẦN ĐÃ TỐT.**

Hãy sử dụng toàn bộ source, checkpoint và runtime hiện có để hoàn thiện kiến trúc đã chốt:

**OpenProject + QLDAPM Gateway/Supervisor + n8n + RAG/Second Brain + OpenClaw/Gemini API + Paperclip-inspired orchestration + Agency Agents personas + Superpowers skills + GitHub.**

Mọi chức năng bắt buộc của Phase 2 phải có implementation thực sự và được kết nối đúng vào hệ thống.

**BẮT ĐẦU TỪ FEATURE GAP ANALYSIS NGẮN GỌN, SAU ĐÓ TRIỂN KHAI LIÊN TỤC.**

**MAINTAIN GEMINI HANDOFF AT EVERY MEANINGFUL CHECKPOINT.**

**DO NOT STOP AT READY_FOR_USER_UAT.**