# BIÊN BẢN NGHIỆM THU — TASK P10-03
## Tạo Backup Schedule Tùy Chọn User Consent + Restore/Runbook Emergency

- **Mã Task:** `P10-03`
- **Giai đoạn:** Phase P10 — Local main release + no-touch Docker runtime handover
- **Ngày hoàn thành:** 2026-10-17
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** DONE
- **Tiêu chí nghiệm thu:**
  - Không lưu secret vào script hoặc source code.
  - Lịch backup là tùy chọn, chỉ kích hoạt khi có sự đồng ý tường minh của người dùng (`-Consent`).
  - Đi kèm kiểm thử phục hồi (Restore drill) và tài liệu runbook cứu hộ khẩn cấp. Phụ thuộc `P09-05`.

---

### 1. Chi Tiết Thực Hiện

1. **Script lập lịch sao lưu an toàn:**
   - File: [`openproject/ai/Schedule-LocalBackup.ps1`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/Schedule-LocalBackup.ps1).
   - Tham số:
     - `-Action Status`: Kiểm tra trạng thái tác vụ lập lịch hiện hành.
     - `-Action Enable -Consent`: Đăng ký tác vụ sao lưu tự động chạy 02:00 AM mỗi ngày. Bắt buộc có cờ `-Consent`, nếu thiếu sẽ báo lỗi và dừng ngay.
     - `-Action Disable`: Hủy đăng ký tác vụ một cách an toàn.
   - **Cam kết không lộ Secret (Zero-Secret):** Lệnh đăng ký tác vụ chỉ gọi trực tiếp `local_backup.py snapshot` sử dụng môi trường private runtime `%LOCALAPPDATA%\QLDAPM\openproject-ai`, tuyệt đối không chứa mật khẩu DB, khóa API hay token trong định nghĩa tác vụ XML.

2. **Quy trình phục hồi khẩn cấp (Emergency Restore Runbook):**
   - Script diễn tập phục hồi cô lập: [`openproject/ai/Test-OpenProjectAIRestore.ps1`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/Test-OpenProjectAIRestore.ps1).
   - Diễn tập khôi phục đã hoàn thành thành công trong task `P09-05` với đầy đủ tính toàn vẹn SHA-256 cho Postgres dump, assets tarball và SQLite snapshot.
   - Tài liệu tham chiếu chi tiết: [`docs/ai-multi-agent-upgrade/LOCAL_WINDOWS_RUNBOOK.md`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/LOCAL_WINDOWS_RUNBOOK.md).

3. **Kết quả kiểm thử tự động:**
   - Test suite: [`openproject/ai/tests/test_backup_schedule.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_backup_schedule.py).
   - Kết quả: **3/3 tests PASS 100%**.
