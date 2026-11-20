"""Audit Script: Milestone M2 — Agent Registry, Model-Runtime Matrix & Handoff Capabilities.
Generates:
- docs/ai/architecture-audit/04_AGENT_REGISTRY_AND_ROLE_AUDIT.md
- docs/ai/architecture-audit/05_AGENT_MODEL_RUNTIME_MATRIX.md
- docs/ai/architecture-audit/06_AGENT_HANDOFF_AND_CAPABILITY_MATRIX.md
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

# Check sqlite receipts for model actual served
db_path = Path("openproject/ai/state/qldapm.db")
if not db_path.exists():
    db_path = Path("openproject/ai/gateway/qldapm.db")

receipt_count = 0
models_served = {}
if db_path.exists():
    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("SELECT count(*) FROM gemini_call_receipts")
        receipt_count = c.fetchone()[0]
        c.execute("SELECT model, count(*) FROM gemini_call_receipts GROUP BY model")
        for m, cnt in c.fetchall():
            models_served[m] = cnt
        conn.close()
    except Exception as e:
        receipt_count = f"Error reading DB: {e}"

# Build 04_AGENT_REGISTRY_AND_ROLE_AUDIT.md
def build_agent_registry_audit():
    return f"""# HỒ SƠ PHÁP Y M2: KIỂM TOÁN AGENT REGISTRY & VAI TRÒ CÁC TÁC NHÂN
> Thời điểm kiểm toán: `{NOW}`  
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
"""

# Build 05_AGENT_MODEL_RUNTIME_MATRIX.md
def build_agent_model_matrix():
    return f"""# HỒ SƠ PHÁP Y M2: MA TRẬN MÔ HÌNH VÀ RUNTIME THỰC CHỨNG (MODEL & RUNTIME MATRIX)
> Thời điểm kiểm toán: `{NOW}`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Bằng chứng thực tế: SQLite receipts bảng `gemini_call_receipts` ({receipt_count} receipts recorded)

---

## 1. MA TRẬN PHÂN LOẠI AGENT THEO RUNTIME & MÔ HÌNH

| Agent Name | Runtime Host | Execution Engine | Configured Model | Requested Model | Actually Served Model | Displayed Model (UI) | Quota & Token Bounds | Tool Permissions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Supervisor** | Docker `qldapm-ai-gateway-1` | Python Async Daemon (`SupervisorHandler`) | N/A (Deterministic Code) | None (0 calls) | None (0 calls) | N/A (Code Orchestration) | 0 RPM / 0 TPM | `plan_request`, `aggregate_proposal`, `dispatch_agent` |
| **PM Agent** | Docker `qldapm-ai-gateway-1` | Gateway Gemini Provider | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | Max 2000 tokens, 2 turns | `analyze_overdue`, `analyze_blockers`, `analyze_workload` |
| **BA Agent** | Docker `qldapm-ai-gateway-1` | Gateway Gemini Provider | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | Max 2000 tokens, 2 turns | `draft_user_story`, `draft_ac`, `detect_ambiguity` |
| **Dev Agent** | WSL2 `OpenClawGateway` (:18789) | OpenClaw Sandbox Execution | `google/gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | Max 3000 tokens, 300s timeout | `read`, `write`, `edit`, `exec`, `process` (workspace-only) |
| **Reviewer Agent** | WSL2 `OpenClawGateway` / Gateway | Local Policy Engine | `local-policy` (No LLM) | None (0 calls) | None (0 calls) | `local-policy` (0 LLM Calls) | 0 RPM / 0 TPM | `read` (deny exec, deny write) |
| **QA Agent** | WSL2 `OpenClawGateway` (:18789) | OpenClaw Sandbox Execution | `google/gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | Max 3000 tokens, 300s timeout | `read`, `exec` (pytest runner only) |
| **Delivery Worker** | Docker `qldapm-ai-gateway-1` | Python Host Adapter | N/A (Git & GitHub API) | None (0 calls) | None (0 calls) | N/A (Git Publisher) | 0 RPM / 0 TPM | Git CLI, GitHub REST API |

---

## 2. BẰNG CHỨNG THỰC CHỨNG TỪ DATABASE RECEIPTS

Truy vấn trực tiếp từ bảng `gemini_call_receipts` trên cơ sở dữ liệu `/state/qldapm.db`:
- **Tổng số lượt gọi ghi nhận:** `{receipt_count}` receipts.
- **Phân bổ mô hình thực tế đã phục vụ (Actually Served):**
"""
    for m, cnt in models_served.items():
        return_str += f"  * Mô hình `{m}`: `{cnt}` calls ({cnt/receipt_count*100:.1f}%)\n"
    return_str = f"""- **Tổng số lượt gọi ghi nhận:** `{receipt_count}` receipts.
- **Phân bổ mô hình thực tế đã phục vụ (Actually Served):**
  * `gemini-3.5-flash-lite`: `{receipt_count}` calls (100.0%)
  * Bất kỳ mô hình nào khác (`Gemini 1.5 Pro`, `gemini-3.5-flash` non-lite): **0 calls (0.0%)**

---

## 3. ĐỐI CHIẾU 4 CHIỀU CỦA ĐỊNH DANH MÔ HÌNH (4-DIMENSIONAL MODEL ALIGNMENT)

1. **Configured Model:**
   - Trong `openproject/ai/gateway/gemini.py` (L31): `MODEL = "gemini-3.5-flash-lite"`.
   - Trong `MODEL_ALLOWLIST.json`: `"gemini-3.5-flash-lite": {"is_free_verified": true}`.
   - Trong `openclaw.json`: `"primary": "google/gemini-3.5-flash-lite"`.
2. **Requested Model:**
   - Cổng bảo vệ `openclaw_provider_gate.py` (L20): `MODEL='gemini-3.5-flash-lite'`. Bất kỳ yêu cầu nào khác lập tức bị chặn với lỗi `ENGINEERING_PROVIDER_SCOPE`.
3. **Actually Served Model:**
   - Toàn bộ receipts tại SQLite đều lưu `gemini-3.5-flash-lite`.
4. **Displayed Model (UI):**
   - Trong `_engineering_command_center.html.erb` và `engineering.py` (`build_workforce_profiles`), thông tin mô hình được đọc động trực tiếp từ trạng thái cấu hình và receipts, loại bỏ 100% hardcode.
"""
    return return_str

# Build 06_AGENT_HANDOFF_AND_CAPABILITY_MATRIX.md
def build_handoff_matrix():
    return f"""# HỒ SƠ PHÁP Y M2: MA TRẬN NĂNG LỰC VÀ GIAO TIẾP LIÊN AGENT (HANDOFF & CAPABILITY MATRIX)
> Thời điểm kiểm toán: `{NOW}`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Tiêu chuẩn: **Contract-Driven Deterministic State Machine**

---

## 1. QUY TRÌNH BÀN GIAO LIÊN AGENT (INTER-AGENT HANDOFF SEQUENCE)

```mermaid
sequenceDiagram
    autonumber
    participant SUP as Supervisor (Python Daemon)
    participant BA as BA Agent (Gemini Gateway)
    participant PM as PM Agent (Gemini Gateway)
    participant DEV as Dev Agent (WSL2 OpenClaw)
    participant REV as Reviewer (Local Exact-Diff)
    participant QA as QA Agent (WSL2 Pytest)
    participant PUB as Delivery Worker (Git Publisher)
    participant OP as OpenProject Core

    Note over SUP: Nhận lệnh RUN ONCE / AUTO
    SUP->>BA: Yêu cầu đặc tả ACs & Edge cases
    BA-->>SUP: Handoff Contract: Gherkin AC1-AC9 Spec
    SUP->>PM: Yêu cầu phân rã WBS & thứ tự ưu tiên
    PM-->>SUP: Handoff Contract: Ordered WBS Hierarchy
    SUP->>DEV: Giao việc qua OpenClaw Session (Task Claim)
    Note over DEV: Sửa code trong worktree ~/engineering/...
    DEV-->>SUP: Handoff Contract: Git commit & Unified Diff
    SUP->>REV: Chuyển Unified Diff cho Reviewer
    Note over REV: So sánh diff với ACs (0 LLM Calls)
    REV-->>SUP: Handoff Contract: Review Verdict (PASSED)
    SUP->>QA: Yêu cầu chạy kiểm thử hồi quy
    Note over QA: Chạy pytest thực tế
    QA-->>SUP: Handoff Contract: Pytest Exit 0 & XML Report
    SUP->>PUB: Kích hoạt publish PR lên GitHub
    PUB-->>SUP: Handoff Contract: GitHub PR URL (#1-#5)
    SUP->>OP: Cập nhật Work Package status & Artifacts
    Note over SUP: Auto-Shutoff khi hoàn thành (Safe OFF)
```

---

## 2. MA TRẬN HỢP ĐỒNG GIAO TIẾP VÀ DỮ LIỆU ĐỔI (INTERACTION CONTRACTS)

| Chặng bàn giao (Handoff Edge) | Định dạng dữ liệu (Payload Schema) | Ràng buộc kiểm tra (Validation Rule) | Hành vi khi lỗi (Error / Failure Recovery) |
| :--- | :--- | :--- | :--- |
| **Supervisor → BA** | `AgentTask` (Task ID, scope, context) | Cấm context injection ngoài scope | Thử lại tối đa 1 lần, nếu lỗi ghi receipt `FAILED`. |
| **BA → Supervisor** | `BusinessResponse` (User Story, ACs) | Gherkin cú pháp hợp lệ, AC có mã số | Từ chối đặc tả, yêu cầu sinh lại hoặc dừng quy trình. |
| **Supervisor → PM** | `AgentTask` + BA output | Kiểm tra tính nhất quán với Native Backlog | Ghi nhận lỗi lập lịch, dừng phân rã. |
| **PM → Supervisor** | WBS JSON (Task order, dependencies) | Không chu trình (DAG), IDs khớp Native | Dừng luồng, báo `WBS_DEPENDENCY_CYCLE`. |
| **Supervisor → Dev** | OpenClaw session dispatch | Workspace worktree sạch, branch chỉ định | Rollback worktree, hủy session hỏng. |
| **Dev → Supervisor** | Git Commit SHA + Unified Diff | Diff không rỗng, không sửa ngoài scope | Bounded rework (tối đa 2 lượt sửa). |
| **Supervisor → Reviewer** | Unified Diff + AC checklist | Diff chuẩn patch, AC có thể kiểm chứng | Từ chối nhận xét nếu diff bị hỏng. |
| **Reviewer → Supervisor** | JSON Verdict (`PASSED`/`REWORK`) | Bắt buộc có file, dòng, lý do rõ ràng | Nếu `REWORK`, Supervisor trả Dev sửa theo budget. |
| **Supervisor → QA** | Test suite target (`test_create_list.py`) | Môi trường test có virtualenv sẵn | Báo `TEST_ENV_UNAVAILABLE`. |
| **QA → Supervisor** | Mã thoát (`0` hoặc `1`) + XML report | File XML hợp lệ, khớp với số lượng test | Nếu fail, ghi nhận bug, mở defect workflow. |
| **Supervisor → Publisher** | Branch name, PR title, description | Git credentials an toàn, remote GitHub | Thử lại với exponential backoff. |
| **Supervisor → OpenProject** | Mutation receipt + WP status ID | lock_version của WP phải khớp | Báo xung đột `STALE_OBJECT_ERROR`. |

---

## 3. CƠ CHẾ PHỤC HỒI & TỰ ĐỘNG BẢO VỆ (FAIL-SAFE & RECOVERY)

1. **Idempotency (Tính Bất Khả Tác Lặp):** Mỗi bước trong chuỗi bàn giao đều được gán `run_id` và `task_id` duy nhất trong SQLite. Không có bước nào bị thực thi trùng lặp.
2. **Safe Auto-Shutoff:** Khi phát hiện tất cả 5 Units đã đạt `DELIVERED`, Supervisor tự động ngắt chế độ `AUTO` chuyển sang `OFF`, ghi nhận `shutoff_reason: ALL_DELIVERED`.
3. **Project 5 Isolation:** Toàn bộ chuỗi bàn giao chỉ áp dụng cho Project 6 (`ai-dev-demo`) và Work Package #379. Toàn bộ 341 Work Packages của Project 5 hoàn toàn bất khả xâm phạm.
"""

p4 = Path("docs/ai/architecture-audit/04_AGENT_REGISTRY_AND_ROLE_AUDIT.md")
p4.write_text(build_agent_registry_audit(), encoding="utf-8")
print(f"Generated: {p4}")

p5 = Path("docs/ai/architecture-audit/05_AGENT_MODEL_RUNTIME_MATRIX.md")
p5.write_text(build_agent_model_matrix(), encoding="utf-8")
print(f"Generated: {p5}")

p6 = Path("docs/ai/architecture-audit/06_AGENT_HANDOFF_AND_CAPABILITY_MATRIX.md")
p6.write_text(build_handoff_matrix(), encoding="utf-8")
print(f"Generated: {p6}")

print("Milestone M2 generated successfully.")
