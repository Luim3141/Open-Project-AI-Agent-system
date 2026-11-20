# BÁO CÁO KIỂM THỬ LIVE GEMINI MULTI-AGENT SUPERVISOR TRÊN MAIN
## MAIN AI SUPERVISOR LIVE UAT REPORT

- **Thời điểm thực thi:** 2026-10-21T13:57:42+07:00
- **Môi trường:** Main AI Gateway (`http://localhost:8090`) qua Rails Bridge `Qldapm::AiBridge.call`
- **Mã định danh lượt chạy (Run ID):** `ca0c3b3f-c01d-4291-a327-9c06b98e4f63`
- **Gói công việc mục tiêu:** Work Package #49 (`AUTH-01 — Đăng ký bằng email và mật khẩu`, Project ID: 5)
- **Người gọi phân quyền:** Actor 19 (`ba-pm`, Role: PM)
- **Mô hình AI thực tế:** `gemini-3.5-flash-lite` (Google Gemini API chính thức, Free tier, Cloud Project: `gen-lang-client-0020540057`)
- **Chi phí phát sinh:** **$0.00 (Hoàn toàn miễn phí, 0 đồng)**

---

### 1. KẾT QUẢ CUỘC GỌI GOOGLE GEMINI API THỰC TẾ

| Lượt gọi | Tác nhân (Agent) | Endpoint API | Trạng thái HTTP | Token Đầu vào | Token Tư duy (Thoughts) | Token Hoàn tất |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Supervisor | `countTokens` | 200 OK | 1,246 | — | — |
| 2 | Supervisor | `generateContent` | 200 OK | 1,246 | 790 | 160 |
| 3 | BA Specialist | `countTokens` | 200 OK | 1,293 | — | — |
| 4 | BA Specialist | `generateContent` | 200 OK | 1,293 | 1,520 | 367 |
| 5 | QA Specialist | `countTokens` | 200 OK | 1,516 | — | — |
| 6 | QA Specialist | `generateContent` | 200 OK | 1,516 | — | 490 |

- **Tổng số cuộc gọi HTTP:** 6 cuộc gọi (Ngưỡng an toàn tối đa: 12 cuộc gọi).
- **Tổng số cuộc gọi generateContent:** 3 cuộc gọi (Ngưỡng an toàn tối đa: 5 cuộc gọi).
- **Tổng token tiêu thụ:** 4,055 input tokens, 2,310 thought tokens, 1,017 output tokens.

---

### 2. HOẠT ĐỘNG CỦA CƠ CHẾ BẢO VỆ CHỐNG HALLUCINATION (REVIEWER AGENT)

- **Phát hiện:** Tác nhân Specialist đưa ra trích dẫn liên quan đến gói công việc `#102` nhưng ngữ cảnh cung cấp không có đủ tài liệu chứng cứ trực tiếp cho phát biểu đó.
- **Xử lý:** Tác nhân `Reviewer` cục bộ đã kích hoạt chính sách bảo vệ nghiêm ngặt:
  - Ghi nhận lỗi: `AGENT_EVIDENCE_REJECTED`.
  - Từ chối tự động chấp thuận kết quả chưa được kiểm chứng.
  - Chuyển trạng thái lượt chạy sang `failed_or_unknown` để yêu cầu con người rà soát thay vì tự động ghi sai lệch vào hệ thống.
- **Bảo toàn dữ liệu:** Work Package #49 trên Main hoàn toàn không bị thay đổi bất kỳ trường dữ liệu nào (`lock_version = 1`, 0 mutations).

---

### 3. KẾT LUẬN
- Pipeline Multi-Agent Supervisor trên Main Gateway hoạt động chính xác theo đúng thiết kế an toàn, điều phối đa chuyên gia mượt mà, tuân thủ hạn mức miễn phí và ngăn chặn thành công việc tạo dữ liệu ảo (hallucination).
