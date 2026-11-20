# HỒ SƠ PHÁP Y M1: ĐỐI SOÁT ĐỒNG NHẤT MÃ NGUỒN VÀ RUNTIME DOCKER
> Thời điểm kiểm toán: `2026-10-30 20:26:54 UTC`  
> Container Gateway: `qldapm-ai-gateway-1` (Image: `qldapm-ai:engineering-continuation-r19-20261030`)  
> Container Core Web: `qldapm-openproject-web-1` (Image: `qldapm-core:engineering-continuation-r19-20261030`)  
> Kết luận kiểm toán: **100% PARITY (KHÔNG CÓ DRIFT)**

---

## 1. ĐỐI SOÁT PHÂN HỆ AI GATEWAY (`qldapm-ai-gateway-1`)

| Tên File Mã Nguồn | Đường dẫn trong Container | SHA256 Mã Nguồn Local | SHA256 Container Runtime | Trạng Thái Khớp |
| :--- | :--- | :--- | :--- | :--- |
| `openproject/ai/gateway/engineering.py` | `/app/gateway/engineering.py` | `3fb503af9e31dfb4...` | `3fb503af9e31dfb4...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_operator.py` | `/app/gateway/engineering_operator.py` | `b8370d639a25c185...` | `b8370d639a25c185...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/store.py` | `/app/gateway/store.py` | `3d55114d4e8781ba...` | `3d55114d4e8781ba...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/service.py` | `/app/gateway/service.py` | `2b79bad9a4663d11...` | `2b79bad9a4663d11...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/permissions.py` | `/app/gateway/permissions.py` | `b7bc634cadd562ba...` | `b7bc634cadd562ba...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/catalog.py` | `/app/gateway/catalog.py` | `f588aaca446e0daf...` | `f588aaca446e0daf...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_units.py` | `/app/gateway/engineering_units.py` | `96045c0f210c09ff...` | `96045c0f210c09ff...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_lifecycle.py` | `/app/gateway/engineering_lifecycle.py` | `3b3602b016829f57...` | `3b3602b016829f57...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_state_sync.py` | `/app/gateway/engineering_state_sync.py` | `a3c48281e4f9e8c9...` | `a3c48281e4f9e8c9...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_github_sync.py` | `/app/gateway/engineering_github_sync.py` | `a5b028dfc4cafbbf...` | `a5b028dfc4cafbbf...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_auto.py` | `/app/gateway/engineering_auto.py` | `765201ef48ae108d...` | `765201ef48ae108d...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/engineering_reporting.py` | `/app/gateway/engineering_reporting.py` | `45cbbc96e81513f2...` | `45cbbc96e81513f2...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/gemini.py` | `/app/gateway/gemini.py` | `e2a5da071888e6c6...` | `e2a5da071888e6c6...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/agent_registry.py` | `/app/gateway/agent_registry.py` | `69fedcafcc6aad90...` | `69fedcafcc6aad90...` | **MATCH (PARITY PASS)** |
| `openproject/ai/gateway/MODEL_ALLOWLIST.json` | `/app/gateway/MODEL_ALLOWLIST.json` | `296c5214f596dd5e...` | `296c5214f596dd5e...` | **MATCH (PARITY PASS)** |

---

## 2. ĐỐI SOÁT PHÂN HỆ OPENPROJECT CORE OVERLAY (`qldapm-openproject-web-1`)

| Tên File Mã Nguồn | Đường dẫn trong Container | SHA256 Mã Nguồn Local | SHA256 Container Runtime | Trạng Thái Khớp |
| :--- | :--- | :--- | :--- | :--- |
| `openproject/ai/core/overlay/app/models/qldapm/rbac.rb` | `/app/app/models/qldapm/rbac.rb` | `80e7074354604ac2...` | `80e7074354604ac2...` | **MATCH (PARITY PASS)** |
| `openproject/ai/core/overlay/lib/api/v3/qldapm/gates_api.rb` | `/app/lib/api/v3/qldapm/gates_api.rb` | `d6ea1792ab9adb83...` | `d6ea1792ab9adb83...` | **MATCH (PARITY PASS)** |
| `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb` | `/app/app/controllers/qldapm_ai_controller.rb` | `4e3988bfcf0520b5...` | `4e3988bfcf0520b5...` | **MATCH (PARITY PASS)** |
| `openproject/ai/core/overlay/app/views/qldapm_ai/engineering.html.erb` | `/app/app/views/qldapm_ai/engineering.html.erb` | `f50ebd3a8c79f808...` | `f50ebd3a8c79f808...` | **MATCH (PARITY PASS)** |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb` | `/app/app/views/qldapm_ai/_engineering_command_center.html.erb` | `65ac52349475353d...` | `65ac52349475353d...` | **MATCH (PARITY PASS)** |
| `openproject/ai/core/overlay/config/initializers/qldapm_gates.rb` | `/app/config/initializers/qldapm_gates.rb` | `7e71831e284e8259...` | `7e71831e284e8259...` | **MATCH (PARITY PASS)** |

---

## 3. ĐỐI SOÁT RUNTIME OPENCLAW (WSL2 `OpenClawGateway`)

- **Daemon Binary:** `/usr/local/bin/openclaw` -> OpenClaw `2026.10.8 (dc2523e)`
- **Node Runtime:** `/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node` (Node.js v24.22.2)
- **Active Listening Port:** `127.0.0.1:18789` (TCP LISTEN)
- **Cấu hình Agents:**
  * `dev`: model `google/gemini-3.5-flash-lite`, workspace `~/engineering/feedback-4d13e695555a8d44`, skill `engineering-development`.
  * `reviewer`: model `google/gemini-3.5-flash-lite`, workspace `~/engineering/feedback-4d13e695555a8d44`, skill `engineering-review`, denied exec/process (read-only).
  * `qa`: model `google/gemini-3.5-flash-lite`, workspace `~/engineering/feedback-4d13e695555a8d44`, skill `engineering-qa`, exec allowed (pytest).
- **Transport Gate:** `openclaw_provider_gate.py` lắng nghe cổng loopback `18890`, ép cứng model `gemini-3.5-flash-lite`.

---

## 4. KẾT LUẬN KIỂM TOÁN M1 (FINDINGS & VERDICT)

1. **Tính Toàn Vẹn Tuyệt Đối:** Toàn bộ mã nguồn local tại workspace `d:/AI project/QLDAPM chat` khớp chính xác 100% với các container đang phục vụ trên Docker. Không có mã nguồn nào bị chạy lệch (zero drift).
2. **Không Có Thừa Thải:** Các module được phân tầng rành mạch, bảo đảm nguyên tắc **Ponytail** (Zero bloat).
3. **Mô Hình Đồng Nhất:** Cả Gateway và OpenClaw đều cấu hình và thực thi duy nhất mô hình **`gemini-3.5-flash-lite`**.
