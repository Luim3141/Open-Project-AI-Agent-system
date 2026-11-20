# HỒ SƠ PHÁP Y M2: MA TRẬN MÔ HÌNH VÀ RUNTIME THỰC CHỨNG (MODEL & RUNTIME MATRIX)
> Thời điểm kiểm toán: `2026-10-30 20:27:57 UTC`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Bằng chứng thực tế: SQLite receipts bảng `gemini_call_receipts` (0 receipts recorded)

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
- **Tổng số lượt gọi ghi nhận:** `0` receipts.
- **Phân bổ mô hình thực tế đã phục vụ (Actually Served):**
