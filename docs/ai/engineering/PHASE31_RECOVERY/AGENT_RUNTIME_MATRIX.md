# MA TRẬN NĂNG LỰC VẬN HÀNH TÁC NHÂN (AGENT RUNTIME MATRIX)
## DỰ ÁN: QLDAPM MAIN — AGENT WORKFORCE TRANSPARENCY

---

### 1. Phân loại và bản chất vận hành thực tế của đội ngũ Agent

Nhằm đảm bảo tính minh bạch pháp y cao nhất, hệ thống phân định rõ ràng bản chất kỹ thuật của từng tác nhân:

| Tác nhân (Agent) | Vai trò hệ thống | Môi trường thực thi (Runtime Environment) | Cơ chế suy luận / Xử lý (Reasoning Engine) | Mô hình cấu hình (Configured Model) | Số lượt gọi LLM (LLM Calls) | Ghi chú vận hành thực tế |
|---|---|---|---|---|---|---|
| **Supervisor** | Điều phối toàn cục & Kiểm soát vòng đời | Container `qldapm-ai-gateway-1` (Python 3.12 / FastAPI) | Điều phối tất định bằng mã nguồn Python (Deterministic Python Code) | Không dùng LLM trực tiếp | **0 LLM Calls** | Quản lý hàng đợi, task claim, lock_version, kiểm tra idempotency, ghi chép SQLite. |
| **Product Manager (PM)** | Lập kế hoạch & Quản lý yêu cầu | Container `qldapm-ai-gateway-1` | Suy luận qua Google Gemini REST API | `gemini-3.5-flash-lite` (Free Tier) | Dynamic (Theo yêu cầu PM) | Phân rã mục tiêu kỹ thuật, tạo đề xuất (proposals) cho Backlog. Chi phí $0.00. |
| **Business Analyst (BA)** | Phân tích nghiệp vụ & Tiêu chí nghiệm thu | Container `qldapm-ai-gateway-1` | Suy luận qua Google Gemini REST API | `gemini-3.5-flash-lite` (Free Tier) | Dynamic (Theo yêu cầu BA) | Soạn thảo User Stories, Acceptance Criteria (AC), phân rã cấu trúc WBS. |
| **Developer (Dev)** | Thực thi mã nguồn & Sửa đổi tệp tin | Sandbox WSL2 Ubuntu cô lập (OpenClaw Node.js v24.22.2) | Phiên làm việc OpenClaw + Công cụ tệp tin cục bộ | `gemini-3.5-flash-lite` | Đã lưu 313 events, 15 sessions | Thao tác trực tiếp trên Git Worktree cô lập. Bị chặn mọi truy cập ra mạng Internet. |
| **Code Reviewer** | Thẩm định chất lượng mã nguồn & Diff | Sandbox WSL2 Ubuntu (OpenClaw) / Gateway | **Chính sách kiểm tra Diff cục bộ (Local-Policy Exact-Diff)** | **KHÔNG DÙNG LLM** | **0 LLM Calls** | So sánh unified diff với tiêu chí chấp nhận. Không tiêu tốn token của người dùng. |
| **QA Engineer** | Kiểm thử tự động & Bằng chứng nghiệm thu | Sandbox WSL2 Ubuntu (OpenClaw) / Gateway | **Trình chạy kiểm thử tự động (Pytest Runner)** | **KHÔNG DÙNG LLM** | **0 LLM Reasoning** | Chạy kiểm thử tự động `pytest`, đọc kết quả XML/JSON và ký số bằng chứng nghiệm thu (Admission Proof). |

---

### 2. Dấu vết phiên làm việc OpenClaw (OpenClaw Forensic Evidence)

Dữ liệu lưu trữ trong cơ sở dữ liệu SQLite của OpenClaw (`~/.openclaw/agents/`):
- **Agent Dev:** 15 sessions ghi nhận, 313 sự kiện quỹ đạo (`trajectory_runtime_events`), 377 mục ghi âm (`transcript_events`), 144 khối bộ nhớ (`memory_chunks`).
- **Agent Reviewer:** 5 sessions ghi nhận, 37 sự kiện quỹ đạo, 33 mục ghi âm, 79 khối bộ nhớ.
- **Agent QA:** 4 sessions ghi nhận, 44 sự kiện quỹ đạo, 48 mục ghi âm, 8 khối bộ nhớ.
- **Tổng cộng:** **24 sessions**, **394 trajectory events**, **458 transcript events**, **231 memory chunks**.

Mọi hành động sửa mã nguồn của Dev và thẩm định của Reviewer/QA đều được lưu trữ nguyên tử, có thể kiểm toán bất kỳ lúc nào mà không cần gọi lại API ngoài.

---

### 3. Cam kết kiểm soát chi phí (Zero-Cost Gemini Policy)
- Tất cả các lệnh gọi Gemini API từ Gateway đều hướng tới mô hình **`gemini-3.5-flash-lite`**.
- Hạn mức Free Tier: RPM = 15, TPM = 1,000,000, RPD = 1,500.
- Circuit Breaker: Gateway tự động ngắt kết nối (Fail-safe) nếu vượt ngưỡng an toàn cục bộ; tuyệt đối không fallback sang các model trả phí (Pro / Ultra).
