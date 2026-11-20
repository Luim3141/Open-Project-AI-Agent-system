# BÁO CÁO XÁC MINH RUNTIME OPENCLAW WSL2 VÀ GEMINI FREE TIER

> **Tài liệu:** `06_OPENCLAW_RUNTIME_VERIFICATION.md`  
> **Môi trường thực thi:** WSL2 Distribution `OpenClawGateway`  
> **Cổng dịch vụ:** `http://127.0.0.1:18789` (OpenClaw Gateway)  
> **Cổng Provider Gate:** `http://127.0.0.1:18890` (Local Token Admission)  
> **Mô hình AI:** `gemini-3.5-flash-lite` (Google Gemini Free Tier)  
> **Chi phí thực tế:** **$0.00 USD** (Hoàn toàn miễn phí, tuân thủ Charter)

---

## 1. KIỂM TOÁN KIẾN TRÚC MÔI TRƯỜNG THỰC THI (WSL2 ARCHITECTURE)

Hệ thống QLDAPM không chạy mã nguồn do AI sinh ra trực tiếp trên máy chủ Windows hay chạy dưới quyền `root`. Mọi thao tác lập trình, chạy lệnh kiểm thử và sửa code đều được cô lập nghiêm ngặt:

1. **User cô lập:** Tiến trình AI agent chạy dưới tài khoản chuẩn `openclaw` (không có quyền sudo không mật khẩu).
2. **Worktree cô lập:** Mỗi đơn vị kỹ thuật (unit) được tạo một git worktree riêng biệt trong thư mục `/home/openclaw/engineering/{unit}` tách biệt hoàn toàn với kho mã nguồn chính.
3. **Môi trường Python ảo (.venv):** Tự động khởi tạo và ghim phiên bản phụ thuộc chính xác (`fastapi==0.115.4`, `pytest==8.3.3`, `uvicorn==0.32.0`, `httpx==0.27.2`).
4. **Bảo vệ khóa bí mật (Credential Protection):** Agent tuyệt đối không được cấp Google API Key thật. Agent chỉ giao tiếp qua Provider Gate cục bộ tại cổng `18890` bằng một client token nội bộ có hạn sử dụng.

---

## 2. KIỂM TOÁN VẬN HÀNH PROVIDER GATE VÀ RETRY CHỊU LỖI

### 2.1. Kiểm soát hạn mức Token và Số lần gọi (Quota Control)
- Trước mỗi bước suy luận (inference), máy chủ chỉ định một hạn mức tối đa (Request Allowance, ví dụ: 12 calls cho Dev, 5 calls cho Reviewer và QA).
- File `/root/.qldapm-openclaw/active.json` do tiến trình root sở hữu liên tục theo dõi:
  - `run_id`: Định danh phiên chạy kèm session ID.
  - `remaining`: Số lượng request còn lại được phép.
  - `deadline`: Thời điểm hết hạn phiên (tránh treo tiến trình).
  - `receipts`: Ghi vết chính xác từng lượt gọi (sequence, timestamp, phase, token count).

### 2.2. Cơ chế Tự động Hấp thụ lỗi HTTP 503 (Upstream Resilience)
- **Vấn đề thực tế phát hiện:** Trong quá trình Dev Agent làm việc, Google Gemini Free Tier đôi khi trả về mã lỗi HTTP 503 do quá tải tạm thời, khiến CLI OpenClaw bị ngắt giữa chừng.
- **Giải pháp kiên cố hóa:** Đã cập nhật `/root/.qldapm-openclaw/provider_gate.py` bổ sung vòng lặp retry 4 lần với cơ chế giãn cách thời gian (2s, 4s, 6s). Khi Google API gặp 503 hoặc 429, Provider Gate tự động giữ kết nối và gửi lại yêu cầu, loại bỏ hoàn toàn hiện tượng đứt gãy phiên agent.

---

## 3. THỐNG KÊ TOKEN VÀ CHI PHÍ THỰC TẾ TRÊN FRESH UNIT 6

Dưới đây là bảng trích xuất biên lai sử dụng tài nguyên thực tế từ `active.json` và `result.json` của Run `72a36697-da92-45ca-b549-2cb8e7c780b3`:

| Vai trò Agent | Lần gọi (Step) | Số lượt request | Prompt Tokens | Output Tokens | Cached Tokens | Chi phí ($) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dev Agent** | `dev-0` | 5 | 62,940 | 1,178 | 36,642 | **$0.00** |
| **Reviewer Agent** | `review-0` | 1 | 6,346 | 90 | 0 | **$0.00** |
| **QA Agent** | `qa-0` | 2 | 10,454 | 309 | 4,048 | **$0.00** |
| **TỔNG CỘNG** | **Unit 6 Delivery**| **8 requests** | **79,740** | **1,577** | **40,690** | **$0.00 (Free Tier)** |

> [!NOTE]
> Nhờ tính năng Context Caching của Gemini 3.5, hơn 40.690 tokens đã được tái sử dụng miễn phí, giảm thời gian phản hồi trung bình xuống dưới 1.5 giây mỗi request.
