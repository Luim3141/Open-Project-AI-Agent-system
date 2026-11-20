# HỒ SƠ PHÁP Y M6: BẢN ĐỒ GIAO TIẾP TOÀN DIỆN HỆ THỐNG (END-TO-END COMMUNICATION MAP)
> Thời điểm kiểm toán: `2026-10-30 20:31:42 UTC`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Tổng số ranh giới giao tiếp khảo sát: **10 Ranh giới (Boundaries)**

---

## 1. SƠ ĐỒ ĐỒ THỊ 10 RANH GIỚI GIAO TIẾP (10-BOUNDARY TOPOLOGY)

```mermaid
flowchart TD
    subgraph UI_Layer [Lớp Giao Diện Người Dùng]
        User([Người dùng / Web Browser])
    end

    subgraph OP_Core [Lớp OpenProject Rails Core :18088]
        OP_Views[Rails View Engine / Nonced JS]
        OP_Ctrl[qldapm_ai_controller.rb]
        OP_RBAC[qldapm/rbac.rb]
        OP_DB[(PostgreSQL DB)]
    end

    subgraph Gateway_Layer [Lớp AI Gateway :18089]
        GW_App[FastAPI Async App]
        GW_Store[(SQLite /state/qldapm.db)]
        GW_Super[Supervisor Handler]
        GW_PM_BA[PM & BA Inference]
    end

    subgraph External_Cloud [Lớp Đám Mây Bên Ngoài]
        GeminiCloud[Google Gemini API v1beta]
        GitHubRepo[GitHub: Luim3141/mini-task-manager]
    end

    subgraph WSL2_OpenClaw [Lớp Môi Trường WSL2 OpenClaw]
        OpenClaw_Daemon[OpenClaw Daemon :18789]
        Provider_Gate[openclaw_provider_gate.py :18890]
        OC_Dev[Dev Agent]
        OC_Rev[Reviewer Agent]
        OC_QA[QA Agent]
        Worktree[(Worktree mini-task-manager)]
    end

    subgraph Aux_Services [Lớp Dịch Vụ Phụ Trợ]
        Qdrant[(Qdrant Vector DB :6333)]
        N8N[n8n Workflow Engine :5679]
    end

    %% Edge Definitions (1 to 10)
    User <-->|Edge 1: HTTPS CSP-Nonced| OP_Views
    OP_Views --> OP_Ctrl
    OP_Ctrl <--> OP_RBAC
    OP_Ctrl <--> OP_DB
    
    OP_Ctrl <-->|Edge 2: HTTP Internal Bridge Secret| GW_App
    GW_App <-->|Edge 3: Python In-Memory Function Calls| GW_Super
    GW_App <--> GW_Store
    
    GW_Super <-->|Edge 4: In-Memory Task Dispatch| GW_PM_BA
    GW_PM_BA <-->|Edge 5: HTTPS REST GenAI SDK| GeminiCloud
    
    GW_Super <-->|Edge 6: Loopback HTTP / WS Token Auth| OpenClaw_Daemon
    OpenClaw_Daemon <-->|Edge 7: Sandboxed Session & File IO| Worktree
    OpenClaw_Daemon --> OC_Dev
    OpenClaw_Daemon --> OC_Rev
    OpenClaw_Daemon --> OC_QA
    
    OpenClaw_Daemon <-->|Edge 8: HTTP Loopback Scoped Admission| Provider_Gate
    Provider_Gate <-->|Edge 8b: Upstream Free Tier Only| GeminiCloud
    
    GW_App <-->|Edge 9: Git CLI & GitHub REST API| GitHubRepo
    
    GW_App <-->|Edge 10a: REST Hybrid Search| Qdrant
    GW_App <-->|Edge 10b: Webhook Triggers| N8N
```

---

## 2. ĐẶC TẢ 10 RANH GIỚI GIAO TIẾP

1. **Ranh giới 1 (User ↔ OpenProject Web):** Giao tiếp browser qua HTTP/HTTPS. Bảo vệ bởi CSRF token, Session Cookie (Rack Session Store), và Strict CSP với dynamic nonces.
2. **Ranh giới 2 (OpenProject ↔ AI Gateway):** Rails controller giao tiếp với FastAPI qua mạng nội bộ Docker `qldapm-internal`. Xác thực qua `X-QLDAPM-Gate-Token`.
3. **Ranh giới 3 (Gateway ↔ Supervisor):** Lời gọi hàm nội bộ trong tiến trình Python. Quản lý trạng thái và khoá điều khiển tất định (`ENGINEERING_LOCK`).
4. **Ranh giới 4 (Supervisor ↔ PM / BA):** Giao việc theo mô hình Pydantic (`AgentTask`, `RunScope`). PM phân tích WBS, BA chuẩn hóa tiêu chí Gherkin.
5. **Ranh giới 5 (PM/BA ↔ Google Gemini API):** Giao thức HTTPS REST v1beta. Sử dụng Google GenAI SDK với client giới hạn byte (`BoundedClient`), mô hình cố định `gemini-3.5-flash-lite`.
6. **Ranh giới 6 (Supervisor ↔ OpenClaw WSL2):** Kết nối qua cổng loopback `127.0.0.1:18789`. Xác thực bằng Bearer Token cục bộ, kiểm tra trạng thái health trước khi gửi phiên.
7. **Ranh giới 7 (OpenClaw ↔ Sandbox Worktree):** Truy xuất filesystem nội bộ trong thư mục worktree chỉ định. Dev sửa code, Reviewer đọc diff, QA chạy pytest.
8. **Ranh giới 8 (OpenClaw ↔ Provider Gate):** OpenClaw gọi proxy cổng 18890 bằng local client token. Gate kiểm tra quota, ép cứng model `gemini-3.5-flash-lite`, rồi chuyển tiếp lên Google API.
9. **Ranh giới 9 (AI Gateway ↔ GitHub):** Sử dụng Git CLI đẩy các commit nhánh và gọi GitHub REST API để quản lý Pull Requests (#1–#5).
10. **Ranh giới 10 (AI Gateway ↔ Qdrant & n8n):** Qdrant phục vụ hybrid RAG retrieval qua cổng 6333; n8n nhận webhooks điều phối báo cáo qua cổng 5679.
