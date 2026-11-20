# Atlassian Artifacts — upload không hoàn tất

## 1. Yêu cầu và phạm vi

Ngày 2026-10-09, chủ dự án chọn “Tải lên Atlassian Artifacts” sau câu hỏi về tài liệu bootstrap.
Năm file được phép upload: AGENTS.md, JIRA_MCP_AUDIT.md, JIRA_CAPABILITIES.md, JIRA_OPERATIONS.md, SPRINT_REVIEW_TEMPLATE.md.
Checkpoint và backup cũ chỉ ở local. Không có đánh giá thành viên thực; không yêu cầu share cho ai khác. Không thay đổi gói hoặc phát sinh phí.

## 2. Trace thực tế qua MCP chính thức

| Bước | Tool/operation | Kết quả |
| --- | --- | --- |
| Discover upload | discover(query=create Artifacts upload) | Schema createArtifactsUpload → executeWrite; length byte + SHA-256 Base64 bắt buộc |
| Discover publish | discover(query=publish Artifact) | Schema publishArtifact → executeWrite; chỉ dùng sau upload thành công |
| Tính metadata local | PowerShell ReadAllBytes/SHA256 | AGENTS.md: 20099 byte; checksum n0KNCPJUWt46O+cuPwgBl4OwDC9l0FwUK6fh3DKRc+c= |
| Chuẩn bị upload lần 1 | executeWrite → createArtifactsUpload | cloudId UUID; length/checksum chính xác; HTTP 400, isError=true |
| Thử lại một lần theo schema | executeWrite → createArtifactsUpload | Dùng site URL được schema cho phép, giữ nguyên bytes/hash; cùng HTTP 400 |
| Kiểm tra sau lỗi | executeRead → listArtifacts | artifacts=[]; “No artifacts created by the current user were found.” |

Lỗi nguyên văn cả hai lần:
```json
{"error":true,"message":"Artifacts artifact_createContent request failed.","statusCode":400}
```

Không có pre-signed URL/completionPayload/contentId trả về. **Chưa upload bytes, chưa gọi publishArtifact, chưa có artifact link.** Dừng tại file đầu tiên; không lặp gọi cả năm file khi cùng lỗi. Không dùng browser/plugin/REST thay thế để che lỗi.
Không suy đoán lỗi là thiếu quyền hoặc phải trả phí; server không cung cấp lý do cụ thể. Đọc listArtifacts thành công chỉ chứng minh khả năng đọc, không chứng minh create hoạt động.

## 3. Kết quả và bước an toàn

Năm tài liệu vẫn đầy đủ trong D:\AI project\QLDAPM chat. Chức năng upload Artifacts **BLOCKED bởi HTTP 400 từ server**, không ảnh hưởng kết nối đọc Jira/QAG3.
Có thể kiểm tra lỗi dịch vụ/quyền với Atlassian bằng thông báo trên, rồi re-discover/retry có chủ đích khi có thay đổi hoặc người dùng yêu cầu; không cần gửi token/password và không mua gói để xử lý giả định.
Các lần ghi Artifacts thất bại không phải Jira issue/workflow write. Không có chia sẻ/publish assessment hoặc mutation Jira trong bootstrap.

## 4. Đối soát khi nhận lại xác nhận tải lên

Ngày 2026-10-09, xác minh lại bằng MCP chính thức: `atlassianUserInfo` trả đúng account đã ghi; `getAccessibleAtlassianResources` trả site `https://luimjiraqldapm.atlassian.net`, cloudId `560ef0cc-d24b-4613-98d3-d541afe8f32b`, có product Artifacts. `discover` xác nhận schema `listArtifacts`; `executeRead → listArtifacts(limit=20)` vẫn trả `artifacts=[]`, không có cursor hay artifact link.

Cả năm file local tồn tại và không rỗng. Chưa có bằng chứng dịch vụ hoặc đầu vào đã thay đổi, nên không gọi lại `createArtifactsUpload` sau hai lần HTTP 400 đã ghi ở mục 2. Xác nhận của người dùng vẫn được lưu là cho phép tải năm tài liệu này; không mở rộng thành quyền chia sẻ cho người khác, thay đổi Jira hoặc mua gói. Kết quả tải lên vẫn **CHƯA HOÀN TẤT**.
