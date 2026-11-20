# HỒ SƠ PHÁP Y M6: MA TRẬN HỢP ĐỒNG TÍCH HỢP HỆ THỐNG (INTEGRATION CONTRACT MATRIX)
> Thời điểm kiểm toán: `2026-10-30 20:31:42 UTC`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Yêu cầu: Định nghĩa tường minh giao thức, schema, auth, timeout cho từng ranh giới

---

## 1. BẢNG CHI TIẾT HỢP ĐỒNG GIAO TIẾP TỪNG RANH GIỚI

| Ranh giới (Edge) | Giao thức (Protocol) | Định dạng tải (Payload Format) | Cơ chế xác thực (Auth Mechanism) | Thời hạn chờ (Timeout) | Tính bất khả tác lặp (Idempotency) |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **1. User ↔ OpenProject** | HTTP/1.1 or HTTP/2 | HTML, JSON, Turbo Streams | Session Cookie + CSRF Nonce | 30s | CSRF token & form submission deduplication |
| **2. OpenProject ↔ Gateway** | HTTP/1.1 REST | JSON (`format.json`) | `X-QLDAPM-Gate-Token` Secret | 15s | `task_id` & `run_id` mapping |
| **3. Gateway ↔ Supervisor** | Python In-Memory | Python Objects (`AgentTask`) | Internal Memory Lock | 90s | `ENGINEERING_LOCK` single-flight |
| **4. Supervisor ↔ PM/BA** | Python Async Call | Pydantic Models (`extra="forbid"`) | Memory Scope | 45s | Unique `trace_id` per turn |
| **5. Gateway ↔ Gemini API** | HTTPS / HTTP/2 | JSON (`generateContent`) | Google API Key (`x-goog-api-key`) | 30s | Quota Limiter + SHA256 Request Digest |
| **6. Supervisor ↔ OpenClaw** | HTTP / WebSocket | JSON RPC (`session dispatch`) | Local Bearer Auth Token | 300s | Session UUID persistent in SQLite |
| **7. OpenClaw ↔ Worktree** | POSIX System Calls | File streams, Unified Diffs | OS Filesystem UID 1000 | 90s | Git Worktree Branch Isolation |
| **8. OpenClaw ↔ Provider Gate** | HTTP Loopback (:18890)| JSON (`v1beta/models/...`) | Local client token (HMAC verified) | 45s | Token reservation + receipt logging |
| **9. Gateway ↔ GitHub** | HTTPS REST / SSH | Git Packfile, GitHub PR JSON | GitHub Personal Access Token | 60s | PR head branch reference |
| **10. Gateway ↔ Qdrant / n8n** | HTTP/1.1 REST | JSON Vectors / Webhook Events | Basic Auth / Webhook Secret | 10s | Document chunk hash / Event ID |

---

## 2. TIÊU CHUẨN BẢO MẬT GIAO THỨC

- **Không chuyển giao Secret thô:** OpenClaw tuyệt đối không được cấp Google API Key hay GitHub Token; mọi thao tác với bên ngoài đều được Gateway hoặc Provider Gate kiểm soát và đại diện thực thi.
- **Strict Data Validation:** Tất cả dữ liệu đầu vào và đầu ra đều được kiểm tra chặt chẽ bởi Pydantic models với cấu hình `extra="forbid"`.
