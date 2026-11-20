# QAG3 rollout kiểm tra tiếp tục ngày 09/10/2026

## Kết quả thực tế

- Official MCP `atlassianUserInfo` và `getAccessibleAtlassianResources` xác thực owner `712020:0d04982c-00bf-46af-b3a7-446d0f44edfb`, site `https://luimjiraqldapm.atlassian.net`, cloudId `560ef0cc-d24b-4613-98d3-d541afe8f32b`. `getJiraIssue(QAG3-2)` trả To Do; response chỉ có status, không suy các field khác đã được đọc đầy đủ.
- Supplemental `api_preflight`: ADMINISTER=true, ADMINISTER_PROJECTS=false. Không suy toàn bộ thao tác quản trị từ các boolean này.
- `inspect_scheme`: QAG3/10002 vẫn gắn scheme10003, không phải10004.
- `inspect_automation`: rules=[], readComplete=true. A01–A05 chưa tồn tại.
- `preview_scheme(associate_scheme,10004)` bị từ chối `PROJECT_NOT_VERIFIED_EMPTY: no deletion or migration attempted`. Không gọi apply_change.
- `inspect_workflow(epic)` trả version4, khác checkpoint version3. Layout hiện hành phải được giữ khi lập preview mới; không phục hồi cấu hình cũ một cách tự động. Accept Epic/Cancel/Restore vẫn không có conditions/validators, Resolution actions còn được giữ. Forge/connect rule catalog rỗng.
- Không ghi Jira, migrate issue, tạo rule, cài app, chạy transition E2E hoặc khởi động lại giám sát trong lượt đối soát này. Không sửa hoặc giả rollout-evidence.

## Chặn kỹ thuật đã xác minh

1. Endpoint đang dùng `PUT /rest/api/3/workflowscheme/project` chỉ gắn scheme khi project không có issue. Đây không chỉ là guard local. QAG3 có WBS đã nhập; phải dùng quy trình migration phù hợp, không xóa/chuyển issue ra ngoài để làm project rỗng. [Atlassian API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-scheme-project-associations/).
2. Gate native đang thấy cho child là kiểm tra Subtask, chưa chứng minh kiểm tra mọi Task của Epic hoặc Epic rỗng. Automation trả lại trạng thái sau khi Done không đáp ứng hard gate trước nghiệm thu.
3. Forge có module workflow validator dùng expression, là ứng viên bổ sung server-side. Chưa cài, chưa kiểm thử visibility/concurrency/giới hạn expression trên site; chưa thể nói đáp ứng đầy đủ. [Forge validator](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/).
4. Forge có allowance miễn phí và billing khi vượt ngưỡng, không được coi là mặc nhiên 0 đồng. Không cài/bật billing trước khi xác minh đường triển khai đáp ứng budget0 và được duyệt quyền cụ thể. [Forge pricing](https://developer.atlassian.com/platform/forge/forge-platform-pricing/).
5. Gói Free không cho tùy chỉnh project role/permission scheme; PM nghiệp vụ không tự trở thành security role. Cần điều kiện chuyển trạng thái nhận diện đúng người thực hiện nếu native hỗ trợ, hoặc validator được duyệt. [Atlassian roles](https://support.atlassian.com/jira-cloud-administration/docs/how-to-use-space-roles/).

## Lô triển khai đề xuất chưa thực hiện

### Gate trước rollout

- Preview trên phiên bản hiện hành, giữ layout/cạnh/Resolution đã lưu. Owner BA-PM và PM là hai tài khoản được duyệt nghiệm thu; không dùng Assignee để thay người thực hiện.
- Xác định field có cấu trúc cho Scope approval/version, Change reason, Lead review, Retest result, BA acceptance, PM approval và Test deployment evidence. Không dùng checklist Markdown như bằng chứng validator đã hoạt động.
- Validator phải đọc child hiện thời, từ chối Epic rỗng/Task chưa Done, checklist thiếu/lỗi chưa retest và lý do rỗng. Không chứng minh nguyên tử chỉ bằng việc có expression; concurrency phải được nghiệm thu riêng.
- Nếu cần app: trình scopes, dữ liệu đọc, điều kiện chi phí0, cách gỡ và tác động khi gỡ; xin approval trước khi đăng ký/cài. Không public endpoint, Docker, addon trả phí hoặc trial.

### Migration và kiểm thử

- Thu snapshot đầy đủ hiện hành của toàn bộ issue, Parent, Assignee, status, Resolution và cấu hình, phân trang tới isLast. Không dùng readback tháng trước thay snapshot trước migration.
- Mapping dự kiến To Do10008→NEW10010, In Progress3→3, Done10009→10009 cho cả3type; nếu thấy status khác thì dừng để bổ sung mapping. Chỉ chuyển trạng thái tương đương, không đánh dấu công việc Done.
- Cần quy trình staged được duyệt: validation gate trước activation kiểm thử, sample E2E sau activation, rollout đối soát toàn bộ sau E2E. Không yêu cầu T23 import lại329issue hoặc ghi tất cả test PASS trước khi có workflow hoạt động.
- Sample test phải được preview số lượng/type/assignee/labels; tách khỏi WBS và hiệu suất. Non-PM test dùng phiên người thật được cho phép, không impersonate.
- Khôi phục giữ key/Parent/Assignee và lịch sử; tắt rule mới trước khi restore mapping đã duyệt. Không xóa project/issue để rollback.

### Automation

- A01 bắt đầu Epic; A02 đưa Epic tới Review khi toàn bộ Task Done; A03 mở lại do Task mới/mở lại; A04 đối soát cả Parent cũ và mới; A05 thông báo reviewer một lần cho mỗi event đi vào bước review.
- Chuẩn bị bằng template native hoặc schema API đã xác minh; tạo disabled, readback components/actor/scope rồi mới enable từng rule sau approval. MCP local hiện không có create/edit/enable template, không đoán payload opaque.
- Không tự Epic Done, không sửa KAN/SAM1, không dùng Automation thay hard gate. Replay/concurrency/quota phải được thử thật, không hứa exactly-once từ status check.

### Bot đánh giá

- Giữ giám sát tạm dừng. Hoàn thiện báo cáo tiến độ và readiness riêng tư, không tự resume scheduler.
- Thiếu Sprint baseline/capacity/changelog/AC-test-review evidence thì `INSUFFICIENT EVIDENCE`, không điểm tổng hoặc xếp hạng. Không xem count329issue hay status Done là nghiệm thu code.
- Gemini optional vẫn tắt khi chưa có key mới và xác nhận Free Tier chưa billing; dùng nhận định Codex/local. Không gửi PII hoặc đánh giá nhân sự ra Gemini.

## Quyết định cần chủ dự án

Cho phép bổ sung app validator riêng chỉ sau khi xác minh chi phí0, preview scopes/data/rollback và được duyệt lô cài cụ thể; hoặc chấp nhận rằng chưa thể đáp ứng hard gate Epic với capability native đã thấy. Không tự chọn hạ yêu cầu hoặc chuyển gói.
