# HỒ SƠ PHÁP Y M3: MA TRẬN PHÂN QUYỀN CÔNG CỤ OPENCLAW (TOOL PERMISSION MATRIX)
> Thời điểm kiểm toán: `2026-10-30 20:29:35 UTC`  
> Phạm vi: Khảo sát chính sách phân quyền công cụ ở cả cấp độ Global và Tác nhân

---

## 1. MA TRẬN PHÂN QUYỀN THEO TÁC NHÂN (TOOL PERMISSION MATRIX)

| Tên Công Cụ (Tool Name) | Mô Tả Chức Năng | Dev Agent | Reviewer Agent | QA Agent | Rationale & Security Safeguard |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`read`** | Đọc nội dung file trong workspace | **CHO PHÉP** | **CHO PHÉP** | **CHO PHÉP** | Cần thiết để khảo sát mã nguồn và xem kết quả. |
| **`write` / `edit`** | Sửa file qua OpenClaw built-in | **CHẶN** | **CHẶN** | **CHẶN** | Ngăn chặn sửa file ngầm không kiểm soát. |
| **`exec` / `process`** | Chạy tiến trình lệnh shell | **CHO PHÉP** | **CHẶN** | **CHO PHÉP** | Dev chạy script, QA chạy pytest; Reviewer cấm tuyệt đối. |
| **`sessions_spawn`** | Tạo phiên làm việc con | **CHẶN** | **CHẶN** | **CHẶN** | Ngăn ngừa việc spawn agent vô tội vạ gây tràn token. |
| **`web_search`** | Tìm kiếm thông tin trên internet | **CHẶN** | **CHẶN** | **CHẶN** | Ngăn ngừa rò rỉ dữ liệu hoặc hallucination từ internet. |
| **`web_fetch`** | Tải trang web / file từ internet | **CHẶN** | **CHẶN** | **CHẶN** | Ngăn ngừa tải binary ngoài scope vào workspace. |
| **`cron` / `automations`** | Đặt lịch chạy nền | **CHẶN** | **CHẶN** | **CHẶN** | Mọi lịch trình đều thuộc quyền quản lý của QLDAPM Gateway. |
| **`elevated` (sudo)** | Chạy quyền quản trị hệ thống | **CHẶN** | **CHẶN** | **CHẶN** | Bảo vệ cô lập hệ điều hành WSL2. |

---

## 2. KẾT LUẬN KIỂM TOÁN AN TOÀN

Chính sách phân quyền tuân thủ nguyên tắc **Least Privilege (Đặc quyền tối thiểu)**:
- Không có bất kỳ tác nhân nào có quyền truy cập Internet.
- Reviewer Agent bị tước hoàn toàn quyền sửa và thực thi, đảm bảo khách quan 100%.
- QA Agent chỉ có quyền chạy test mà không được phép tự ý sửa code để qua test.
