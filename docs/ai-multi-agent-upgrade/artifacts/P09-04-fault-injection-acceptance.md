# BIÊN BẢN NGHIỆM THU TASK P09-04
## Fault-Injection: 429 / 503 / Timeout / Crash / Restart / Quota Reset

- **Mã task:** `P09-04`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (4/4 fault-injection scenarios PASS, zero duplicate write)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Kiểm thử khả năng chống chịu sự cố (Fault-Tolerance) và tự phục hồi của hệ thống khi gặp các lỗi hạ tầng mạng, provider LLM, sự cố sập nguồn/container crash, và thời điểm chuyển giao hạn mức hàng ngày (Quota Reset).
- **Tiêu chí chấp nhận:**
  - **429 Rate Limit / Quota Exhaustion:** Bắt chính xác lỗi hết hạn mức từ Google AI API Free Tier, kích hoạt Circuit Breaker, tính toán thời gian chờ `retry_at` có backoff, chuyển trạng thái an toàn sang `WAITING_QUOTA` mà không gây mất mát dữ liệu hay thử lại vô tận (no retry storm).
  - **503 Service Unavailable / Timeout & Đối soát (Reconciliation):** Khi xảy ra timeout mạng giữa chừng, hệ thống đánh dấu trạng thái không rõ ràng (`OUTCOME_UNKNOWN`). Quy trình đối soát `reconcile_request` truy vấn native OpenProject tìm kiếm marker vết `QLDAPM-request-<digest>`; nếu đã tồn tại thì đánh dấu `reconciled = True` và TUYỆT ĐỐI KHÔNG thực hiện ghi trùng lặp (zero duplicate write).
  - **Container Crash & Restart (Tính bền vững SQLite WAL):** Giả lập tiến trình bị ngắt đột ngột; toàn bộ transaction đã commit trên SQLite WAL được bảo toàn vẹn toàn khi khởi động lại. Cùng một `idempotency_key` khi gửi lại sẽ nhận được kết quả đã lưu trữ từ cache mà không gọi lại thao tác ghi.
  - **Quota Reset Boundary (00:00 PST / 14:00 UTC+7):** Hạn mức RPM/TPM/RPD được giải phóng tự động sang ngày mới, trong khi toàn bộ lịch sử đề xuất (proposals) và bản ghi idempotency vẫn được lưu giữ bền vững phục vụ audit.

---

### 2. Các kịch bản kiểm thử Fault-Injection thực tế
1. **Kiểm thử Provider 429 Quota Exhaustion:**
   - Thực hiện liên tiếp các request vượt giới hạn RPM của cấu hình Free Tier.
   - Kết quả: Ném lỗi `RPM_EXHAUSTED` kèm thuộc tính `retry_at`, bản ghi token trong bảng `gemini_usage` vẫn bảo toàn.
2. **Kiểm thử Timeout & Chống Ghi trùng lặp (Reconciliation):**
   - Giả lập việc client mất kết nối sau khi comment đã được gửi lên OpenProject.
   - Khi client gọi `reconcile_request`, Gateway kiểm tra danh sách activity, tìm thấy marker vết và trả về `reconciled: True`. Số lượng comment trên work package duy trì đúng 1 bản ghi (không nhân đôi).
3. **Kiểm thử Sập nguồn / Crash & Restart:**
   - Ghi nhận yêu cầu mutation `create_work_package` kèm `idempotency_key`.
   - Hủy bỏ kết nối DB, tái khởi động instance `Store` mới trên cùng thư mục lưu trữ.
   - Đọc lại `idempotency_key`: Trả về kết quả hoàn chỉnh ban đầu, trạng thái `finished`.
4. **Kiểm thử Quota Reset:**
   - Chèn dữ liệu sử dụng từ ngày hôm trước (`yesterday_time`), kích hoạt reservation ngày mới: Quota hôm nay được cấp phát bình thường, dữ liệu hôm qua vẫn lưu lại để phục vụ báo cáo.

---

### 3. Bằng chứng kiểm thử tự động
File kiểm thử: [`openproject/ai/tests/test_fault_injection.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_fault_injection.py)
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.471s

OK
- test_provider_429_trips_circuit_breaker_and_preserves_ledger: PASS
- test_timeout_and_reconciliation_prevents_duplicate_writes: PASS
- test_crash_and_restart_simulation_with_sqlite_wal: PASS
- test_quota_reset_boundary_preserves_proposals_and_idempotency: PASS
```
