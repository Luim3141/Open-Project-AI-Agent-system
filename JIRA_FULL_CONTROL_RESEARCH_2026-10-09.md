# Nghiên cứu điều khiển Jira qua MCP: khả năng và phương án triển khai

Ngày nghiên cứu: 2026-10-09. Site mục tiêu: luimjiraqldapm.atlassian.net; project QAG3. Ngân sách phát sinh: 0.

## 1. Kết luận

MCP chính thức không phải bản sao toàn bộ Jira REST API. Thiếu tool không đồng nghĩa thiếu API hoặc tài khoản thiếu quyền. Phương án đề xuất là giữ MCP Atlassian cho công việc thường ngày, bổ sung một MCP local nhỏ cho những API quản trị chính thức còn thiếu. Chỉ triển khai sau khi được duyệt; không thay thế hoặc mở rộng quyền của kết nối hiện có trong lượt nghiên cứu này.

Không có bằng chứng cho lời hứa “full chức năng” trên site này: quyền thực tế, gói sản phẩm, loại project và cơ chế xác thực vẫn ràng buộc mọi connector. Phương án mới không giải quyết tự động giới hạn Jira Free hoặc bảo đảm hard gate nghiệp vụ chưa được kiểm thử.

## 2. Vì sao MCP hiện tại thiếu thao tác?

Catalog Atlassian hiện công bố các tool quản trị project, đọc workflow, mở editor và cập nhật screen; chưa liệt kê tool mời người dùng, sửa project-role actors, publish workflow scheme hoặc CRUD automation. `getJiraWorkflowEditorLink` chỉ mở thay đổi điền sẵn, không áp dụng thay đổi. Nhóm `manage_jira` mặc định bị tắt; việc bật nhóm chỉ mở các tool thuộc catalog, không biến toàn bộ REST API thành tool. Tool còn phụ thuộc scope, xác thực và quyền tổ chức. [Catalog MCP chính thức](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).

Đối soát phiên trước đã đọc được QAG3 bằng MCP nhưng discovery chưa trả các thao tác trên. Đây không phải bằng chứng account đã bị HTTP 403, hoặc chắc chắn tổ chức đang tắt manage_jira. Lượt này không gọi lại Jira để xác minh quyền/gói.

## 3. Những API thực sự tồn tại

| Công việc | API / cách làm được tài liệu hóa | Điều kiện và giới hạn |
|---|---|---|
| Mời người dùng cấp tổ chức | `POST /admin/v2/orgs/{orgId}/users/invite` | API yêu cầu tổ chức có ít nhất một subscription trả phí; không chọn làm đường triển khai ngân sách 0. |
| Tạo người dùng Jira | `POST /rest/api/3/user` | Endpoint tương thích legacy; yêu cầu Jira admin và organization admin, có `products`. Không coi là thay thế chắc chắn cho luồng mời hiện đại. |
| Thêm người vào project role | `POST /rest/api/3/project/{key}/role/{id}` | Cần quyền quản trị phù hợp và accountId. `POST` bổ sung; `PUT` thay toàn bộ actors, không dùng làm mặc định. Free không cho gán role. |
| Tạo/cập nhật workflow | `/rest/api/3/workflows/create`, `/workflows/update` và endpoint validation tương ứng | Kiểm tra capabilities, quyền, phiên bản và rule khả dụng trước; không tự suy ra mọi validator đều được hỗ trợ. |
| Ánh xạ và publish workflow scheme | Draft issue-type mappings; `POST /rest/api/3/workflowscheme/{id}/draft/publish` | Có `validateOnly`; publish bất đồng bộ, cần theo dõi task tới kết quả cuối, không coi 303 là hoàn tất. |
| Gán scheme vào project | `PUT /rest/api/3/workflowscheme/project` | Chỉ classic/company-managed và project không có issue; không xóa issue để ép điều kiện này. |
| Quản lý automation | Automation public REST: tạo, đọc, cập nhật rule; đổi state/scope | API hỗ trợ API token, không hỗ trợ OAuth 2.0 apps/Forge ở các resource đã khảo sát; cần xác thực riêng phù hợp. |

Nguồn cho bảng: [Organization users](https://developer.atlassian.com/cloud/admin/organization/rest/api-group-users/), [Jira users](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/), [Project role actors](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-role-actors/), [Workflows](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflows/), [Workflow scheme drafts](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-scheme-drafts/), [Project associations](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-scheme-project-associations/), [Automation rules](https://developer.atlassian.com/cloud/automation/rest/api-group-rule-management/) và [Automation authentication](https://developer.atlassian.com/cloud/automation/security/authentication/).

“Publish” ở đây là workflow/workflow scheme, không phải release một project version; đó là những thao tác khác nhau.

## 4. Giới hạn miễn phí không được đánh tráo

Nếu site thật đang dùng Free, không thể gán project role hoặc tùy chỉnh permission scheme theo mô hình của gói trả phí. Nhãn BA/PM/BE/FE/Tester và assignee vẫn là phân công nghiệp vụ, không phải phân quyền bảo mật. MCP không thể mở khóa tính năng trả phí. Gói thực tế trên site chưa được xác minh trong lượt nghiên cứu. [Atlassian: giới hạn quyền trên Free](https://support.atlassian.com/jira-cloud-administration/docs/permissions-and-issue-level-security-in-free-plans/).

Đối với mời thành viên, chỉ cân nhắc endpoint Jira legacy khi xác minh hỗ trợ và quyền thực tế; nếu không đáp ứng, dùng giao diện quản trị sau khi người dùng cho phép, giữ trong hạn mức miễn phí, không trial/upgrade. Không lấy session cookie hoặc gọi endpoint nội bộ không tài liệu hóa để lách điều kiện API.

## 5. Người khác triển khai trên GitHub như thế nào?

Đã đối chiếu handlers/methods, không chỉ README. Bằng chứng commit và license nằm trong [báo cáo GitHub](./JIRA_GITHUB_CAPABILITIES_RESEARCH_2026-10-09.md).

| Candidate | Code đã có | Kết luận cho dự án |
|---|---|---|
| sooperset/mcp-atlassian | Tool tác nghiệp issue/agile; user lookup/assignable search. Không thấy handler cho các gap admin đang cần trong server đã kiểm tra. | Không đổi sang server này chỉ để giải quyết invite/role/publish. [Server source](https://github.com/sooperset/mcp-atlassian/blob/0a5d2427144d72f5aade07d4fabd385421cec401/src/mcp_atlassian/servers/jira.py). |
| atlassian-api/atlassian-python-api | SDK có role actors, draft mappings, publish scheme; không phải MCP sẵn dùng. | Có thể tái sử dụng sau review nếu helper hiện có chưa đủ; kiểm tra JiraCloud, payload mới và async handling trước. [Core methods](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/atlassian/jira/core_methods.py). |
| pycontribs/jira | SDK có user/role legacy; Cloud compatibility cho các thao tác này chưa chứng minh, không thấy dedicated publish/mapping handlers trong client đã kiểm tra. | Không chọn làm nền quản trị Cloud mới. [Client source](https://github.com/pycontribs/jira/blob/bf7306b8b3905c91f97401eaae61d04827e1c309/jira/client.py). |
| windoze95/gojira-mcp | MCP có workflow create/update, draft publish/polling và automation handlers, nhưng thiếu một số role/mapping writes trong source kiểm tra. Package ghi UNLICENSED. | Bằng chứng mô hình MCP bọc API có thực; chỉ tham khảo, chưa đề xuất cài do license/gaps chưa giải quyết. [Workflow handlers](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/tools/defs/workflows.ts), [Package](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/package.json). |

Mẫu chung quan sát được: tool MCP có schema gọi SDK/REST ở phía server, không phải MCP tự tạo thêm quyền Jira. Có code không đồng nghĩa endpoint đã hoạt động trên site của người dùng. Không candidate nào trong phạm vi kiểm tra được chứng minh đáp ứng toàn bộ yêu cầu này.

## 6. Thiết kế đề xuất: official MCP + local admin MCP hẹp

Đây là kiến trúc đề xuất, chưa cài đặt:

- MCP Atlassian hiện có: issue, assignee, comment, sprint, đọc số liệu và bot giám sát.
- MCP local qua stdio: chỉ các tool quản trị còn thiếu đã xác minh API. Không mở server public, không cần Docker/tunnel.
- Mỗi tool có schema riêng và target cố định; không cấp tool gọi URL bất kỳ, chạy Python hoặc shell tùy ý.
- Giới hạn site và project QAG3; workflow/scheme chỉ cho phép ID đã đối soát, không đụng KAN/SAM1 hoặc scheme dùng chung.
- Credential riêng theo yêu cầu từng API, lưu qua credential store/môi trường an toàn. Không tái sử dụng token MCP OAuth một cách suy đoán; không lưu secret trong repo/chat/log.
- Trước ghi: đọc cấu hình hiện tại, hiển thị diff, xác minh quyền và ảnh hưởng; phê duyệt các thay đổi quản trị. Sau ghi: đọc lại, kiểm tra kết quả bất đồng bộ và lưu audit không chứa secret.
- Chống lặp: tìm đối tượng đã có trước khi tạo; không retry mù sau timeout; đối soát trạng thái rồi mới quyết định.
- Automation tạo ở trạng thái disabled, giới hạn scope QAG3, xem lại rule/actor trước khi enable. Automation phản ứng sau sự kiện không thay cho validator chặn chuyển trạng thái.

Tận dụng helper/credential store hiện có nếu phù hợp; không dựng lại toàn bộ client Jira. Tên tool bổ sung là thiết kế mới, không phải tool Atlassian đã có sẵn.

## 7. Trình tự triển khai và tiêu chí nghiệm thu

1. Được duyệt bổ sung tích hợp ngoài official MCP; xem trước quyền, chi phí và rollback. Không sửa AGENTS.md để tự cấp quyền cho đề xuất này.
2. Kiểm tra account/site/cloudId, organization-admin/Jira-admin thực tế, gói và số người dùng; không suy ra quyền từ câu “full quyền”.
3. Bổ sung từng tool còn thiếu, bắt đầu bằng read/validation. Kiểm tra âm tính: sai site/project, thiếu quyền, timeout, lặp request, shared scheme đều không gây ghi ngoài phạm vi.
4. Đọc lại QAG3 có còn rỗng không; cấu hình ba workflow và scheme trước WBS nếu đáp ứng điều kiện API. Không coi cấu hình trước đây là trạng thái hiện tại.
5. Hoàn tất hard gates đã duyệt, nghiệm thu các test trong kế hoạch gốc: Epic rỗng/chưa xong Task, non-PM, reopen, scope change, parent change, sự kiện đồng thời, snapshot Sprint. Chưa đạt thì không import toàn bộ WBS hoặc báo workflow hoàn tất.
6. Mời đúng thành viên, đối soát accountId và quyền truy cập; không cấp site/org admin cho cả nhóm. Nhập WBS draft sau khi được duyệt và gates đạt; đọc lại parent/assignee/checklist.
7. Cập nhật architecture.md và runbook theo trạng thái đã triển khai; giữ bot giám sát đọc riêng, không cho AI tự sửa quyền hoặc chấm điểm người thật khi thiếu baseline.

Rollback: disable tích hợp local/revoke credential riêng; restore cấu hình QAG3 đã chụp nếu an toàn và được duyệt, disable rule vừa bổ sung. Không xóa project, issue hoặc tài khoản làm rollback; migration status cần phương án riêng trước publish.

## 8. Bằng chứng và giới hạn nghiên cứu

Lượt này đọc tài liệu công khai và source GitHub; không cài/chạy code bên thứ ba hoặc thực hiện API quản trị trên site. API được tài liệu hóa không tương đương LIVE TESTED. Source có method không bảo đảm endpoint phù hợp Jira Cloud hiện tại. Xem báo cáo kiểm tra GitHub riêng để chọn phần có thể tái sử dụng; không chấp nhận quảng cáo “full Jira” khi chưa có tool và test tương ứng.
