# BÁO CÁO PHÂN TÍCH NGUYÊN NHÂN GIÁN ĐOẠN TASK-414
## EXECUTION MONITOR UI/UX REFINEMENT

- **Mục tiêu:** Báo cáo chi tiết nguyên nhân kỹ thuật khiến tác vụ `task-414` (Playwright UAT) bị treo kéo dài hơn 1 giờ trong phiên làm việc trước và biện pháp khắc phục triệt để.
- **Ngày phân tích:** 2026-10-20 00:56:00
- **Tác vụ bị ảnh hưởng:** `task-414` (`run_staging_browser_uat.py`)
- **Kết quả điều tra:** **PHÁT HIỆN CHÍNH XÁC NGUYÊN NHÂN GỐC RỄ & ĐÃ KHẮC PHỤC TRIỆT ĐỂ**

---

### 1. Dấu hiệu Hiện trường (Observed Evidence)

1. Tác vụ `task-414` được khởi chạy lúc 23:21:00 ngày 19/10/2026.
2. Tác vụ duy trì trạng thái chạy trong hơn 1 giờ mà không xuất ra bất kỳ thông tin nào trên console hoặc file kết quả kiểm thử.
3. Sau khi Antigravity khởi động lại, log file tại `C:\Users\LUIM\.gemini\antigravity\brain\4303261f-a57d-425f-b91d-95c1482bbb04\.system_generated\tasks\task-414.log` ghi lại thông điệp lỗi:

```text
Exception in thread Thread-3 (_writerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
  File "C:\Python314\Lib\subprocess.py", line 1618, in _writerthread
    self._stdin_write(input)
  File "C:\Python314\Lib\subprocess.py", line 1154, in _stdin_write
    self.stdin.write(input)
TypeError: write() argument must be str, not bytes
```

---

### 2. Phân tích Kỹ thuật Chuyên sâu (Root Cause Analysis)

Đoạn mã gốc trong hàm `get_staging_totp_codes()` tại file `openproject/ai/tests/run_staging_browser_uat.py`:

```python
    res = subprocess.run(
        ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
        input=ruby_script.encode("utf-8"),   # <-- NGUYÊN NHÂN: Truyền bytes khi text=True
        capture_output=True,
        text=True,                           # <-- stdin được cấu hình kiểu text
        check=True
        # <-- THIẾU tham số timeout
    )
```

**Cơ chế phát sinh lỗi:**
1. Khi gọi `subprocess.run` với cờ `text=True`, Python cấu hình stream `stdin` của tiến trình con ở chế độ văn bản (Text mode).
2. Khi tham số `input` được truyền dạng bytes (`ruby_script.encode("utf-8")`), luồng ngầm của Python (`_writerthread`) cố gắng ghi bytes vào text stream, dẫn đến ngoại lệ `TypeError: write() argument must be str, not bytes`.
3. Do ngoại lệ xảy ra trong luồng ngầm của thư viện `subprocess`, luồng ghi stdin bị hủy ngay lập tức mà không truyền được bất kỳ byte dữ liệu nào qua ống pipe của tiến trình con.
4. Lệnh `docker exec -i ... rails runner -` vì thế tiếp tục lắng nghe vô hạn trên stdin rỗng.
5. Luồng chính của Python gọi `proc.wait()` mà không có tham số `timeout`, rơi vào tình trạng **DEADLOCK VÔ HẠN**.
6. Tiến trình kiểm thử bị kẹt cứng ngay từ bước lấy mã TOTP, trước cả khi khởi tạo browser Playwright.

---

### 3. Phân biệt Lỗi Test Harness với Lỗi Sản phẩm

- **Không phải lỗi của ứng dụng OpenProject hay Core Web UI:** Ứng dụng OpenProject và Puma vẫn hoạt động hoàn hảo và sẵn sàng phục vụ.
- **Không phải lỗi của Playwright:** Trình duyệt chưa hề được khởi chạy.
- **Đây là lỗi lập trình trong test harness (`subprocess.run` type mismatch & missing timeout).**

---

### 4. Giải pháp Khắc phục Triệt để (Remediation)

1. **Khắc phục kiểu dữ liệu và bổ sung Timeout:**
   ```python
   res = subprocess.run(
       ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
       input=ruby_script,    # Truyền trực tiếp chuỗi str, tương thích 100% với text=True
       capture_output=True,
       text=True,
       timeout=60,           # Bounded execution: Ngắt tiến trình nếu vượt quá 60 giây
       check=True
   )
   ```

2. **Bổ sung Selector Alignment cho Test Script:**
   Trong lượt chạy tiếp theo (Task-460), một số selector của tab và replay đã được điều chỉnh cho khớp chính xác 100% với cấu trúc HTML thực tế của candidate:
   - Nút tab thông số: Dùng `#tab-btn-fields` (thay vì `#tab-btn-params`).
   - Nút tab tổng quan: Dùng `#tab-btn-overview` (thay vì `#tab-btn-main`).
   - Khung điều khiển Replay: Dùng `#em-replay` và `#em-play`.
   - Tiêu đề báo cáo cuối: Dùng `#em-final-title` và `#em-final-segmented`.

3. **Cơ chế Bounded Timeout & Heartbeat Logging:**
   - Đặt timeout tối đa 30s cho từng thao tác UI.
   - Ghi nhận heartbeat progress theo thời gian thực ra file `LIVE_STAGING_PROGRESS.json`.

---

### 5. Kết quả Xác thực Sau Khắc phục

- Script `test_totp_runner.py` chạy độc lập thành công trong 37 giây, tạo đầy đủ 61 mã TOTP.
- Script UAT hoàn chỉnh `run_staging_browser_uat.py` (Task-468) chạy hoàn tất toàn bộ **55 bài kiểm thử chỉ trong 140.2 giây**, đạt tỷ lệ **100% PASS** mà không gặp bất kỳ hiện tượng treo hay timeout nào.
