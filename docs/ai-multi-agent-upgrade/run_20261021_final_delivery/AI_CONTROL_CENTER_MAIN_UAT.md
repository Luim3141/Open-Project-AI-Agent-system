# BÁO CÁO NGHIỆM THU AI CONTROL CENTER TRÊN MAIN
## AI CONTROL CENTER MAIN UAT REPORT

- **Thời điểm nghiệm thu:** 2026-10-21T07:33:54.508109+00:00
- **Giao diện điều khiển:** AI Assistant & AI Control Center (`http://localhost:8088/projects/qldapm-local`)
- **Backend xử lý:** AI Gateway (`http://localhost:8090`), Cơ sở dữ liệu SQLite `/state/gateway.sqlite`

---

### 1. CÁC TÍNH NĂNG ĐÃ NGHIỆM THU

1. **Lịch sử thực thi (Execution History):**
   - Mọi lượt gọi AI từ OpenProject đều được ghi lại với đầy đủ metadata: `run_id`, `actor_id`, `project_id`, `work_package_id`, `provider`, `model`, `token_usage`, `state`.
   - Lượt chạy UAT mẫu `ca0c3b3f-c01d-4291-a327-9c06b98e4f63` hiển thị đầy đủ chi tiết chuỗi tác nhân (Supervisor → BA → QA → Reviewer).
2. **Biểu đồ luồng thực thi (Graph Visualization & Drag-and-Drop):**
   - Đồ thị trạng thái DAG hiển thị rõ nét các bước thực thi của từng Specialist Agent.
   - Hỗ trợ tương tác kéo thả (drag & drop), tự động căn chỉnh (auto-layout) và chế độ trình chiếu (presentation mode).
3. **Chi tiết lượt chạy (Execution Detail & Audit Trail):**
   - Bảng hiển thị thông điệp gốc, số lượng token đầu vào/đầu ra, thời gian xử lý từng chặng và lý do từ chối của Reviewer khi chứng cứ không đầy đủ.
