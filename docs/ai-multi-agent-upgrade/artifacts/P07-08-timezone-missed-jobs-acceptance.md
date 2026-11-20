# BIÊN BẢN NGHIỆM THU TASK P07-08
## Kiểm Tra Schedule Asia/Bangkok và Chính Sách Missed Jobs Khi Máy/Docker Tắt

- **Task ID:** P07-08
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Không double run và không catch-up burst sau Docker restart; lịch đúng múi giờ Asia/Bangkok (UTC+7).
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Quy chuẩn múi giờ chuẩn hóa (Asia/Bangkok Timezone):**
  - Mọi lịch biểu định kỳ (ví dụ `0 0 9 * * *` cho Daily Brief) đều được cấu hình và thực thi đúng múi giờ `Asia/Bangkok`.
  - Khử hoàn toàn sai lệch giữa UTC máy chủ và giờ địa phương Việt Nam (+07:00).
- **Chính sách bù lịch chống bão request (Zero Catch-up Burst Policy):**
  - Khi máy tính hoặc Docker tắt nhiều ngày (ví dụ nghỉ cuối tuần hoặc nghỉ lễ 5 ngày): khi bật lại, hệ thống chỉ chạy bù tối đa **1 lần duy nhất cho ngày hôm nay** (`SINGLE_TODAY_ONLY`).
  - Toàn bộ các lượt chạy của các ngày trong quá khứ được xác định là quá hạn và bị triệt tiêu (`suppressed_historical_runs_count`), tuyệt đối không xả hàng loạt request trong quá khứ làm cạn kiệt hạn mức Free Tier hoặc gây quá tải hệ thống.
- **Chống chạy lặp sau khi khởi động lại (Zero Double-Run on Restart):**
  - Khi Docker hoặc container n8n restart trong cùng một ngày mà công việc của ngày hôm đó đã hoàn thành (`already_completed_days`), hệ thống nhận diện ngày đã hoàn thành và trả về 0 lượt chạy bù (`already_completed_today: True`).

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/scheduler_registry.py`:**
   - Cung cấp hàm `resolve_catchup_plan(...)` và chuẩn hóa múi giờ `BANGKOK_TZ`.
   - Triệt tiêu dồn tích lịch cũ, đảm bảo đúng quy tắc `SINGLE_TODAY_ONLY`.
2. **`openproject/ai/tests/test_scheduler_timezone_and_ownership.py`:**
   - `test_all_schedules_use_asia_bangkok_timezone`: Thẩm định toàn bộ lịch trình đăng ký dùng `Asia/Bangkok`.
   - `test_missed_jobs_no_catchup_burst`: Mô phỏng tắt máy 5 ngày, chỉ chạy đúng 1 lần cho ngày hiện tại và triệt tiêu 4 ngày cũ.
   - `test_docker_restart_same_day_no_double_run`: Khởi động lại cùng ngày không chạy trùng lặp.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_scheduler_timezone_and_ownership.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.000s).

---

### 4. Kết luận

Task `P07-08` đã hoàn thành 100% tiêu chí nghiệm thu. Múi giờ Asia/Bangkok và chính sách missed jobs vận hành chuẩn xác, bảo vệ hoàn toàn hệ thống khỏi bão request sau restart.
