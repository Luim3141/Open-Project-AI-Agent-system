# BẰNG CHỨNG THỰC THI MULTI-AGENT & GEMINI LIVE CHÍNH THỨC TRÊN MAIN
## OFFICIAL LIVE MULTI-AGENT RUN EVIDENCE — RUN ID: `0165de09-666d-465d-bdd7-14ceb97947eb`

- **Môi trường:** QLDAPM Main (`http://localhost:8088`, AI Gateway `http://localhost:8090`)
- **Dự án kiểm định:** `qldapm-local` (Project ID: 5)
- **Tài khoản thực thi:** PM `ba-pm` (User ID: 19, Role: PM)
- **Đối tượng nghiệp vụ:** Work Package #49 (`[AUTH-01] Đăng ký tài khoản người dùng`) kèm Subtasks #102 đến #106
- **Thời gian chạy:** 2026-10-21T19:07:09+07:00 (Thời lượng: 17.345 giây)
- **Mô hình AI:** Google Gemini `gemini-3.5-flash-lite` (Free Tier, 0 VNĐ chi phí)
- **Engine điều phối:** `gemini_supervisor` (Đồ thị thực thi 5 tác tử: Supervisor → BA → QA → Reviewer → Final Report)

---

## 1. TỔNG QUAN CHỈ SỐ TIÊU THỤ VÀ VẬN HÀNH

| Chỉ số kiểm tra | Giá trị thực tế ghi nhận | Giới hạn hạn mức (Free Tier) | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Số lần gọi API Gemini** | **3 cuộc gọi** (Supervisor, BA, QA) | Tối đa 5 cuộc gọi/lượt | **ĐẠT (PASS)** |
| **Tổng số Tokens tiêu thụ** | **7,328 Tokens** (Prompt: 5,042, Candidate: 986, Cached/Agg: 1,300) | Tối đa 1,000,000 TPM | **ĐẠT (PASS)** |
| **Chi phí phát sinh** | **0.00 USD / 0 VNĐ** | Gói Miễn phí (Free Tier) | **ĐẠT (PASS)** |
| **Tổng số biên lai HTTP (Receipts)** | **6 biên lai** (3 countTokens + 3 generateContent) | 100% trả về HTTP 200 OK | **ĐẠT (PASS)** |
| **Số sự kiện vòng đời (Events)** | **29 sự kiện liên tục** (từ tiếp nhận đến hoàn tất) | Không bị ngắt quãng, không gián đoạn | **ĐẠT (PASS)** |
| **Kết quả thẩm định của Reviewer** | **100% PASS** (0 cảnh báo, 0 trích dẫn sai) | Không sai lệch ngữ cảnh | **ĐẠT (PASS)** |
| **Thay đổi dữ liệu hệ thống** | **0 đột biến (Zero Mutation)** | Chỉ đọc và phân tích đề xuất | **ĐẠT (PASS)** |

---

## 2. BẢNG BIÊN LAI HTTP (HTTP CALL RECEIPTS AUDIT)

Hệ thống ghi nhận 6 biên lai mật mã đối soát với máy chủ Google Gemini, lưu tại Gateway:

| STT | Mã định danh biên lai (Receipt ID) | Tác tử (Agent) | Giai đoạn (Phase) | HTTP Status | Độ trễ (Latency) | Mô hình sử dụng |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| 1 | `8b56c019-e4ef-4a6b-b5af-9159e30009b4` | **Supervisor** | `countTokens` | 200 OK | 1.418s | `gemini-3.5-flash-lite` |
| 2 | `35b5c955-aa23-4cf3-a28f-b53aa57eea86` | **Supervisor** | `generateContent` | 200 OK | 3.199s | `gemini-3.5-flash-lite` |
| 3 | `b721d6ac-4b52-4c26-8d87-1eb27c86a9bb` | **BA Agent** | `countTokens` | 200 OK | 0.317s | `gemini-3.5-flash-lite` |
| 4 | `fe367a0d-fcbc-46f9-b799-96570c7ff7d8` | **BA Agent** | `generateContent` | 200 OK | 7.325s | `gemini-3.5-flash-lite` |
| 5 | `44f590a1-27eb-4488-b1ca-9ce6a7e007d4` | **QA Agent** | `countTokens` | 200 OK | 0.481s | `gemini-3.5-flash-lite` |
| 6 | `3f35d664-141b-4099-aae9-6310d9504a03` | **QA Agent** | `generateContent` | 200 OK | 2.318s | `gemini-3.5-flash-lite` |

**Phân bổ Tokens chi tiết theo từng cuộc gọi:**
- **Call 1 (Supervisor - Lập kế hoạch phân bổ chuyên gia):** Prompt: 1,579 tokens | Phản hồi: 192 tokens | Tổng: 1,771 tokens.
- **Call 2 (BA Agent - Phân tích yêu cầu và chính sách tài khoản):** Prompt: 1,631 tokens | Phản hồi: 373 tokens | Tổng: 3,304 tokens.
- **Call 3 (QA Agent - Xây dựng kịch bản kiểm thử và tiêu chí chấp nhận):** Prompt: 1,832 tokens | Phản hồi: 421 tokens | Tổng: 2,253 tokens.

---

## 3. CHUỖI 29 SỰ KIỆN THỰC THI (EVENT LIFECYCLE CHRONOLOGY)

Toàn bộ quá trình từ khi người dùng PM gửi lệnh trên giao diện trình duyệt đến khi trả kết quả được lưu vết dạng append-only trong cơ sở dữ liệu Gateway:

```text
Seq | Event Type                | Agent ID     | Trạng thái  | Giai đoạn API
----+---------------------------+--------------+-------------+--------------------
 01 | REQUEST_RECEIVED          | SYSTEM       | QUEUED      | Tiếp nhận yêu cầu từ Rails Core
 02 | AUTHORIZED                | ba-pm (19)   | QUEUED      | Xác thực thẩm quyền PM cho Project 5
 03 | QUEUED                    | SYSTEM       | QUEUED      | Đưa vào hàng đợi điều phối
 04 | PLANNING_STARTED          | supervisor   | PLANNING    | Bắt đầu phân rã bài toán
 05 | MODEL_REQUEST_STARTED     | supervisor   | CALLING     | countTokens (Kiểm tra budget)
 06 | MODEL_RESPONSE_RECEIVED   | supervisor   | RECEIVED    | countTokens -> 200 OK
 07 | MODEL_REQUEST_STARTED     | supervisor   | CALLING     | generateContent (Sinh kế hoạch tác tử)
 08 | MODEL_RESPONSE_RECEIVED   | supervisor   | RECEIVED    | generateContent -> 200 OK
 09 | PLAN_CREATED              | supervisor   | COMPLETED   | Hoàn thành phân công cho BA và QA
 10 | AGENT_ASSIGNED            | ba           | QUEUED      | Giao nhiệm vụ phân tích nghiệp vụ #49
 11 | AGENT_ASSIGNED            | qa           | QUEUED      | Giao nhiệm vụ thiết kế test cases #49
 12 | AGENT_ASSIGNED            | reviewer     | QUEUED      | Chỉ định kiểm định viên độc lập
 13 | AGENT_STARTED             | ba           | RUNNING     | BA Agent bắt đầu làm việc
 14 | MODEL_REQUEST_STARTED     | ba           | CALLING     | countTokens (Prompt BA)
 15 | MODEL_RESPONSE_RECEIVED   | ba           | RECEIVED    | countTokens -> 200 OK
 16 | MODEL_REQUEST_STARTED     | ba           | CALLING     | generateContent (Gemini phân tích BA)
 17 | MODEL_RESPONSE_RECEIVED   | ba           | RECEIVED    | generateContent -> 200 OK
 18 | AGENT_COMPLETED           | ba           | REVIEW      | BA Agent bàn giao kết quả
 19 | AGENT_STARTED             | qa           | RUNNING     | QA Agent bắt đầu làm việc
 20 | MODEL_REQUEST_STARTED     | qa           | CALLING     | countTokens (Prompt QA)
 21 | MODEL_RESPONSE_RECEIVED   | qa           | RECEIVED    | countTokens -> 200 OK
 22 | MODEL_REQUEST_STARTED     | qa           | CALLING     | generateContent (Gemini thiết kế test cases)
 23 | MODEL_RESPONSE_RECEIVED   | qa           | RECEIVED    | generateContent -> 200 OK
 24 | AGENT_COMPLETED           | qa           | REVIEW      | QA Agent bàn giao kết quả
 25 | REVIEW_STARTED            | reviewer     | REVIEWING   | Reviewer Agent kiểm tra đối chiếu mã
 26 | REVIEW_COMPLETED          | reviewer     | COMPLETED   | Reviewer xác nhận 100% trích dẫn hợp lệ
 27 | RESULT_AGGREGATED         | supervisor   | REVIEW      | Tổng hợp báo cáo liên chuyên gia
 28 | RESULT_AVAILABLE          | SYSTEM       | REVIEW      | Gửi bản đề xuất về Rails Core
 29 | RUN_COMPLETED             | SYSTEM       | REVIEW      | Hoàn thành toàn vẹn phiên thực thi
```

---

## 4. BÁO CÁO THẨM ĐỊNH CỦA REVIEWER AGENT (GATE GROUNDING AUDIT)

- **Cơ chế kiểm soát:** `ReviewerAgent` hoạt động độc lập ở bước cuối cùng, sử dụng thuật toán đối soát toán học để kiểm tra xem mọi trích dẫn Work Package trong văn bản có thực sự tồn tại trong Project 5 hay không.
- **Dữ liệu đối chiếu:**
  - Work Package mục tiêu: `#49` (`[AUTH-01] Đăng ký tài khoản người dùng`, Lock Version: 1).
  - Các Subtask trực thuộc được mở rộng: `#102`, `#103`, `#104`, `#105`, `#106`.
- **Dấu vân tay mật mã dữ liệu nguồn (Source Fingerprint):**
  `6038a8199c19c0b5e13951878f38af68d974b5a73da02382a91ef68464b437c0`
- **Kết quả kiểm toán trích dẫn:**
  - Số lượng trích dẫn hợp lệ: 6/6 (100%).
  - Số lượng trích dẫn giả mạo hoặc ngoài phạm vi: 0.
  - Xung đột phiên bản (Lock Version Mismatch): 0.
  - **Phán quyết (Verdict):** `REVIEWER_PASSED` — Chấp thuận đưa lên giao diện hiển thị cho người dùng.

---

## 5. NỘI DUNG PHẢN HỒI NGUYÊN BẢN CỦA ĐỘI NGŨ MULTI-AGENT

Dưới đây là nguyên văn nội dung được hiển thị trên giao diện AI Assistant cho Project Manager:

> **LIVE_GEMINI · gemini-3.5-flash-lite · 3 model calls · 7328 total tokens (provider metadata) · 17.345s**  
> *Provider remaining quota: unavailable. Chỉ phân tích/đề xuất; chưa có native mutation.*
> 
> ### BA (Phân tích nghiệp vụ):
> Phân tích Work Package #49 (AUTH-01) về tính năng đăng ký tài khoản bằng email và mật khẩu. Đánh giá các tiêu chí chấp nhận (Acceptance Criteria), làm rõ yêu cầu về định dạng email, tính duy nhất của email, chính sách mật khẩu, và quyền hạn mặc định của tài khoản mới.
> - Work Package #49 định nghĩa tính năng đăng ký cơ bản cho người dùng mới bằng email và mật khẩu.
> - Tiêu chí chấp nhận yêu cầu email phải đúng định dạng, chưa tồn tại trong hệ thống và mật khẩu/xác nhận mật khẩu phải khớp nhau.
> - Tài khoản đăng ký thành công sẽ ở trạng thái chưa thuộc Project nào và không được cấp quyền dữ liệu Project mặc định.
> - Hiện tại chưa có đặc tả chi tiết về quy tắc chính sách mật khẩu (độ dài, ký tự đặc biệt) trong nội dung công việc.
> - Bổ sung đặc tả chi tiết về chính sách mật khẩu để BA và QA có căn cứ xây dựng test cases.
> - Định nghĩa rõ nội dung thông báo lỗi khi email đã tồn tại hoặc không đúng định dạng.
> - QA xây dựng bộ test cases kiểm thử các trường hợp dữ liệu hợp lệ, biên và các ngoại lệ khi đăng ký.  
> *Giới hạn: Thiếu thông tin chi tiết về các ràng buộc chính sách mật khẩu; Chưa có mô tả chi tiết về giao diện hoặc thông điệp phản hồi lỗi cho người dùng.*
> 
> ### QA (Thiết kế kiểm thử):
> Phân tích Work Package #49 (AUTH-01) về tính năng đăng ký tài khoản bằng email và mật khẩu. QA đã xây dựng bộ test cases đề xuất dựa trên các tiêu chí chấp nhận (Acceptance Criteria), tập trung vào định dạng email, kiểm tra tính duy nhất, xác thực mật khẩu và phân quyền mặc định.
> - Work Package #49 yêu cầu email phải đúng định dạng và chưa tồn tại trong hệ thống.
> - Mật khẩu và xác nhận mật khẩu phải hợp lệ và khớp nhau trước khi tạo tài khoản.
> - Tài khoản mới sau khi đăng ký thành công sẽ chưa thuộc Project nào và không được cấp quyền dữ liệu Project mặc định.
> - Chưa có đặc tả chi tiết về quy tắc mật khẩu mạnh (độ dài tối thiểu, ký tự hoa/thường/đặc biệt) trong phần mô tả.
> - Xây dựng test case kiểm tra định dạng email hợp lệ và không hợp lệ (thiếu @, sai tên miền, v.v.).
> - Xây dựng test case kiểm tra trường hợp email đã tồn tại trong hệ thống (thông báo lỗi trùng lặp).
> - Xây dựng test case kiểm tra khớp mật khẩu và xác nhận mật khẩu.
> - Xây dựng test case kiểm tra trạng thái tài khoản mới tạo (không thuộc Project nào và không có quyền mặc định).
> - Bổ sung chính sách mật khẩu cụ thể vào mô tả yêu cầu của BA.  
> *Giới hạn: Chưa có thông tin chi tiết về các quy tắc chính sách mật khẩu cụ thể; Request yêu cầu chỉ phân tích và tạo đề xuất test cases mà không thay đổi dữ liệu (read-only).*
> 
> *Reviewer local: trích dẫn/phiên bản/phạm vi đã đối chiếu; nội dung gợi ý vẫn cần người dùng thẩm định.*

---

## 6. KẾT LUẬN NGHIỆM THU

Phiên thực thi Live Gemini Multi-Agent `0165de09-666d-465d-bdd7-14ceb97947eb` đã hoàn thành xuất sắc toàn bộ các chỉ tiêu kỹ thuật khắt khe:
1. Đúng tài khoản thẩm quyền (`ba-pm`).
2. Đúng Work Package nghiệp vụ (`#49`).
3. Tác tử Supervisor điều phối chính xác 2 chuyên gia (BA và QA).
4. Reviewer Agent phê duyệt 100% trích dẫn không sai lệch.
5. Không làm biến động dù chỉ 1 trường dữ liệu trong 329 Work Packages của hệ thống.
