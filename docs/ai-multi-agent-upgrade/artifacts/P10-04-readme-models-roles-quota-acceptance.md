# BIÊN BẢN NGHIỆM THU — TASK P10-04
## Tạo README Cho Models / Roles / Quota Và Hướng Dẫn Vận Hành Không Tốn Chi Phí

- **Mã Task:** `P10-04`
- **Giai đoạn:** Phase P10 — Local main release + no-touch Docker runtime handover
- **Ngày hoàn thành:** 2026-10-17
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** DONE
- **Tiêu chí nghiệm thu:**
  - Thông tin model/tính năng cập nhật tự động từ cấu hình (`MODEL_ALLOWLIST.json`), không hardcode quota.
  - Hướng dẫn rõ ràng về 5 vai trò (20 người dùng LAN), cơ chế Fair-Share Queue và chính sách 0 đồng (No-cost usage & maintenance). Phụ thuộc `P02-11`.

---

### 1. Chi Tiết Thực Hiện

1. **Soạn thảo sổ tay hướng dẫn vận hành hoàn chỉnh:**
   - File: [`openproject/ai/README_OPERATIONS.md`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/README_OPERATIONS.md).
   - Nội dung chính:
     - **Chính sách Không Chi Phí:** Zero-billing, không dùng VPS, không dùng domain trả phí, không tự động kích hoạt thẻ tín dụng.
     - **Mô hình & Quản lý Hạn Mức:** Tham chiếu động `MODEL_ALLOWLIST.json`, kiểm soát giới hạn 15 RPM, 250,000 TPM, 500 RPD theo chuẩn Free Tier của Google AI Studio; cơ chế Circuit Breaker và tự làm mới lúc 00:00 PST.
     - **Phân Quyền & Quy Mô 20 Người Dùng LAN:** 5 vai trò Scrum (PM, BA, FE, BE, QA) với quy tắc bất biến PM-Only-Write; hàng đợi công bằng Fair-Share FIFO Queue chống starvation.
     - **Quy Trình Khởi Động Không Chạm (No-Touch Startup):** Hướng dẫn vận hành chỉ với việc mở Docker Desktop; script phục hồi ngoại lệ `Repair-QLDAPM-Local.ps1`.
     - **Sao Lưu & Phục Hồi:** Hướng dẫn sử dụng `Schedule-LocalBackup.ps1` có kiểm soát đồng thuận và diễn tập phục hồi qua `Test-OpenProjectAIRestore.ps1`.

2. **Kiểm tra không hardcode quota:**
   - Cấu hình model được đọc động từ [`openproject/ai/gateway/MODEL_ALLOWLIST.json`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/MODEL_ALLOWLIST.json).
   - Toàn bộ tham số giới hạn và trạng thái model được quản lý qua runtime policy của Gateway.
