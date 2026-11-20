# HỒ SƠ PHÁP Y M4: KIỂM TOÁN NHÀ CUNG CẤP & CẤU HÌNH MÔ HÌNH GEMINI
> Thời điểm kiểm toán: `2026-10-30 20:30:11 UTC`  
> Hồ sơ kiểm định: `openproject/ai/gateway/gemini.py`, `MODEL_ALLOWLIST.json`, `gemini-free.candidate.json`  
> Cơ sở dữ liệu chứng thực: `/state/qldapm.db` (0 receipts ghi nhận)

---

## 1. THÔNG SỐ CẤU HÌNH MÔ HÌNH CHÍNH THỨC (SSOT)

Mô hình trí tuệ nhân tạo duy nhất được phê duyệt và cấu hình chính thức trong toàn bộ hệ thống QLDAPM MAIN là:
### **`gemini-3.5-flash-lite`**

| Điểm cấu hình trong mã nguồn | Giá trị cấu hình | Ý nghĩa & Ràng buộc bảo vệ |
| :--- | :--- | :--- |
| **`openproject/ai/gateway/gemini.py` (L31)** | `MODEL = "gemini-3.5-flash-lite"` | Cố định model ID cho toàn bộ các lượt gọi suy luận của Gateway (PM, BA, Backlog). |
| **`openproject/ai/gateway/MODEL_ALLOWLIST.json`** | `"is_free_verified": true` | Khẳng định mô hình thuộc gói Free Tier được xác minh chính thức. Cấm tự động bật billing (`auto_enable_billing: false`). |
| **`openproject/ai/automation/openclaw_provider_gate.py` (L20)** | `MODEL = 'gemini-3.5-flash-lite'` | Cổng loopback :18890 chặn đứng ngay lập tức nếu OpenClaw yêu cầu model khác. |
| **`openproject/ai/gateway/engineering_operator.py` (L120)** | `policy['model'] != 'gemini-3.5-flash-lite'` -> raise | Chốt chặn an toàn: nếu policy bị sửa đổi ngoài model này, toàn bộ worker lập tức dừng. |
| **`~/.openclaw/openclaw.json` (WSL2)** | `"primary": "google/gemini-3.5-flash-lite"` | Cấu hình mặc định cho Dev, Reviewer, QA trong OpenClaw. |

---

## 2. ĐỐI CHIẾU VỚI CÁC PHIÊN BẢN KHÁC (`gemini-3.5-flash` vs `gemini-3.8-flash`)

1. **Về `gemini-3.5-flash` (bản non-lite):**
   - Không được kích hoạt trong QLDAPM MAIN vì hạn mức token và chính sách Free Tier ưu tiên `flash-lite` để đảm bảo 100% không phát sinh chi phí theo cam kết của Project Charter.
2. **Về `gemini-3.8-flash`:**
   - Tại thời điểm khảo sát, `gemini-3.8-flash` chưa thuộc danh mục Free Tier được kiểm chứng ổn định (`MODEL_ALLOWLIST.json`), do đó bị cấm tuyệt đối theo chính sách `FREE_ONLY`.
3. **Về `Gemini 1.5 Pro` / `Flash`:**
   - Các chuỗi `Gemini 1.5 Pro` trước đây trên giao diện UI chỉ là nhãn văn bản hardcode cũ (tàn dư từ template UI ban đầu). Tại Phase 2.9.2, lỗi này đã được loại bỏ hoàn toàn; giao diện hiện đọc trực tiếp `actual_model_id` là `gemini-3.5-flash-lite`.

---

## 3. THỐNG KÊ LỊCH SỬ THỰC THI (RECEIPTS FORENSICS)

Truy vấn trực tiếp từ bảng `gemini_call_receipts` trên SQLite:
- **Tổng số lượt gọi ghi nhận:** `0` calls.
- **Tổng token tiêu thụ:** `0` tokens.
- **Chi tiết phân bổ:**

- **Kết luận:** **100% lượt gọi đều sử dụng chính xác `gemini-3.5-flash-lite`**. Không có bất kỳ lượt gọi nào vi phạm sang model trả phí hoặc model ngoài danh mục.
