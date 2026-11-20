# QLDAPM — ngôn ngữ miền

QLDAPM quản lý công việc và hỗ trợ nhóm năm vai trò bằng phân tích, đề xuất và quy trình tự động nội bộ.

## Language

**Công việc nghiệp vụ**:
Một hạng mục được nhóm quản lý theo phân cấp Epic, Task và Subtask. Đây là đối tượng nghiệp vụ, khác một lượt xử lý của agent.
_Avoid_: Gọi AgentTask là Task nghiệp vụ.

**Actor nghiệp vụ**:
Thành viên có danh tính và quyền trong dự án, gắn với vai trò PM, BA, FE, BE hoặc QA.
_Avoid_: Dùng vai trò agent hay owner workflow để suy ra quyền của thành viên.

**Tác vụ agent (AgentTask)**:
Một yêu cầu phân tích có chủ thể, dự án, hội thoại và tham chiếu nguồn xác định.
_Avoid_: Đồng nhất với OpenProject ID hoặc Source ID của công việc nghiệp vụ.

**Lượt agent (AgentRun)**:
Một lần xử lý cụ thể của tác vụ agent, có tiến độ, kết quả và dấu vết riêng.
_Avoid_: Xem việc xếp hàng hay tạo tác vụ là đã thực thi thành công.

**Owner workflow**:
Quản trị viên vận hành các quy trình tự động nội bộ. Đây là vai trò vận hành, khác PM trong nghiệp vụ.
_Avoid_: Owner n8n đồng nghĩa PM hoặc cả năm thành viên đều là người quản trị workflow.

**Machine trigger**:
Yêu cầu từ quy trình tự động có nguồn gốc và phạm vi riêng, khác yêu cầu trực tiếp của một thành viên.
_Avoid_: Gọi machine trigger là một lần con người phê duyệt.

**Xác nhận đề xuất**:
Quyết định cho một thay đổi cụ thể sau khi xem preview và phạm vi hiện tại.
_Avoid_: Xem lịch chạy, kết quả agent hoặc tham chiếu hội thoại cũ là sự phê duyệt.
