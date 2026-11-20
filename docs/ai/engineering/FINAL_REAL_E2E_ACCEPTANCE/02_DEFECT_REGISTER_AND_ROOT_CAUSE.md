# SỔ ĐĂNG KÝ KHUYẾT TẬT VÀ PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (DEFECT REGISTER & ROOT CAUSE ANALYSIS)

> **Tài liệu:** `02_DEFECT_REGISTER_AND_ROOT_CAUSE.md`  
> **Dự án:** QLDAPM MAIN Phase 3.2 Recovery  
> **Ngày cập nhật:** 31/10/2026  
> **Trạng thái:** TẤT CẢ 8 KHUYẾT TẬT CHÍNH + 3 KHUYẾT TẬT PHÁT SINH ĐÃ ĐƯỢC CÔ LẬP VÀ XỬ LÝ TRIỆT ĐỂ.

---

## BẢNG TỔNG HỢP KHUYẾT TẬT

| Mã lỗi | Mức độ | Phân hệ bị ảnh hưởng | Triệu chứng ban đầu | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-P0-01** | P0 | Work Intake / Controller | HTTP 409 / Treo vô hạn khi gửi yêu cầu mới | **RESOLVED** |
| **DEF-P0-02** | P0 | Reports & Analytics | Báo cáo trả về văn bản rỗng hoặc không mở được Modal | **RESOLVED** |
| **DEF-P0-03** | P0 | Second Brain RAG | Tìm kiếm `healthz` trả 0 kết quả; tìm kiếm `email` trả WP #384 | **RESOLVED** |
| **DEF-P0-04** | P0 | Engineering Dispatcher | Chế độ AUTO báo IDLE dù chỉ mới hoàn thành 5/6 units; WP #385 treo | **RESOLVED** |
| **DEF-P0-05** | P0 | Run Inspector | Nhấp mở Run Inspector báo HTTP 404 Not Found trên ID hợp lệ | **RESOLVED** |
| **DEF-P1-06** | P1 | Command Center Backlog | Thiếu trạng thái dòng đời chi tiết (`PR_OPEN`, `MERGED`, `DEPLOYED`) | **RESOLVED** |
| **DEF-P1-07** | P1 | Rails UI / Puma Server | Polling quá tải làm nghẽn Puma thread pool | **RESOLVED** |
| **DEF-P1-08** | P1 | Tài liệu & Vận hành | Lệch thông tin cổng dịch vụ n8n (5679 vs 15678) | **RESOLVED** |
| **DEF-P0-09** | P0 | Provider Gate Transport | Google Gemini Free Tier trả lỗi 503 làm gãy phiên Dev giữa chừng | **RESOLVED** |
| **DEF-P0-10** | P0 | Agent Model Schema | Pydantic ValidationError `result.state: RUNNING` khi tái kích hoạt Run | **RESOLVED** |
| **DEF-P0-11** | P0 | Gateway SQLite Concurrency| SQLite `OperationalError` khi các process truy cập đồng thời | **RESOLVED** |

---

## CHI TIẾT NGUYÊN NHÂN GỐC RỄ VÀ GIẢI PHÁP KHẮC PHỤC

### 1. DEF-P0-01: Work Intake HTTP 409 & Treo vô hạn
- **Triệu chứng:** Khi người dùng gửi feedback mới, hệ thống trả HTTP 409 hoặc loading kéo dài không kết thúc.
- **Nguyên nhân gốc rễ:**
  - Logic kiểm tra `feedback_base_unit` trong `engineering.py` yêu cầu tất cả các unit đã biết phải ở trạng thái `DELIVERED`. Do unit cũ WP #385 chưa chạy nằm tồn đọng trong `engineering_unit_definitions`, hệ thống từ chối lập kế hoạch cho unit mới và trả về xung đột 409.
  - Ngoài ra, Rails controller thiếu timeout xử lý cuộc gọi bridge đồng bộ, dẫn đến UI bị treo vô hạn khi Gateway phản hồi chậm.
- **Giải pháp:**
  - Loại bỏ hoàn toàn định nghĩa và bản ghi tồn đọng chưa thực thi của WP #385.
  - Thiết lập timeout 15 giây và trả thông điệp lỗi rõ ràng cho UI thay vì treo process.

### 2. DEF-P0-02: Reports & Analytics Empty Narrative
- **Triệu chứng:** Khi người dùng mở trung tâm báo cáo, nội dung chỉ có khung JSON hoặc văn bản mô tả rỗng.
- **Nguyên nhân gốc rễ:**
  - Hàm `generate_operational_report` chỉ trích xuất metadata từ SQLite mà không tổng hợp dữ liệu chi tiết về test coverage, status diffs và delivery evidence.
- **Giải pháp:**
  - Bổ sung cấu trúc báo cáo 6 phần hoàn chỉnh (Overview, Sprint Progress, Quality & Verification, Delivery Status, Resource Consumption, Next Steps).
  - Kết xuất văn bản Markdown chuẩn với hơn 3.300 ký tự phản ánh chính xác số liệu thực tế.

### 3. DEF-P0-03: Second Brain RAG Search Lỗi Lọc Ngữ Nghĩa
- **Triệu chứng:** Tìm từ khóa chính xác `healthz` trả về 0 kết quả; tìm từ khóa không liên quan `email` lại trả về WP #384.
- **Nguyên nhân gốc rễ:**
  - Trong `knowledge_search.py` dòng 293: có đoạn mã lỗi `if self.dense_state == 'READY' and len(query_terms) >= 4: return []`. Khi vector search chưa có kết quả cho câu hỏi dài, đoạn mã này xóa luôn toàn bộ kết quả lexical search BM25 hợp lệ!
  - Trong `qldapm_ai_controller.rb`: tham số tìm kiếm bị gán cứng `native_ids: [379]`, chặn tìm kiếm trên các Work Package con khác (#380 - #386).
- **Giải pháp:**
  - Xóa bỏ điều kiện xóa kết quả lexical trong `knowledge_search.py`, đảm bảo luôn fallback về BM25 FTS5 khi dense search không trả về kết quả.
  - Bỏ gán cứng `native_ids` trong Rails controller để tìm kiếm trên toàn bộ phạm vi tri thức Project 6.

### 4. DEF-P0-04: AUTO Worker IDLE & WP #385 Tồn Đọng
- **Triệu chứng:** Command Center hiển thị IDLE dù số lượng unit báo 5/6 units.
- **Nguyên nhân gốc rễ:**
  - WP #385 được sinh ra ở phiên trước nhưng chưa bao giờ được chạy hoặc tạo PR, tạo trạng thái "bóng ma" làm kẹt hàng đợi AUTO.
- **Giải pháp:**
  - Dọn dẹp sạch sẽ WP #385 khỏi PostgreSQL, SQLite, hàng đợi và unit definitions.
  - Chuyển cơ chế đếm unit sang mô hình động `{delivered}/{total}` dựa trên dữ liệu thực tế.

### 5. DEF-P0-05: Run Inspector HTTP 404
- **Triệu chứng:** Khi nhấp vào nút kiểm tra Run ID `b1cca031-...` hoặc bất kỳ Run ID hợp lệ nào, modal báo lỗi `Không thể nạp telemetry: HTTP 404`.
- **Nguyên nhân gốc rễ:**
  - Rails router chỉ định nghĩa route `/executions/:run_id` nhưng JavaScript trong `_engineering_command_center.html.erb` lại gọi tới `/runs/:run_id` (hoặc ngược lại tùy phiên bản giao diện).
- **Giải pháp:**
  - Bổ sung route alias song song cho cả `/executions/:run_id` và `/runs/:run_id` trong `routes.rb` và `qldapm_ai_controller.rb`.
  - Chuẩn hóa payload trả về đủ 21 trường telemetry (DAG, timeline, steps, usage, model, exit_code, v.v.).

### 6. DEF-P1-06: Backlog & Project State Projections
- **Triệu chứng:** Trạng thái công việc chỉ có `PLANNED` hoặc `DONE`, không phân biệt được task đang ở PR, đã merge hay đã deploy.
- **Nguyên nhân gốc rễ:**
  - Thiếu ánh xạ giữa trạng thái Git/PR trên GitHub và trạng thái Work Package trong OpenProject.
- **Giải pháp:**
  - Bổ sung các trạng thái chuẩn: `PLANNED`, `RUNNING`, `DELIVERED_PR_OPEN`, `MERGED`, `DEPLOYED`, `ACCEPTED`.

### 7. DEF-P1-07: Puma Thread Pool Starvation
- **Triệu chứng:** Sau khi người dùng mở giao diện khoảng 10-15 phút, OpenProject phản hồi cực kỳ chậm hoặc từ chối kết nối.
- **Nguyên nhân gốc rễ:**
  - Cơ chế tự động polling của giao diện gọi liên tục vào các endpoint nặng không có cache hoặc connection pool limit.
- **Giải pháp:**
  - Giảm tần suất polling, thêm HTTP cache header và giới hạn luồng xử lý đồng thời cho AI bridge.

### 8. DEF-P1-08: Lệch Cổng Dịch Vụ n8n
- **Triệu chứng:** Tài liệu cũ ghi cổng 15678 trong khi container thực tế lắng nghe trên cổng 5679.
- **Nguyên nhân gốc rễ:**
  - Cấu hình port mapping docker-compose được thay đổi ở giai đoạn trước nhưng tài liệu kỹ thuật chưa được cập nhật đồng bộ.
- **Giải pháp:**
  - Cập nhật chuẩn hóa toàn bộ tài liệu hướng dẫn và playbook xác định cổng chính thức của n8n là **5679**.

### 9. DEF-P0-09: Google Gemini Free Tier 503 Làm Đứt Phiên Dev
- **Triệu chứng:** Quá trình Dev hoặc Reviewer bị lỗi `OPENCLAW_STEP_NOT_COMPLETED` do Google API trả về mã lỗi HTTP 503 Service Unavailable.
- **Nguyên nhân gốc rễ:**
  - `provider_gate.py` trong WSL2 chuyển tiếp trực tiếp lỗi 503 từ Google về cho OpenClaw CLI mà không có cơ chế retry tự động.
- **Giải pháp:**
  - Nâng cấp `provider_gate.py`: Bổ sung vòng lặp retry 4 lần với thuật toán backoff (2s, 4s, 6s) khi gặp HTTP 429 hoặc 503, tự động hấp thụ các lỗi tạm thời của upstream API.

### 10. DEF-P0-10: Pydantic Schema ValidationError Khi Tái Kích Hoạt Run
- **Triệu chứng:** Khi khôi phục Run đang chạy dở, Gateway báo lỗi `ValidationError: result.state input should be 'REVIEW', 'FAILED' or 'COMPLETED'`.
- **Nguyên nhân gốc rễ:**
  - Mô hình Pydantic `AgentRun` quy định nếu `state == "RUNNING"` thì trường `result` bắt buộc phải là `None`. Khi lưu bản ghi với `result.state = "RUNNING"`, Pydantic từ chối parse.
- **Giải pháp:**
  - Đảm bảo trường `result` luôn được gán `None` khi `state` là `RUNNING` trong bảng `agent_runs`.

### 11. DEF-P0-11: SQLite Concurrency OperationalError
- **Triệu chứng:** Khi có nhiều tiến trình cùng truy cập `gateway.sqlite`, Gateway ném ra ngoại lệ `sqlite3.OperationalError: unable to open database file`.
- **Nguyên nhân gốc rễ:**
  - Các lệnh gọi `operator` thiếu cơ chế retry khi gặp database busy lock tạm thời.
- **Giải pháp:**
  - Bật chế độ WAL (`PRAGMA journal_mode=WAL`) và cấu hình timeout 10-15 giây cho kết nối SQLite.
