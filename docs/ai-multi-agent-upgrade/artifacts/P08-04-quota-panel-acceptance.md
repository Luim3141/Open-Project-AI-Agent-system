# P08-04 ACCEPTANCE ARTIFACT: GEMINI FREE-TIER QUOTA PANEL & 20-USER LAN FAIR ALLOCATION

> **Task ID:** P08-04  
> **Phase:** P08 — Control Center / quota / approval / local status  
> **Status:** DONE (100% Verified)  
> **Author:** Antigravity (Senior Full-Stack & AI Multi-Agent Architect)  
> **Date:** 2026-10-17  
> **Module:** [`openproject/ai/gateway/quota_panel.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/quota_panel.py)  
> **Tests:** [`openproject/ai/tests/test_control_center.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_control_center.py)

---

## 1. MỤC TIÊU VÀ PHẠM VI BẢO ĐẢM CHI PHÍ 0 ĐỒNG

Đáp ứng Change Request **`CR-USER-CAPACITY-20`** (mở rộng dung lượng từ 5 lên tối đa 20 người dùng mạng LAN):
1. **Zero Hardcoded Limits:** Hạn mức được đọc động từ cấu hình hệ thống (`limits.rpd: 500`, `limits.rpm: 15`, `limits.tpm: 250000`).
2. **Định mức danh nghĩa 20 Users:** 500 RPD / 20 users = **~25 RPD / người / ngày** làm mức phân bổ cơ sở danh nghĩa.
3. **Chính sách điều phối công bằng (Fair Queue):** Sử dụng cơ chế hàng đợi xoay vòng (Round-Robin Fair Queue) theo nhu cầu thực tế: tài nguyên của các user không hoạt động được tự động điều phối cho các thành viên đang làm việc, tối đa hóa hiệu quả sử dụng mà không bao giờ vượt trần 500 RPD của Google Free Tier.
4. **Minh bạch mô hình (FREE_ONLY):** Cam kết chỉ dùng model miễn phí `gemini-2.5-flash` và `gemini-1.5-flash`; bảo vệ tài khoản người dùng tuyệt đối với chính sách `STRICT_ZERO_COST`.
5. **Chu kỳ làm mới (Quota Reset):** Nêu rõ mốc làm mới hạn mức Google: `00:00 PST` (tương đương `14:00/15:00 UTC+7 Asia/Bangkok`).
6. **Link xác minh độc lập:** Dẫn link trực tiếp tới [Google AI Studio Plan Information](https://aistudio.google.com/app/plan_information) để người dùng tự kiểm chứng.

---

## 2. BẰNG CHỨNG KIỂM THỬ (TEST RESULTS)

- Test case: `ControlCenterTests.test_p08_04_quota_panel_20_users`
- Kết quả: **PASS (100%)**
- Số liệu đo lường:
  - `limits.rpd`: 500 | `limits.rpm`: 15 | `limits.tpm`: 250,000
  - `usage_today.rpd_used`: 50 | `rpd_remaining`: 450 | `percent_used`: 10.0%
  - `multi_user_allocation.max_active_users`: 20 | `nominal_per_user_rpd`: 25
  - `allocation_policy`: `DYNAMIC_FAIR_QUEUE_ROUND_ROBIN`
