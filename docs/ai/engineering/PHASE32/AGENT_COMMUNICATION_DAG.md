# SƠ ĐỒ ĐIỀU PHỐI ĐA TÁC NHÂN & ĐỒ THỊ TRUYỀN THÔNG (AGENT COMMUNICATION DAG) — PHASE 3.2
## KIẾN TRÚC ĐIỀU PHỐI AUTONOMOUS AI ENGINEERING, STATE MACHINE & EVIDENCE RECEIPT LINEAGE

**Hệ thống:** QLDAPM Autonomous AI Engineering Engine  
**Runtime:** Hybrid QLDAPM Gateway (Python FastAPI) + OpenClaw (WSL2 Ubuntu 24.04 LTS) + OpenProject Core (Ruby on Rails 7.1)  
**Mô hình suy luận:** Google Gemini 3.5 Flash Lite (`gemini-3.5-flash-lite`, Free Tier, \$0.00)  

---

### 1. SƠ ĐỒ TOÀN CẢNH LUỒNG ĐIỀU PHỐI ĐA TÁC NHÂN (DAG WORKFLOW)

```mermaid
flowchart TD
    User["Chủ dự án (Human Owner / Admin)"] -->|1. Yêu cầu tính năng tự nhiên| IntakeModal["AI Work Intake Console (#qcc-intake-modal)"]
    IntakeModal -->|2. engineering_plan| Gateway["QLDAPM AI Gateway (Service.py)"]
    
    subgraph PlanningPhase ["Giai đoạn Lập Kế hoạch & Đặc tả (PM & BA)"]
        Gateway -->|3. Phân tích yêu cầu & AC| BAAgent["BA Agent (Gemini Flash Lite)"]
        BAAgent -->|4. Sinh Specification & ACs| PMAgent["PM Agent (Gemini Flash Lite)"]
        PMAgent -->|5. Tạo Work Packages con (#385+)| OpenProject["OpenProject Core Database (Project 6)"]
        PMAgent -->|6. Xuất bản Atomic Plan| PlanStore["SQLite engineering_plans"]
    end

    subgraph ExecutionPhase ["Giai đoạn Thực thi Kỹ thuật Độc lập (OpenClaw Host Adapter)"]
        PlanStore -->|7. Claim Unit| Supervisor["Supervisor Coordinator"]
        Supervisor -->|8. Chuyển giao Worktree| DevAgent["Developer Agent (OpenClaw Python)"]
        DevAgent -->|9. Viết code & Test local| ReviewerAgent["Reviewer Agent (OpenClaw Auditor)"]
        ReviewerAgent -->|10. Duyệt Diff & Security| QAAgent["QA Agent (Pytest Runner)"]
        QAAgent -->|11. Chạy 21 Tests Chấp nhận| GateKeeper["Gate Verification & Receipt Signer"]
    end

    subgraph DeliveryPhase ["Giai đoạn Xuất bản & Minh bạch (Delivery & Ingestion)"]
        GateKeeper -->|12. Tạo Stacked PR| GitHub["GitHub Repo (Luim3141/mini-task-manager)"]
        GateKeeper -->|13. Cập nhật trạng thái WP| OpenProject
        GateKeeper -->|14. Vector Ingestion (BGE-M3)| Qdrant["Qdrant Vector DB (Second Brain)"]
        GateKeeper -->|15. Sinh Báo cáo Tiến độ| ReportEngine["Engineering Reporting Engine"]
    end

    ReportEngine -->|16. Báo cáo & Trực quan hóa| CommandCenter["AI Command Center (Live UI)"]
    CommandCenter -->|17. Giám sát & Tra cứu DAG| User
```

---

### 2. PHÂN TÁCH TRÁCH NHIỆM VÀ RUNTIME MATRIX (RESPONSIBILITY MATRIX)

| Tác nhân (Agent) | Vai trò & Trách nhiệm chính | Runtime Môi trường | Mô hình AI / Công cụ | Quyền hạn Ghi (Write Authority) |
|---|---|---|---|---|
| **Supervisor** | Điều phối vòng đời, giám sát budget tokens, kiểm tra timeout và checkpoint. | QLDAPM Gateway | Python deterministic state machine | Không ghi mã nguồn; chỉ quản lý state queue. |
| **BA Agent** | Tiếp nhận user stories, phân tích ca sử dụng, sinh Acceptance Criteria (AC). | QLDAPM Gateway | `gemini-3.5-flash-lite` (Free Tier) | Không ghi; chỉ sinh đặc tả JSON. |
| **PM Agent** | Lập kế hoạch nguyên tử (Atomic Plan), phân rã nhiệm vụ và tạo Work Packages con. | QLDAPM Gateway | `gemini-3.5-flash-lite` (Free Tier) | Ghi Work Packages trong Project 6 (Actor 20). |
| **Dev Agent** | Viết code FastAPI, cấu hình SQLite models, triển khai API endpoints. | OpenClaw WSL2 | OpenClaw agent runtime + Python tools | Ghi mã nguồn trong branch Git cục bộ. |
| **Reviewer Agent** | Kiểm tra static analysis, diffs, SQL injection prevention, PSR standards. | OpenClaw WSL2 | OpenClaw reviewer persona + diff tools | Không ghi code; ký duyệt review receipt. |
| **QA Agent** | Thực thi bộ kiểm thử `pytest`, thu thập log kiểm thử và đo lường tỷ lệ đạt chuẩn. | OpenClaw WSL2 | Pytest test runner | Ghi kết quả kiểm thử và capture bằng chứng. |
| **Delivery Gate** | Tạo GitHub Stacked PR, chuyển trạng thái OpenProject, nạp tri thức RAG. | Host Worker | GitHub CLI + Qldapm Native Bridge | Đẩy commit/PR lên GitHub và cập nhật WP. |

---

### 3. VÒNG ĐỜI TRẠNG THÁI VÀ CHECKPOINT RECOVERY (FINITE STATE MACHINE)

Mỗi Engineering Unit trải qua 8 trạng thái hữu hạn được kiểm soát bằng cryptographic hash và lock version:

```
[ADMITTED] ──> [CLAIMED] ──> [SCAFFOLDING] ──> [DEVELOPING] ──> [REVIEWING] ──> [TESTING] ──> [VERIFIED] ──> [DELIVERED]
     │              │               │                 │               │              │             │              │
     ▼              ▼               ▼                 ▼               ▼              ▼             ▼              ▼
[PAUSED]        [PAUSED]        [PAUSED]          [PAUSED]        [PAUSED]       [PAUSED]      [PAUSED]       [ARCHIVED]
```

1. **ADMITTED:** Yêu cầu đã được Gateway tiếp nhận, gán Run ID và đưa vào `ai_queue`.
2. **CLAIMED:** Worker OpenClaw claim tác vụ, thiết lập deadline 1800s và context task.
3. **SCAFFOLDING:** Khởi tạo Git worktree độc lập, checkout stacked branch từ base PR hợp lệ gần nhất.
4. **DEVELOPING:** Dev Agent hoàn thành mã nguồn, chạy self-checks cục bộ.
5. **REVIEWING:** Reviewer Agent đối soát toàn bộ diffs và phát hiện lỗi tĩnh hoặc bảo mật.
6. **TESTING:** QA Agent thực thi 100% các bài test trong file chấp nhận (`test_*.py`).
7. **VERIFIED:** Bộ tiêu chí chấp nhận (AC) đạt tỷ lệ 100% PASS, ký số bằng chứng QA.
8. **DELIVERED:** Git commit, push branch, tạo Pull Request trên GitHub, cập nhật Work Package và lập chỉ mục Vector vào Qdrant.

---

### 4. TELEMETRY VÀ BẢO CHỨNG PHÁP Y (AUDIT TRAIL)

Mọi thao tác trong suốt đồ thị truyền thông đều được ký số và lưu vết tại:
- **`requests` table (SQLite):** Lưu toàn bộ Idempotency keys, payloads, và Native responses.
- **`execution_events` table (SQLite):** Lưu trình tự chuỗi sự kiện thời gian thực (sequence, agent_id, event_type, timestamp).
- **`provider_receipts` table (SQLite):** Lưu vết tokens tiêu thụ, thời gian phản hồi HTTP, model ID của Google Gemini.
- **`qldapm-openproject-db-1` (Postgres):** Ghi nhận lịch sử hoạt động và transitions của từng Work Package.
