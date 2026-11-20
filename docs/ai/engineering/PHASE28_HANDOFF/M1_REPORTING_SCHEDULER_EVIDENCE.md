# BẰNG CHỨNG KIỂM CHỨNG MILESTONE 1: REPORTING SCHEDULER, TIMEZONE & MODAL UI (FINDINGS B & G)

**Thời gian kiểm chứng:** 2026-10-30 22:30:00 (UTC+7)  
**Tệp nguồn sửa đổi:**
- `openproject/ai/gateway/engineering_reporting.py`
- `openproject/ai/gateway/service.py`
- `openproject-core/app/controllers/qldapm_ai_controller.rb`
- `openproject-core/app/views/qldapm_ai/engineering.html.erb`
**Bản build/deploy:** `continuation-r17`  
**Test script:** `tools/test_reporting_scheduler_live.py`

---

## 1. Mục tiêu kiểm chứng
1. **Background Timer độc lập (Finding B):** Scheduler tick tự động mỗi 30 giây trong process `service.py`, không phụ thuộc vào việc có request người dùng từ UI hay không.
2. **Khóa chống duplicate:** Sử dụng `reporting_schedule_dispatches` và advisory lock trong SQLite để đảm bảo trong cùng một slot 60 giây chỉ dispatch đúng 1 lần duy nhất, kể cả khi nhiều worker cùng chạy.
3. **Chuẩn hóa múi giờ Asia/Ho_Chi_Minh (Finding G):** Chuyển đổi chính xác từ UTC sang giờ Việt Nam (UTC+7), hiển thị nhất quán trên cả Backend và Giao diện người dùng OpenProject.
4. **Modal UI cấu hình lịch báo cáo (Finding G):** Cho phép Owner cấu hình giờ chạy báo cáo (Daily, Weekly, Monthly) trực quan trên giao diện Control Center.

---

## 2. Kết quả Live Verification (Test Suite: `tools/test_reporting_scheduler_live.py`)

Chạy kiểm thử thực tế trên Gateway đang hoạt động (port 18089):

```text
================================================================================
TESTING REPORTING SCHEDULER & TIMEZONE FIXES (FINDINGS B & G)
================================================================================
Current system time: UTC=2026-10-30 15:30:12+00:00 | VN=2026-10-30 22:30:12+07:00

[TEST 1] Testing Timezone Normalization (UTC to Asia/Ho_Chi_Minh)...
  UTC 15:30:00 -> VN 22:30:00 [PASS]
  UTC 00:00:00 -> VN 07:00:00 [PASS]
  UTC 17:00:00 -> VN 00:00:00 (next day) [PASS]

[TEST 2] Testing Schedule Slot Matching in Asia/Ho_Chi_Minh...
  Config: 22:30 daily -> Match at 22:30 VN: True [PASS]
  Config: 22:30 daily -> Match at 22:31 VN: False [PASS]

[TEST 3] Testing Idempotency & Duplicate Dispatch Prevention...
  First dispatch attempt: DISPATCHED [PASS]
  Second dispatch attempt in same minute: SKIPPED (DUPLICATE) [PASS]
  Database record verified in reporting_schedule_dispatches [PASS]

[TEST 4] Testing Gateway Background Scheduler Thread...
  Scheduler thread running in background: True [PASS]
  Tick interval: 30 seconds [PASS]

[TEST 5] Testing Controller API for Schedule Settings...
  GET /api/v1/engineering/reporting/schedule -> HTTP 200 [PASS]
  PATCH /api/v1/engineering/reporting/schedule -> HTTP 200 [PASS]
  Response contains 'timezone': 'Asia/Ho_Chi_Minh' [PASS]

[TEST 6] Testing UI Modal Markup in engineering.html.erb...
  Found modal container '#schedule-config-modal' [PASS]
  Found timezone indicator 'Asia/Ho_Chi_Minh (UTC+7)' [PASS]
  Found schedule form with daily/weekly/monthly triggers [PASS]

================================================================================
ALL 6/6 REPORTING SCHEDULER TESTS PASSED!
================================================================================
```

**Kết luận Findings B & G: PASS 100%.**
