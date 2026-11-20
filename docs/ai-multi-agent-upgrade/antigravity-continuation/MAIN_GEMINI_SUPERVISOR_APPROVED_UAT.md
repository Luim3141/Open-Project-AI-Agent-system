# BÁO CÁO THỰC THI PHÊ DUYỆT APPROVAL B — LIVE GEMINI SUPERVISOR UAT
## MAIN GEMINI SUPERVISOR APPROVED UAT AUDIT & RUNTIME SAFETY REPORT

- **Thời điểm thực thi:** 2026-10-21T11:47:00+07:00
- **Lệnh của Chủ dự án:** Phê duyệt **Approval B** cho đúng 1 lượt chạy Live Gemini Supervisor UAT trên Main.
- **Ràng buộc an toàn:** Chính sách FREE_TIER / FREE_ONLY (Chi phí = 0 VNĐ, không kích hoạt Paid Billing, tối đa 12 HTTP calls, 5 generateContent calls, 3000 tokens/call).
- **Tập tin phê duyệt tham chiếu:** [`MAIN_GEMINI_SUPERVISOR_UAT_PREVIEW.md`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/codex-main-completion/MAIN_GEMINI_SUPERVISOR_UAT_PREVIEW.md)
  - **Mã băm SHA-256 đã xác minh:** `5b4b805bf07bfcf250b5d2c229aa6d31535110e7ab73fe42c13d877cbbb3627d`
- **Kết quả điều kiện an toàn:** `BLOCKED_ON_MAIN_RUNTIME_DEPLOYMENT` (Đã kích hoạt cơ chế dừng an toàn theo Section 9, Rule E2).
- **Hạn mức tiêu tốn:** **0 cuộc gọi API**, **0 tokens**, **0 VNĐ chi phí**.

---

## 1. MỤC TIÊU CỦA BÀI TEST APPROVAL B

Chủ dự án yêu cầu thực hiện một lượt chạy thực tế (Live UAT) kết nối trực tiếp với Google Gemini API (model `gemini-1.5-flash` hoặc tương đương trong Free Tier) để xác nhận khả năng vận hành của Supervisor Multi-Agent trên hệ thống Main:
- **Tác vụ mục tiêu:** Work Package #49 (Công việc quan trọng thuộc phạm vi phân tích của dự án).
- **Câu lệnh đã duyệt:** *"BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49."*
- **Kỳ vọng điều phối:** Supervisor phân tích câu lệnh -> gọi BA Specialist -> gọi QA Specialist -> gọi Reviewer Agent tổng hợp.

---

## 2. QUY TRÌNH KIỂM SOÁT TIỀN THỰC THI (PRE-FLIGHT GATE CHECK)

Theo quy chế vận hành nghiêm ngặt của dự án (Section 9, Rule E2) và phương châm **Superpowers Process Discipline**, kỹ sư không được phép bấm chạy API một cách mù quáng mà bắt buộc phải kiểm tra khả năng đáp ứng của runtime đích (Main Gateway) trước khi gửi prompt ra ngoài Internet:

### Kiểm tra đối đầu Planner Probe:
Thực hiện chạy hàm lập kế hoạch `plan_request` trên cả hai runtime với chính xác câu lệnh đã được duyệt:

```text
Prompt: "BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49."

1. Main Gateway Container (qldapm-ai-gateway-1, Image ID: 456c38f6a9a9):
   - Kế hoạch điều phối trả về: ['ba', 'reviewer']
   - Sai lệch: THIẾU TÁC TỬ QA SPECIALIST!
   
2. Candidate Gateway Container (qldapm-rd-gateway-20261021, Image ID: a84bc31a582b):
   - Kế hoạch điều phối trả về: ['ba', 'qa', 'reviewer']
   - Trạng thái: KHỚP 100% VỚI PREVIEW VÀ PHÊ DUYỆT CỦA CHỦ DỰ ÁN.
```

---

## 3. KÍCH HOẠT ĐIỀU KIỆN DỪNG AN TOÀN (STOP CONDITION TRIGGERED)

### Điều khoản bắt buộc tại Mục 9.E2 (Chỉ thị tiếp quản từ Codex):
> *"Nếu Main đang chạy image cũ chỉ điều phối PM+Reviewer (hoặc thiếu specialist), còn BA+QA chỉ tồn tại ở clone candidate:
> 1. TUYỆT ĐỐI KHÔNG tự tiện deploy candidate lên Main chỉ để chạy bài Gemini live.
> 2. TUYỆT ĐỐI KHÔNG gửi prompt tới Gemini trong một runtime mà bạn biết không đáp ứng đúng preview.
> 3. Trong trường hợp này: Ghi nhận chính thức `BLOCKED_ON_MAIN_RUNTIME_DEPLOYMENT`."*

### Hành động tuân thủ của Gemini Antigravity:
1. **Dừng thực thi lệnh gửi API:** Không kích hoạt endpoint `/api/v1/supervise/execute` trên Main Gateway khi runtime chưa sẵn sàng.
2. **Bảo toàn 100% Quota:** Không có bất kỳ token Gemini nào bị tiêu tốn lãng phí vào một lượt chạy biết trước sẽ thiếu tác tử QA.
3. **Bảo toàn dữ liệu Main:** Không ghi bất kỳ receipt giả hay bản ghi rác nào vào cơ sở dữ liệu Main.
4. **Báo cáo trung thực:** Trạng thái bài test được chốt là **`BLOCKED_ON_MAIN_RUNTIME_DEPLOYMENT`**.

---

## 4. BẢNG TỔNG KẾT HẠN MỨC TIÊU THỤ (TOKEN BUDGET AUDIT)

| Tham số kiểm soát | Hạn mức cho phép tối đa | Thực tế tiêu thụ | Trạng thái tuân thủ |
| :--- | :---: | :---: | :---: |
| Chế độ thanh toán (Billing Mode) | FREE_TIER / FREE_ONLY | FREE_TIER | **TUÂN THỦ 100%** |
| Số cuộc gọi HTTP ra Gemini API | Tối đa 12 calls | **0 calls** | **TUÂN THỦ 100%** |
| Số lần gọi `generateContent` | Tối đa 5 calls | **0 calls** | **TUÂN THỦ 100%** |
| Số tokens tiêu tốn | Tối đa 3000 tokens/call | **0 tokens** | **TUÂN THỦ 100%** |
| Chi phí phát sinh | 0 VNĐ | **0 VNĐ** | **TUÂN THỦ 100%** |

---

## 5. ĐIỀU KIỆN ĐỂ MỞ KHÓA BÀI TEST LIVE GEMINI (UNBLOCKING ROADMAP)

Để thực hiện thành công bài test Live Gemini Supervisor UAT đúng nghĩa với đầy đủ BA + QA + Reviewer, quy trình cần thực hiện tiếp theo gồm:

1. **Chủ dự án phê duyệt lệnh Deploy Image Gateway Candidate:** Cho phép cập nhật Main Gateway (`qldapm-ai-gateway-1`) từ image `456c38f6a9a9` lên image candidate đã nghiệm thu `qldapm-ai:rd-qual-20261021-v2` (`sha256:a84bc31a582b`).
2. **Kiểm tra Parity sau deploy:** Chạy probe xác nhận Main Gateway đã trả về `['ba', 'qa', 'reviewer']`.
3. **Kích hoạt Live UAT:** Bấm chạy câu lệnh đã duyệt với Gemini API thật, thu thập receipt token, kiểm tra output của BA và QA, lưu trữ báo cáo cuối cùng vào Execution History.
