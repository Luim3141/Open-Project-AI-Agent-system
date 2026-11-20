# BIÊN BẢN NGHIỆM THU — TASK P10-02
## Tạo Recovery One-Command Tùy Chọn Chỉ Cho Ca Container Stopped/Missing

- **Mã Task:** `P10-02`
- **Giai đoạn:** Phase P10 — Local main release + no-touch Docker runtime handover
- **Ngày hoàn thành:** 2026-10-17
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** DONE
- **Tiêu chí nghiệm thu:**
  - Bình thường KHÔNG cần script; các container tự động phục hồi qua Docker Desktop `restart: unless-stopped`.
  - Khi có sự cố ngoại lệ (container bị dừng thủ công `docker stop` hoặc `compose down`), lệnh `Repair-QLDAPM-Local.ps1` phục hồi hệ thống một cách idempotent.
  - Không đòi hỏi cấu hình lại từ đầu (zero reconfiguration), không tạo dữ liệu trùng lặp, không phá vỡ dữ liệu nghiệp vụ (no seeder/mutation).

---

### 1. Chi Tiết Triển Khai & Kiểm Chứng

1. **Lệnh phục hồi duy nhất (One-Command Recovery):**
   - Script: [`openproject/ai/Repair-QLDAPM-Local.ps1`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/Repair-QLDAPM-Local.ps1).
   - Cơ chế cốt lõi trong [`openproject/ai/local_runtime.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/local_runtime.py) (`repair` / `start`):
     - Xác minh lock image và tính toàn vẹn chữ ký image trước khi khởi động.
     - Khởi động tuần tự theo thứ tự phụ thuộc: `db` -> `staging-web` -> `staging-gateway` -> `n8n` -> `n8n-editor`.
     - Chờ health check từng service chuyển sang `healthy` trước khi tiến hành bước tiếp theo.
     - Hoàn toàn **idempotent**: nếu container đã đang chạy, giữ nguyên trạng thái, không restart vô cớ.
     - Tuyệt đối không gọi seeder, không tạo database mới, không xoá volumes hay resets mã nguồn.

2. **Kết quả kiểm thử tự động (Unit Test):**
   - Test suite: [`openproject/ai/tests/test_local_runtime.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_local_runtime.py).
   - Test case mới: `test_operator_repair_idempotency_and_no_business_mutation`.
   - Kết quả: **16/16 tests PASS 100% in 1.035s**.
