# HỒ SƠ PHÁP Y M2: KIỂM TOÁN AGENT REGISTRY & VAI TRÒ CÁC TÁC NHÂN
> Thời điểm kiểm toán: `2026-10-30 20:27:57 UTC`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Tham chiếu mã nguồn: `openproject/ai/gateway/agent_registry.py`, `engineering_personas.py`, `engineering_units.py`

---

## 1. KIỂM TOÁN TỔNG THỂ AGENT REGISTRY

Lực lượng Agent trong QLDAPM MAIN được quản lý tập trung qua singleton `_GLOBAL_REGISTRY` (`AgentRegistry`) trong `openproject/ai/gateway/agent_registry.py`.

Mỗi Agent có:
- **`AgentDefinition`:** Ràng buộc chặt chẽ bằng Pydantic `extra="forbid"`, định nghĩa `provider`, `allowed_tools`, `max_turns`, `max_tokens_per_call`, `timeout_seconds`.
- **`engineering_profile(role)`:** Cung cấp siêu dữ liệu thực thi cho Project 6, phân định rõ ràng giữa môi trường Python Gateway và OpenClaw WSL2.
- **`Persona Instruction`:** Định hình phong cách và ranh giới theo chuẩn Agency Agents (`engineering_personas.py`).

---

## 2. BẢNG PHÂN TÍCH CHI TIẾT TỪNG VAI TRÒ (PERSONA DEEP-DIVE)

### 2.1. Supervisor (Tổng Quản Điểu Phối)
- **Mã nguồn:** `SupervisorHandler` trong `agent_registry.py`, `supervisor.py`, `engineering_auto.py`.
- **Cơ chế suy luận:** **Deterministic DAG Planning (Không gọi LLM)**.
- **Trách nhiệm cốt lõi:**
  1. Giành quyền điều khiển độc quyền (`ENGINEERING_LOCK`).
  2. Quản lý vòng đời tác vụ (Claim -> Stage handoff -> Bounded rework -> Completion -> Safe OFF).
  3. Kiểm soát ngân sách Gemini Free Tier và hạn mức quay vòng.
  4. Tự động ngắt (`AUTO OFF`) an toàn khi đạt trạng thái `ALL_DELIVERED`.
- **Công cụ cho phép:** `plan_request`, `aggregate_proposal`, `dispatch_agent`, `existing queue`, `Native scoped publisher`, `SecondBrain`.

### 2.2. PM Agent (Project Manager)
- **Mã nguồn:** `PMAgent` trong `pm_agent.py`, `engineering_personas.py`.
- **Cơ chế suy luận:** **Gateway Gemini Reasoning** (`gemini-3.5-flash-lite`).
- **Trách nhiệm cốt lõi:**
  1. Phân tích tiến độ Sprint, công việc quá hạn (Overdue), và các điểm nghẽn (Blockers).
  2. Xác định thứ tự ưu tiên các Work Packages trên Native Backlog.
  3. Lập kế hoạch phân bổ tác vụ cho Dev.
- **Công cụ cho phép:** `analyze_overdue`, `analyze_blockers`, `analyze_workload`, `analyze_sprint_risks`.

### 2.3. BA Agent (Business Analyst)
- **Mã nguồn:** `BAAgent` trong `ba_agent.py`, `engineering_personas.py`.
- **Cơ chế suy luận:** **Gateway Gemini Reasoning** (`gemini-3.5-flash-lite`).
- **Trách nhiệm cốt lõi:**
  1. Chuẩn hóa yêu cầu người dùng thành User Stories và Tiêu chí chấp nhận Gherkin (`Given/When/Then`).
  2. Phát hiện sự mơ hồ (Ambiguity Detection) trong mô tả nghiệp vụ.
  3. Định nghĩa các trường hợp biên (Edge Cases).
- **Công cụ cho phép:** `draft_user_story`, `draft_ac`, `detect_ambiguity`, `draft_dependencies`.

### 2.4. Dev Agent (Senior Developer)
- **Mã nguồn:** `DEVAgent` trong `dev_agent.py`, tích hợp OpenClaw WSL2 daemon (`openclaw.json`).
- **Cơ chế suy luận:** **OpenClaw Sandbox Coding** (Model: `google/gemini-3.5-flash-lite` qua Provider Gate :18890).
- **Trách nhiệm cốt lõi:**
  1. Tiếp nhận đặc tả AC từ BA/PM và thực thi mã nguồn trong Git worktree riêng (`~/engineering/feedback-4d13e695555a8d44`).
  2. Tuân thủ triết lý TDD (Test-Driven Development) và debugging có hệ thống.
  3. Tạo git commits và tạo unified diff sạch.
- **Skill:** `engineering-development`.
- **Công cụ cho phép trong OpenClaw:** `read`, `write`, `edit`, `exec`, `process` (chỉ trong thư mục workspace, cấm truy cập mạng internet).

### 2.5. Reviewer Agent (Code Reviewer / Reality Checker)
- **Mã nguồn:** `ReviewerAgent` trong `reviewer_agent.py`.
- **Cơ chế suy luận:** **`local-policy` (0 LLM Calls, 0 Token Cost)**.
- **Trách nhiệm cốt lõi:**
  1. So sánh trực tiếp unified diff với tiêu chí chấp nhận ACs.
  2. Kiểm tra tính toàn vẹn (không xóa code bừa bãi, không tạo side-effects ngoài scope).
  3. Xuất JSON verdict (`PASSED` hoặc `REWORK_REQUIRED`) kèm trích dẫn chính xác file và số dòng.
- **Skill:** `engineering-review`.
- **Công cụ trong OpenClaw:** `read` only (cấm ghi, cấm chạy lệnh shell `exec/process`).

### 2.6. QA Agent (Quality Assurance Engineer)
- **Mã nguồn:** `QAAgent` trong `qa_agent.py`, tích hợp OpenClaw WSL2 daemon.
- **Cơ chế suy luận:** **OpenClaw Sandbox Execution** (Model: `google/gemini-3.5-flash-lite`).
- **Trách nhiệm cốt lõi:**
  1. Chạy bộ kiểm thử tự động thật (`pytest`) trên workspace.
  2. Thu thập mã thoát thực tế (`exit code 0` cho pass) và lưu trữ artifacts (`acceptance-0.xml`).
  3. Ánh xạ từng kết quả kiểm thử vào tiêu chí chấp nhận AC1–AC9.
- **Skill:** `engineering-qa`.
- **Công cụ trong OpenClaw:** `read`, `exec` (chỉ chạy lệnh test chỉ định, cấm sửa mã nguồn).

### 2.7. Delivery / Git Worker
- **Mã nguồn:** `engineering_worker.py`, `engineering_delivery.py`, `engineering_github_sync.py`.
- **Trách nhiệm cốt lõi:**
  1. Đẩy branch lên kho GitHub đích (`Luim3141/mini-task-manager`).
  2. Mở Pull Requests (#1 đến #5) tương ứng với từng giai đoạn tính năng.
  3. Đồng bộ trạng thái review và PR checks về OpenProject Command Center.

---

## 3. KẾT LUẬN KIỂM TOÁN VAI TRÒ AGENT

1. **Phân định ranh giới rành mạch:** Không có sự chồng chéo giữa các Agent. Supervisor là code deterministic, PM/BA là Gateway reasoning, Dev/QA là sandbox execution, Reviewer là exact-diff local inspection.
2. **Bảo toàn nguyên tắc Ponytail:** Giữ cấu trúc tối giản nhất đáp ứng đầy đủ quy trình kỹ thuật phần mềm chuẩn mực.
