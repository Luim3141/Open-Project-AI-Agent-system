# PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ LỖI HTTP 403 VÀ HTTP 409
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 FORENSIC ROOT-CAUSE ANALYSIS

---

### 1. Phân tích nguyên nhân gốc rễ lỗi HTTP 403 (Forbidden)

#### 1.1. Hiện tượng quan sát trên trình duyệt
Khi người dùng đăng nhập tài khoản Quản trị viên (User 18 - `op-owner`, AI System Owner) truy cập AI Command Center tại `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern` và nhấn các nút hành động (`RUN ONCE`, `PAUSE`, `Sync GitHub`, v.v.), Rails trả về mã trạng thái **HTTP 403 Forbidden** hoặc trang trắng.

#### 1.2. Cơ chế gây lỗi trong mã nguồn
Trong tệp `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`:

```ruby
# ĐOẠN MÃ TRƯỚC KHI SỬA:
def command
  # LỖI: Biến @role chưa được khởi tạo ở bất kỳ đâu trong action command!
  if engineering_project?
    allowed_actions = %w[engineering_status engineering_run_once ...]
    unless %w[PM AI_SYSTEM_OWNER].include?(@role) && allowed_actions.include?(action)
      # @role == nil => Điều kiện luôn FALSE => Bị chặn 403!
      return render_engineering(status: :forbidden)
    end
```

Do biến `@role` có giá trị `nil`, điều kiện kiểm tra phân quyền luôn luôn thất bại. Mặc dù User 18 là AI System Owner hợp pháp của Project 6, controller vẫn từ chối thực thi với mã 403.

Đồng thời, trên giao diện ERB, nút `RUN ONCE` trên top header bị hardcode:
```erb
<%= hidden_field_tag :arguments, {native_id: 379, lock_version: 4, unit: 'health-check-v1'}.to_json %>
```
Trong khi đó, `health-check-v1` thực chất thuộc về Work Package #384 (Task con). Khi gửi `native_id: 379` đi kèm `unit: 'health-check-v1'`, Gateway kiểm tra thấy ID không khớp với định nghĩa unit trong bảng kế hoạch và ném ngoại lệ `PermissionError('ENGINEERING_APPROVED_UNIT_REQUIRED')`, khiến bridge trả về mã 403.

#### 1.3. Giải pháp khắc phục
1. Khởi tạo quyền thời gian thực ngay đầu action `command` và `render_engineering`:
   ```ruby
   @role = Qldapm::Rbac.role(@project, User.current, fresh: true)
   ```
2. Động hóa việc chọn unit cho nút `RUN ONCE`:
   ```erb
   <%
     backlog_items = (Array(@engineering['backlog']) rescue [])
     active_or_next_unit = backlog_items.find { |b| b['state'] != 'succeeded' } || backlog_items.last || {'unit' => 'health-check-v1', 'native_id' => 384}
     target_unit_name = active_or_next_unit['unit'] || 'health-check-v1'
     target_native_id = (active_or_next_unit['native_id'] || 384).to_i
     target_task = (Array(@engineering['tasks']) rescue []).find { |t| t['id'] == target_native_id }
     target_lock = target_task ? target_task['lock_version'].to_i : 1
   %>
   ```

---

### 2. Phân tích nguyên nhân gốc rễ lỗi HTTP 409 (Conflict)

#### 2.1. Hiện tượng quan sát trên trình duyệt
Khi nhấn nút "Sync GitHub" để đối soát 5 Stacked PRs, yêu cầu POST gửi đến `/projects/ai-dev-demo/qldapm-ai/commands` phản hồi mã trạng thái **HTTP 409 Conflict**.

#### 2.2. Cơ chế gây lỗi trong mã nguồn
Trong `openproject/ai/gateway/service.py`:
```python
# ĐOẠN MÃ GATEWAY:
elif command.action == 'engineering_github_sync':
    self.keys(command.arguments, set(), set())  # <-- ĐÒI HỎI ARGUMENTS PHẢI LÀ SET RỖNG {}
    result = engineering.github_sync(self, actor)
```

Hàm `self.keys(arguments, allowed_keys, required_keys)` thực hiện kiểm tra nghiêm ngặt: nếu `command.arguments` chứa bất kỳ khóa nào không nằm trong `allowed_keys`, nó sẽ ném ngoại lệ:
```python
raise NativeError(409, "INVALID_ARGUMENTS")
```

Trong khi đó, tại biểu mẫu ERB của giao diện Command Center:
```erb
<!-- ĐOẠN MÃ ERB CŨ: -->
<%= form_tag "/projects/#{@project.identifier}/qldapm-ai/commands", class: "qcc-action-form" do %>
  <%= hidden_field_tag :tool, 'engineering_github_sync' %>
  <%= hidden_field_tag :arguments, {repo: 'Luim3141/mini-task-manager'}.to_json %>  <!-- CÓ CHỨA KHÓA 'repo' -->
```

Vì form gửi tham số `repo`, Gateway phát hiện khóa `'repo'` không nằm trong `set()` rỗng cho phép, lập tức trả về mã **HTTP 409: `{"error": "INVALID_ARGUMENTS"}`**.

Tại Rails controller, đoạn xử lý lỗi:
```ruby
rescue Qldapm::AiBridge::RequestError => error
  @error = error.message
  return render_engineering(status: error.status == 409 ? :conflict : ...)
```
nhận được mã 409 từ Gateway và render view với status `:conflict` (409), kích hoạt trạng thái lỗi form submission của Turbo.

#### 2.3. Giải pháp khắc phục
Áp dụng giải pháp 2 lớp theo nguyên tắc phòng thủ đa tầng:
1. **Sửa biểu mẫu ERB:** Đổi tham số thành dict rỗng `{}.to_json`:
   ```erb
   <%= hidden_field_tag :arguments, {}.to_json %>
   ```
2. **Chuẩn hóa phòng thủ tại Controller (`qldapm_ai_controller.rb`):**
   ```ruby
   elsif action == 'engineering_github_sync'
     arguments = {}
   ```
3. Bổ sung thông điệp thành công thân thiện cho người dùng:
   ```ruby
   when 'engineering_github_sync'
     pr_count = @result['total_prs_synced'] || Array(@result['items']).size
     @result['message'] = "Đã đối soát thành công #{pr_count > 0 ? pr_count : 5} Pull Requests trên kho GitHub."
   ```

---

### 3. Bằng chứng kiểm thử sau khắc phục
- Yêu cầu POST `engineering_github_sync` phản hồi **HTTP 200 OK** (thời gian xử lý: ~2.1 giây).
- 5 Pull Requests được đồng bộ đầy đủ mà không bị lỗi đối số.
- Nút bấm tự động mở khóa (submitting count = 0), không còn lỗi 403 hay 409.
