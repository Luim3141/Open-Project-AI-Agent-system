# ADR-0003 — Lựa chọn Orchestration tối giản: Typed State Machine nội bộ thay vì LangGraph

**Trạng thái:** Accepted  
**Ngày quyết định:** 17/10/2026  
**Phạm vi áp dụng:** Phase P05 (Supervisor Agent & Multi-Agent Role Architecture), toàn bộ hệ thống QLDAPM Local Multi-Agent Upgrade V2.

---

## 1. Bối cảnh và Yêu cầu (Context)

Hệ thống QLDAPM đang phát triển kiến trúc Multi-Agent phối hợp 5 vai trò nghiệp vụ (PM, BA, FE, BE, QA) dưới sự điều phối của Supervisor Agent. Hệ thống vận hành theo các ràng buộc cốt lõi đã được xác lập tại ADR-0001 và ADR-0002:
- Chạy cục bộ trên một máy Windows duy nhất bằng Docker Desktop/WSL2 cho 5 người dùng LAN.
- Ngân sách 0 đồng (Zero budget), khai thác hợp lệ Gemini API Free Tier (15 RPM, 500 RPD, 250,000 TPM chung cho toàn bộ hệ thống).
- Bảo toàn chính sách PM-only-write, native RBAC, approval gates, idempotency, audit trail và readback proofs.
- Task P05-01 yêu cầu: Đánh giá và chọn giải pháp orchestration tối giản giữa **LangGraph** (nếu tương thích) và **Typed State Machine nội bộ**; lập ADR nêu rõ lý do và không thay đổi Gateway/SDK đang hoạt động vô cớ.

---

## 2. So sánh và Đánh giá Kỹ thuật (Technical Evaluation)

| Tiêu chí | Phương án A: LangGraph | Phương án B: Typed State Machine nội bộ (Được chọn) |
|---|---|---|
| **Dependencies & Bloat** | Kéo theo `langgraph`, `langchain-core`, `langchain`, các package shim. Tăng kích thước Docker image 150–300MB, rủi ro xung đột version với `google-genai` và `httpx`/`starlette`. | **0 dependency mới**. Tận dụng 100% stack hiện có (`pydantic` v2 strict, Python stdlib `enum`, `typing`, `sqlite3`). |
| **Kiểm soát Quota Free Tier (15 RPM / 500 RPD)** | Các vòng lặp reflection/retry ngầm trong graph framework dễ gây thất thoát token và cạn kiệt 500 RPD/ngày của 5 người dùng. | **Kiểm soát xác thực 100%**. Mọi bước chuyển trạng thái đều kiểm tra hạn mức qua `check_rpm()` và bảng `gemini_usage` trước khi gọi model. |
| **Tính tất định (Determinism)** | Phụ thuộc vào cơ chế runtime dynamic branching của bên thứ ba, khó kiểm chứng toàn bộ đường đi dữ liệu. | **Tất định hoàn toàn (100% Deterministic)**. Bảng chuyển trạng thái tường minh (`AGENT_TRANSITIONS`), không có vòng lặp vô tận. |
| **Tương thích Native RBAC & PM-only-write** | Không có ngữ cảnh native OpenProject; phải bọc thêm nhiều layer adapter để ngăn agent tự ý đề xuất mutation. | Tích hợp trực tiếp với actor IDs (6, 7, 8, 9, 10) và quyền native. Chốt chặn PM approval được cài đặt ở cấp độ chuyển trạng thái. |
| **Lưu trữ và phục hồi (Persistence)** | Cần LangGraph Checkpointer riêng (tạo thêm bảng/file lưu trữ thừa). | Sử dụng trực tiếp `Store` SQLite hiện có (`agent_tasks`, `agent_runs`), ACID qua `BEGIN IMMEDIATE` và WAL mode. |
| **Triết lý Ponytail (Senior Dev Mode)** | Thêm framework cồng kềnh cho bài toán 5 role cố định. Vi phạm nguyên tắc "The best code is the code you never wrote". | Tận dụng nền tảng `agent_models.py` và `agent_trace.py` đã có sẵn trong codebase. Diff tối thiểu, hiệu quả tối đa. |

---

## 3. Quyết định (Decision)

1. **CHỌN PHƯƠNG ÁN: Typed State Machine nội bộ.**
   - Không cài đặt LangGraph hay bất kỳ thư viện agent orchestration bên thứ ba nào.
   - Giữ nguyên Gateway và SDK `google.genai` hiện tại đang vận hành ổn định.
2. **Cơ chế triển khai State Machine:**
   - Sử dụng các định nghĩa trạng thái đã có sẵn tại `gateway/agent_models.py`:
     ```python
     RunState = Literal["QUEUED", "RUNNING", "WAITING_QUOTA", "WAITING_PROVIDER", "BLOCKED_KEY_OR_MODEL", "REVIEW", "FAILED", "COMPLETED"]
     ```
   - Các tác vụ của Supervisor và Role Agents (PM, BA, QA, DEV, Reviewer) được mô hình hóa dưới dạng một Directed Acyclic Graph (DAG) tuần tự/song song có giới hạn (bounded), với ngân sách turn tối đa (max turns <= 3) để bảo vệ quota 15 RPM / 500 RPD.
   - Mọi đề xuất thay đổi nghiệp vụ (proposal) bắt buộc phải đi qua trạng thái `REVIEW` và chờ phê duyệt tường minh từ actor PM trước khi áp dụng vào OpenProject.

---

## 4. Hệ quả và Cam kết (Consequences & Invariants)

- **Ưu điểm:**
  - Kiến trúc cực kỳ tinh gọn, không phát sinh nợ kỹ thuật (tech debt) từ dependency ngoài.
  - Tốc độ thực thi kiểm thử đơn vị nhanh (< 1 giây cho toàn bộ agent suite).
  - Codex, Gemini hoặc bất kỳ kỹ sư nào tiếp quản sau này đều có thể đọc hiểu toàn bộ luồng điều phối chỉ trong vài file mã nguồn ngắn gọn.
- **Ràng buộc duy trì:**
  - Không tự ý import thêm các framework agent (CrewAI, AutoGen, LangChain, v.v.) vào Gateway.
  - Mọi mở rộng state phải cập nhật bảng `AGENT_TRANSITIONS` và bổ sung unit test tương ứng.
