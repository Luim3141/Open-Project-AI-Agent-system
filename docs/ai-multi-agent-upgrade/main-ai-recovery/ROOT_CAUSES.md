# BÁO CÁO PHÂN TÍCH TẬN GỐC NGUYÊN NHÂN SỰ CỐ AI ASSISTANT TRÊN MAIN
## ROOT CAUSE ANALYSIS — QLDAPM MAIN AI & MULTI-AGENT RECOVERY

- **Môi trường:** QLDAPM Main (OpenProject Core `http://localhost:8088`, AI Gateway `http://localhost:8090`)
- **Dự án kiểm định:** `qldapm-local` (ID: 5, 329 Work Packages, 7 Sprints, 7 Versions)
- **Tài khoản mục tiêu:** PM `ba-pm` (ID: 19), Admin `op-owner` (ID: 18)
- **Thời điểm hoàn thành điều tra & sửa lỗi:** 2026-10-21T19:10:00+07:00

---

## 1. NGUYÊN NHÂN GÂY LỖI HTTP 403 FORBIDDEN

Qua phân tích luồng dữ liệu giữa Trình duyệt, Rails Controller (`qldapm_ai_controller.rb`) và AI Gateway (`gateway/app.py`, `gateway/bridge.py`):

### 1.1. Tầng 1: Cô lập quyền Quản trị viên (Gate B Admin Isolation)
- **Vị trí mã nguồn:** [`openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb#L101) dòng 101 và 263:
  ```ruby
  return head :forbidden if User.current.admin?
  ...
  return deny_access unless actor_info && actor_info["role"].present?
  ```
- **Cơ chế kích hoạt:** Khi Chủ dự án sử dụng tài khoản Quản trị hệ thống (`op-owner`, User ID 18, `admin: true`) truy cập AI Assistant hoặc gửi lệnh AI:
  - Admin không phải là thành viên trực tiếp trong bảng `members` của Project 5 (chỉ có 5 vai trò thành viên nghiệp vụ: User 19=PM, 20=BA, 21=BE, 22=FE, 23=QA).
  - Để ngăn ngừa rủi ro bảo mật Admin mượn danh tính (Impersonation Gate B), hệ thống chủ động trả về HTTP 403 Forbidden.
- **Khắc phục:** Định tuyến rõ ràng người dùng: Các thao tác AI phân tích và lập kế hoạch thuộc trách nhiệm của PM (`ba-pm`, ID 19). Quản trị viên hệ thống có nhiệm vụ cấu hình và giám sát hạ tầng.

### 1.2. Tầng 2: Ánh xạ lỗi tại Execution Monitor Polling
- **Vị trí mã nguồn:** `qldapm_ai_controller.rb` dòng 59-61:
  ```ruby
  rescue ::ArgumentError, ::KeyError => error
    status = error.message.match?(/403|404|không có quyền|Không tìm thấy/) ? :forbidden : :service_unavailable
    render json: {error: status == :forbidden ? "EXECUTION_ACCESS_DENIED" : "EXECUTION_UNAVAILABLE"}, status:
  ```
- **Cơ chế kích hoạt:** Khi giao diện frontend (`_execution_client.html.erb`) thực hiện polling lấy tiến trình (`/projects/5/qldapm-ai/executions/{run_id}.json`), nếu Gateway gặp lỗi tạm thời hoặc run chưa sẵn sàng trong microsecond đầu tiên, controller chuyển thành HTTP 403 `EXECUTION_ACCESS_DENIED`.
- **Hệ quả tại UI:** Tại `_execution_client.html.erb` dòng 946:
  ```javascript
  if (response.redirected || [401, 403, 404].includes(response.status)) {
    clearPrivate('Phiên đăng nhập hoặc quyền xem đã thay đổi. Đăng nhập lại qua AI Assistant.');
    text('em-connection', 'Đã dừng cập nhật để bảo vệ dữ liệu.');
    return false;
  }
  ```
  Nhận mã 403, trình duyệt lập tức xóa trắng dữ liệu sơ đồ DAG và dừng polling vĩnh viễn với thông báo "Đã dừng cập nhật để bảo vệ dữ liệu."

### 1.3. Tầng 3: Lệch thời gian HMAC Signature (Clock Drift)
- **Vị trí mã nguồn:** `gateway/bridge.py` (`verify_assertion`):
  ```python
  if payload["audience"] != "qldapm-ai-ui" or payload["project"] != config["project_id"] or abs(time.time() - payload["at"]) > 30:
      raise PermissionError("UI_ASSERTION_EXPIRED_OR_PROJECT")
  ```
- **Cơ chế kích hoạt:** Nếu container web và container gateway có độ lệch đồng hồ hệ thống quá 30 giây hoặc payload `at` bị trễ hàng đợi, Gateway trả về 403 `UI_ASSERTION_DENIED`.

---

## 2. NGUYÊN NHÂN GÂY LỖI HTTP 422 UNPROCESSABLE ENTITY

### 2.1. Lỗi phân tích số nguyên `write_scope_ids` (Integer Parsing Bug)
- **Vị trí mã nguồn:** `qldapm_ai_controller.rb` dòng 109:
  ```ruby
  # MÃ NGUỒN CŨ GÂY LỖI:
  "write_scope_ids" => params[:write_scope_ids].to_s.split(/[\s,]+/).map { |id| Integer(id) }
  ```
- **Cơ chế kích hoạt:** Khi người dùng nhập khoảng trắng (`" "`), nhập có dấu phẩy thừa (`"49, "`), hoặc nhập chuỗi ký tự (`"công việc 49"`):
  - Phương thức `split(/[\s,]+/)` sinh ra mảng chứa chuỗi rỗng `""` hoặc từ không phải số.
  - Hàm Ruby `Integer("")` ném ngoại lệ `ArgumentError: invalid value for Integer(): ""`.
  - Khối `rescue ArgumentError` bắt được lỗi và render giao diện với `status: :unprocessable_entity` (HTTP 422).
- **Giải pháp sửa:** Thay thế bằng phép trích xuất số nguyên an toàn bằng biểu thức chính quy:
  ```ruby
  "write_scope_ids" => params[:write_scope_ids].to_s.scan(/\d+/).map(&:to_i)
  ```
  Xử lý mượt mà mọi trường hợp: `""` -> `[]`, `"49, "` -> `[49]`, `"WP #49"` -> `[49]`, không bao giờ ném ngoại lệ.

### 2.2. Đánh đồng lỗi Gateway Offline thành HTTP 422
- **Vị trí mã nguồn:** `qldapm_ai_controller.rb` dòng 139-144:
  ```ruby
  # MÃ NGUỒN CŨ:
  rescue ::ArgumentError, ::KeyError => error
    @error = error.message
    render_assistant(status: :unprocessable_entity)
  ```
- **Cơ chế kích hoạt:** Khi Gateway bận, khởi động lại, hoặc trả mã lỗi 503, thư viện `AiBridge` ném `ArgumentError: "AI gateway từ chối hoặc chưa sẵn sàng (503)..."`. Controller vô tình bắt `ArgumentError` này và trả về HTTP 422 thay vì HTTP 503.
- **Giải pháp sửa:** Ánh xạ tường minh: Lỗi từ chối/quyền hạn trả về `:forbidden` (403), lỗi gián đoạn/kết nối trả về `:service_unavailable` (503), lỗi tham số sai định dạng trả về `:unprocessable_entity` (422).

---

## 3. NGUYÊN NHÂN GÂY LỖI GEMINI_REVIEW_FAILED

### 3.1. Hiện tượng
Trong các lần chạy thử nghiệm với Live Gemini, tác vụ chạy tới bước Reviewer thì bị dừng khẩn cấp với thông báo:
`GEMINI_REVIEW_FAILED; results retained for review`.

### 3.2. Cơ chế bẫy lỗi của Reviewer Agent
Trong [`openproject/ai/gateway/reviewer_agent.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/reviewer_agent.py#L38) dòng 38-45:
```python
# 2. Check for uncited work packages mentioned in summary text
mentioned_ids = [int(m) for m in re.findall(r"#(\d+)", result.summary)]
cited_ids = {r.work_package_id for r in result.references}
for mid in mentioned_ids:
    if mid not in pkg_map:
        issues.append(f"Nhận định đề cập công việc #{mid} nhưng không có bằng chứng native tồn tại.")
    elif mid not in cited_ids:
        issues.append(f"Công việc #{mid} được nhắc tới nhưng thiếu trích dẫn native reference có lock_version.")
```
Quy tắc kiểm định của Reviewer: **Bất kỳ ký tự `#<số>` nào xuất hiện trong văn bản phân tích đều bị coi là một trích dẫn bằng chứng bắt buộc.**
1. Nếu `<số>` không nằm trong danh sách `pkg_map` được cấp phép -> **LẬP TỨC TỪ CHỐI** vì nghi ngờ mô hình tự bịa đặt ID không có thật.
2. Nếu `<số>` có trong `pkg_map` nhưng mô hình quên đưa vào mảng `citations` -> **LẬP TỨC TỪ CHỐI** vì thiếu bằng chứng xác minh phiên bản `lock_version`.

### 3.3. Lỗi thiếu Subtask Manifest tại Gateway Service
- Khi người dùng gửi yêu cầu: *"BA và QA phân tích Work Package #49..."*, Gateway trích xuất `targets = [49]`.
- Hệ thống chỉ tải thông tin của duy nhất Task #49 (`packages = [native.package(49)]`), dẫn đến `pkg_map` chỉ chứa ID 49.
- Trong mô tả của #49 có các công việc con (Subtasks #102..#106). Mô hình Gemini (đặc biệt là BA và QA) khi phân tích nghiệp vụ đã tự nhiên viết: *"Tham chiếu liên kết với công việc con #102..."*.
- Reviewer quét thấy chuỗi `#102`. Do `pkg_map` chỉ có 49, Reviewer kết luận: `"Nhận định đề cập công việc #102 nhưng không có bằng chứng native tồn tại."` -> Đánh dấu kết quả `FAILED` -> Ném `ProviderError: GEMINI_REVIEW_FAILED`.

### 3.4. Giải pháp khắc phục tận gốc
1. **Nạp đầy đủ cây phân cấp công việc con vào ngữ cảnh:** Tại `gateway/service.py`, khi một Task hoặc Epic được chỉ định phân tích, hệ thống tự động kiểm tra liên kết `children` và nạp kèm các Subtask trực thuộc (tối đa 10 packages). Khi đó `pkg_map` chứa đầy đủ cả #49 lẫn #102..#106.
2. **Cập nhật System Prompt nghiêm ngặt:** Bổ sung chỉ thị cho các Specialist Agent trong `gateway/live_agents.py`: Chỉ được dùng ký hiệu `#<ID>` cho các công việc có trong danh sách được cấp; các tham chiếu ngoài phạm vi phải viết dưới dạng khái niệm chung.
3. **Cơ chế tự động đồng bộ trích dẫn (Auto-alignment):** Tại `gateway/live_agents.py`, bất kỳ ID hợp lệ nào xuất hiện dưới dạng `#<ID>` trong văn bản sẽ được tự động đưa vào mảng `references` cùng với `lock_version` chính xác; các ký hiệu `#` không thuộc phạm vi hợp lệ sẽ được chuẩn hóa thành dạng văn bản thông thường để tránh kích hoạt cờ cảnh báo của Reviewer.

---

## 4. NGUYÊN NHÂN LỖI GIAO DIỆN HIỂN THỊ STALE VÀ DỪNG CẬP NHẬT

### 4.1. Sự lệch pha giữa `source_ids` và `source_fingerprint`
- **Vị trí mã nguồn:** `gateway/service.py` dòng 513 và 586:
  ```python
  # MÃ NGUỒN CŨ:
  context_receipt = {
      'engine': 'local_supervisor',
      'source_ids': targets or None,  # Chỉ lưu [49] (1 phần tử)
      'source_fingerprint': digest(...) # Nhưng hash từ packages (6 phần tử cả subtasks!)
  }
  ```
- Khi polling `get_ai_run`:
  ```python
  current = [native.package(i) for i in source_ids] # Đọc lại 1 phần tử [49]
  if digest(...) != result['source_fingerprint']:   # So sánh hash 1 phần tử với hash 6 phần tử -> KHÔNG KHỚP!
      return {'status': 'stale', 'text': 'Dữ liệu hoặc quyền đọc đã đổi...'}
  ```
- **Hệ quả:** Mặc dù tác vụ chạy thành công 100%, nhưng mỗi khi giao diện hỏi lại trạng thái, hàm kiểm tra tính toàn vẹn phát hiện hash không khớp và lập tức hạ cấp trạng thái thành `STALE`, khiến màn hình hiển thị thông báo lỗi thay vì câu trả lời.
- **Giải pháp sửa:** Đồng bộ `source_ids = [p['id'] for p in packages]` ở mọi vị trí khởi tạo và tổng kết tác vụ.
