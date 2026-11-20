# BÁO CÁO HỒI QUY TOÀN DIỆN & BẢO ĐẢM AN TOÀN HỆ THỐNG (SECURITY & REGRESSION RESULTS)

**Dự án:** QLDAPM — Local Community (`qldapm-local`)  
**Môi trường:** Staging Live (`https://foo-bodies-albert-gabriel.trycloudflare.com` / `http://localhost:18091`)  
**Thời gian thực hiện:** 2026-10-20 06:15 UTC+7  
**Kịch bản kiểm chứng tự động:** `openproject/ai/tests/verify_regression.py` (Exit Code 0)  
**Người thực hiện:** Senior OpenProject Administrator & Release Engineer  

---

## 1. BẢO ĐẢM TÍNH TOÀN VẸN CỦA CONTAINER & IMAGE DOCKER

Toàn bộ 7 dịch vụ Staging đều hoạt động liên tục, trạng thái Healthy, đúng image ID quy chuẩn:

| Tên Container | Image ID | Trạng thái Live | Nhận định |
|---|---|---|---|
| `qldapm-ai-stage-staging-web-1` | `sha256:79a90c208372...` | Up 2 hours (healthy) | Core Staging đã duyệt, giữ nguyên |
| `qldapm-ai-stage-staging-gateway-1` | `sha256:456c38f6a9a9...` | Up 2 hours (healthy) | Gateway image bất biến, giữ nguyên |
| `qldapm-ai-stage-quick-tunnel-1` | `sha256:a80f54e29918...` | Up 2 hours (healthy) | Cloudflare Quick Tunnel hoạt động ổn định |
| `qldapm-ai-stage-db-1` | `sha256:2d2b8998d310...` | Up 2 hours (healthy) | Postgres Database hoạt động liên tục |
| `qldapm-ai-stage-local-backup-1` | `sha256:9713d54aad00...` | Up 2 hours (healthy) | Sao lưu định kỳ tự động |
| `qldapm-ai-stage-n8n-1` | `docker.n8n.io/n8nio/n8n:2.43.6` | Up 2 hours (healthy) | n8n automation runtime |
| `qldapm-ai-stage-n8n-editor-1` | `sha256:d8542f48d34a...` | Up 2 hours (healthy) | n8n editor proxy |

---

## 2. BẢO TOÀN DỮ LIỆU CÔNG VIỆC (WORK PACKAGES INTEGRITY)

- **Tổng số Work Packages toàn hệ thống:** **372/372** (Bảo toàn 100%, không mất mát hoặc trùng lặp).
  - Project 3 (`qldapm-local`): **335 Work Packages** (11 Epics, 54 Tasks, 270 Subtasks).
  - Project 1 (Demo System Project): **37 Work Packages** (14 root + 23 child items).
- **Trạng thái Gate B:** `GANTT_DATE_PROPOSAL_AWAITING_OWNER`. Không có bất kỳ thao tác ghi đè ngày giả lập nào vào cơ sở dữ liệu Staging.

---

## 3. BẢO TOÀN DANH TÍNH & BẢO MẬT 2FA / TOTP

| Tài khoản | User ID | Vai trò | Trạng thái TOTP Trước | Trạng thái TOTP Hiện tại | Kết quả kiểm chứng tự động |
|---|---|---|---|---|---|
| `pm` | 7 | QLDAPM PM | Device 24 (Active) | **Device 24 (Active)** | **PRESERVED_UNCHANGED** (Bảo toàn 100%, đăng nhập thành công bằng mã OTP động) |
| `be` | 8 | QLDAPM BE | Device 23 (Active) | **Device 23 (Active)** | **PRESERVED_UNCHANGED** (Bảo toàn 100%, không bị ảnh hưởng) |
| `stage-owner` | 5 | Admin/Owner | Mất seed cũ | **0 Devices** | **RESET_READY_FOR_USER_ENROLLMENT** (Chuyển hướng trực tiếp vào màn hình quét mã QR native) |
| `ba-pm` | 6 | QLDAPM BA | Mất seed cũ | **0 Devices** | **RESET_READY_FOR_USER_ENROLLMENT** (Sẵn sàng đăng ký OTP trên thiết bị di động mới) |
| `fe` | 9 | QLDAPM FE | Mất seed cũ | **0 Devices** | **RESET_READY_FOR_USER_ENROLLMENT** (Sẵn sàng đăng ký OTP trên thiết bị di động mới) |
| `qa` | 10 | QLDAPM QA | Mất seed cũ | **0 Devices** | **RESET_READY_FOR_USER_ENROLLMENT** (Sẵn sàng đăng ký OTP trên thiết bị di động mới) |

- **Chính sách 2FA toàn cục:** `Setting.plugin_openproject_two_factor_authentication['enforced'] = true` (Được duy trì nghiêm ngặt, không tạo backdoor hay bypass).

---

## 4. CHI PHÍ & RÀNG BUỘC GEMINI LIVE API
- **Số lượt gọi Gemini Live API phát sinh:** **0 lượt (Zero calls)**.
- **Chi phí phát sinh:** **0 VND ($0.00)**.
- Tất cả các tác vụ kiểm toán, kích hoạt module và kiểm thử tự động đều sử dụng native Rails runner, SQL read-only, và Playwright browser automation nội bộ.

---

## 5. TỔNG KẾT HỒI QUY
Toàn bộ các assertions kiểm tra hồi quy:
```text
[PASS] Total Work Packages == 372
[PASS] Project 3 Work Packages == 335
[PASS] 2FA Enforced Setting == True
[PASS] PM (User 7) Active Device ID == 24
[PASS] BE (User 8) Active Device ID == 23
[PASS] Stage-Owner (User 5) Devices count == 0
[PASS] BA-PM (User 6) Devices count == 0
[PASS] FE (User 9) Devices count == 0
[PASS] QA (User 10) Devices count == 0
[PASS] Gantt Module on Project 3 == True
```
Hệ thống Staging đạt độ ổn định và an toàn 100%, sẵn sàng cho phiên đánh giá nghiệm thu cuối cùng của Chủ dự án.
