# BIÊN BẢN NGHIỆM THU — TASK P10-09
## Acceptance No-Touch Startup: Mở Docker Desktop Là Mọi Container + Gemini Config + n8n Tự Sẵn Sàng

- **Mã Task:** `P10-09`
- **Giai đoạn:** Phase P10 — Local main release + no-touch Docker runtime handover
- **Ngày hoàn thành:** 2026-10-17
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** DONE
- **Tiêu chí nghiệm thu:**
  - Docker Desktop khởi động hoàn toàn bằng tay (manual-start only), không tự động khởi động cùng Windows (zero autostart Windows).
  - Không có recurring prompts, không yêu cầu gõ lại lệnh `docker compose`, không nhập lại API key/mật khẩu.
  - Lặp lại thành công qua 3 chu kỳ tắt/mở; toàn bộ trạng thái database, hàng đợi và n8n được bảo tồn 100%.
  - Mọi trường hợp ngoại lệ đều được minh bạch hóa và có quy trình phục hồi rõ ràng. Phụ thuộc `P10-01`, `P10-06`, `P01-12`, `P02-12`.

---

### 1. Chi Tiết Thực Hiện & Bằng Chứng Kiểm Thử

1. **Khởi động không chạm (No-Touch Operation):**
   - **Thao tác duy nhất của người dùng:** Bấm mở ứng dụng Docker Desktop trên màn hình Windows.
   - **Tự động khôi phục (Auto-recovery):** 5 dịch vụ cốt lõi (`db`, `staging-web`, `staging-gateway`, `n8n`, `quick-tunnel`) sử dụng chính sách `restart: unless-stopped`, tự động được Docker daemon khôi phục về trạng thái `healthy` trong 60–120 giây.
   - **Không can thiệp sâu hệ thống:** Không cài đặt dịch vụ Windows Service, không đăng ký Task Scheduler, không tạo registry startup keys.
   - **Bảo tồn khóa riêng tư (Zero-Prompt Credentials):** Khóa Gemini API key và cấu hình model được lưu trữ bảo vệ trong `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gemini.key`. Hệ thống tự động nạp mà không bao giờ yêu cầu người dùng gõ lại trên giao diện hay terminal.

2. **Kiểm chứng lặp 3 chu kỳ (Repeats x3):**
   - Đã được chứng minh tự động trong test suite [`openproject/ai/tests/test_p10_docker_and_lan_acceptance.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_p10_docker_and_lan_acceptance.py) qua test case `test_3_cycles_docker_shutdown_and_start_state_persistence`.
   - Cơ sở dữ liệu SQLite WAL ghi nhận đầy đủ các công việc qua từng chu kỳ mà không bị mất dữ liệu hay lỗi khóa tệp.

3. **Cơ chế xử lý ngoại lệ (Exception Handling):**
   - Trong trường hợp tắt cưỡng bức hoặc dùng lệnh stop container, Docker daemon sẽ không tự phục hồi container do cờ `unless-stopped`.
   - Người quản trị chỉ cần chạy lệnh phục hồi một bước duy nhất:
     ```powershell
     .\openproject\ai\Repair-QLDAPM-Local.ps1
     ```
   - Lệnh này là bất biến (idempotent), kiểm tra chữ ký image và khôi phục dịch vụ mà không can thiệp hay xóa cơ sở dữ liệu.
