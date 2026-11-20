# BÁO CÁO KIỂM TOÁN PHÁP Y ĐỘC LẬP (INDEPENDENT FORENSIC BASELINE) — PHASE 2.7
**Thời điểm thực hiện:** 2026-10-30T17:40:00+07:00  
**Tác giả kiểm toán:** Gemini CLI (Principal Software Architect & Reliability Engineer)  
**Phạm vi:** Đối soát thực tế toàn bộ hệ thống QLDAPM MAIN, OpenProject, Gateway/Supervisor, OpenClaw, Docker containers, cơ sở dữ liệu PostgreSQL/SQLite, và Git repositories.  
**Quy tắc:** Chỉ đọc và ghi nhận dữ liệu thực tế đo lường trực tiếp; không suy đoán, không dùng mock, không che giấu khiếm khuyết.

---

## 1. ĐỐI SOÁT TRẠNG THÁI SOURCE CODE & GIT

### 1.1. Workspace QLDAPM MAIN (`D:\AI project\QLDAPM chat`)
- **Git HEAD SHA:** `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`
- **Active Branch:** `codex/local-multi-agent-upgrade`
- **Last Commit Message:** `de7fe8f chore: version local n8n report workflows`
- **Tracked Files Status (`git status -uno`):** `CLEAN` (100% không có tracked file nào bị dirty).
- **Untracked Files:** Các file cấu hình cục bộ, tài liệu chuyển giao Phase 2 và artifacts kiểm thử đã được bảo toàn nguyên vẹn theo quy ước checkpoint.

### 1.2. Demo Repository (`D:\AI project\QLDAPM-demo\mini-task-manager`)
- **Git HEAD SHA:** `def9d0a8852af42a407bd42fb0051615a2de9331`
- **Active Branch:** `codex/mini-task-manager-ready`
- **Remote URL:** `https://github.com/Luim3141/mini-task-manager.git`
- **Tracked Files Status:** `CLEAN` (chỉ có thư mục uncommitted `? dev/` chứa test artifacts cục bộ).

---

## 2. ĐỐI SOÁT DOCKER RUNTIME & SERVING REVISION

Được kiểm tra qua lệnh `docker inspect` và `docker ps --no-trunc` trực tiếp trên Docker daemon:

| Tên Container | Container ID (rút gọn) | Config Image Tag | Image Digest (Thực tế phục vụ) | Trạng thái / Health | Cổng (Ports) |
|---|---|---|---|---|---|
| `qldapm-ai-gateway-1` | `7d3255bbee6d` | `qldapm-ai:engineering-continuation-r15-20261030` | `sha256:dc3e736fa1a37dea2644364ea96cf09db6d93549a8c7e6fe38e2eea3a18a8267` | Up (healthy) | `127.0.0.1:18089->8090/tcp` |
| `qldapm-openproject-web-1` | `acd82fe4b221` | `qldapm-core:engineering-continuation-r15-20261030` | `sha256:d03d007298461c54c7374d78a01322abb84559850f9d7964bc8f8513d4ddff73` | Up (healthy) | `8080/tcp` (Proxy 18088) |
| `qldapm-n8n-main` | `cbcbcf0c01e3` | `docker.n8n.io/n8nio/n8n:2.43.6` | `sha256:0d694582f3c7...` | Up 13 hours | `127.0.0.1:5679->5678/tcp` |
| `qldapm-qdrant` | `6cacb6b0f1b0` | `qdrant/qdrant:latest` | `sha256:9234b6f70a...` | Up 13 hours | `127.0.0.1:6333-6334/tcp` |
| `qldapm-openproject-db-1` | `7a46baa501f1` | `postgres:17` | `sha256:2d2b8998d310...` | Up 13 hours (healthy) | `5432/tcp` |

**Phát hiện xác minh:**
Container `qldapm-ai-gateway-1` và `qldapm-openproject-web-1` thực tế đang chạy revision **`continuation-r15`** (được tạo lúc 09:41:36Z và 09:41:58Z ngày 30/10/2026).  
Trong `docs/ai/engineering/deployment.json`, giá trị đã ghi nhận `continuation-r15`. Tuy nhiên, trong `IMPLEMENTATION_STATE.json` trường `deployment_current` vẫn còn sót chuỗi `continuation-r14` và digest cũ. Đây là khiếm khuyết **DEFECT-01**.

---

## 3. ĐỐI CHIẾU MÃ NGUỒN CỤC BỘ VÀ MÃ TRONG CONTAINER (SOURCE PARITY MATRIX)

Bảng đối soát tính toán bằng hàm băm SHA256 độc lập giữa file trên ổ đĩa máy chủ và file bên trong container đang phục vụ:

| Thành phần | Đường dẫn file trên Host | SHA256 Host (Local) | SHA256 Container (`sha256sum`) | Trùng khớp (Parity) | Ghi chú |
|---|---|---|---|---|---|
| **Gateway** | `gateway/engineering.py` | `2327163ca24a...` | `2327163ca24a...` | **100% MATCH** | Core engineering admission |
| **Gateway** | `gateway/engineering_operator.py` | `b8370d639a25...` | `b8370d639a25...` | **100% MATCH** | Operator & context |
| **Gateway** | `gateway/store.py` | `6952ccf8f292...` | `6952ccf8f292...` | **100% MATCH** | Owner cross-actor authority |
| **Gateway** | `gateway/service.py` | `a3d9ac320e1d...` | `a3d9ac320e1d...` | **100% MATCH** | Service Command dispatch |
| **Gateway** | `gateway/permissions.py` | `3ce4872c84cf...` | `3ce4872c84cf...` | **100% MATCH** | Role permission table |
| **Gateway** | `gateway/catalog.py` | `2fb14a0432b6...` | `2fb14a0432b6...` | **100% MATCH** | MCP Tool argument schemas |
| **Gateway** | `gateway/engineering_units.py` | `96045c0f210c...` | `96045c0f210c...` | **100% MATCH** | Backlog unit definitions |
| **Gateway** | `gateway/engineering_lifecycle.py` | `3b3602b01682...` | `3b3602b01682...` | **100% MATCH** | Cancel/resume authorization |
| **Gateway** | `gateway/engineering_state_sync.py` | `a3c48281e4f9...` | `a3c48281e4f9...` | **100% MATCH** | 5-way state sync reconciliation |
| **Gateway** | `gateway/engineering_github_sync.py`| `03b3632a68d3...` | `03b3632a68d3...` | **100% MATCH** | Stacked branches & cache |
| **Gateway** | `gateway/engineering_auto.py` | `765201ef48ae...` | `765201ef48ae...` | **100% MATCH** | Concurrency lock & auto-off |
| **Gateway** | `gateway/engineering_reporting.py` | `7cc49c36790d...` | `7cc49c36790d...` | **100% MATCH** | Metrics & report generator |
| **Core** | `core/overlay/.../rbac.rb` | `80e707435460...` | `80e707435460...` | **100% MATCH** | Owner & PM roles |
| **Core** | `core/overlay/.../gates_api.rb` | `d6ea1792ab9a...` | `d6ea1792ab9a...` | **100% MATCH** | Gates API bridge |
| **Core** | `core/overlay/.../qldapm_ai_controller.rb` | `7bae43d49c35...` | `7bae43d49c35...` | **100% MATCH** | Reporting endpoints & RBAC |
| **Core** | `core/overlay/.../engineering.html.erb` | `df1b59f45343...` | `df1b59f45343...` | **100% MATCH** | Control Center UI |

**Kết luận Parity:** Tất cả 16 file cốt lõi trong container đang chạy hoàn toàn trùng khớp 100% với mã nguồn trên máy chủ. Không có độ lệch mã nguồn (code drift) giữa source và runtime.

---

## 4. ĐỐI SOÁT WSL2 & OPENCLAW RUNTIME

Được kiểm tra qua bash shell trong distro `OpenClawGateway`:
- **WSL Distro:** `OpenClawGateway` (State: `Running`, WSL version: 2).
- **Node runtime:** Node `v24.22.2` tại `/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node`.
- **OpenClaw binary:** `/usr/local/bin/openclaw` -> `OpenClaw 2026.10.8 (dc2523e)`.
- **Gateway Process (PID 30953):** Lắng nghe tại port `18789`. Kiểm tra `curl -s http://127.0.0.1:18789/health` trả về `{"ok":true,"status":"live"}`.
- **Provider Gate Process (PID 2899):** `/root/.qldapm-openclaw/provider_gate.py` đang chạy quản lý kết nối an toàn.
- **Mini Task Manager App Process (PID 31498):** Lắng nghe tại port `18791` (`/home/openclaw/engineering/mini-task-manager-server.py`). Kiểm tra `http://127.0.0.1:18791/` và `/tasks` đều trả về HTTP 200 OK.

---

## 5. ĐỐI SOÁT SÂU TÍNH TOÀN VẸN CỦA PROJECT 5 (`qldapm-local`)

Đối soát trực tiếp trên cơ sở dữ liệu PostgreSQL (`qldapm-openproject-db-1`) thông qua OpenProject Rails Engine:

```json
{
  "project_id": 5,
  "identifier": "qldapm-local",
  "name": "QLDAPM — Local Community",
  "wp_count": 341,
  "wp_id_min": 38,
  "wp_id_max": 378,
  "wp_ids_checksum": "df934ee9fb1b71c5593b76802027439ae183981abc90a223f8601a2a34b132bf",
  "status_breakdown": {
    "1": 340,
    "37": 1
  },
  "type_breakdown": {
    "10": 272,
    "1": 57,
    "5": 12
  },
  "min_lock_version": 0,
  "max_lock_version": 4,
  "last_wp_updated_at": "2026-10-29T10:08:56Z",
  "members": [
    {"user_id": 19, "login": "ba-pm", "roles": ["QLDAPM PM"]},
    {"user_id": 20, "login": "pm", "roles": ["QLDAPM BA"]},
    {"user_id": 21, "login": "be", "roles": ["QLDAPM BE"]},
    {"user_id": 22, "login": "fe", "roles": ["QLDAPM FE"]},
    {"user_id": 23, "login": "qa", "roles": ["QLDAPM QA"]}
  ]
}
```

**Kết luận tính toàn vẹn Project 5:**
1. Số lượng Work Packages: Chính xác **341**.
2. Dải ID: Từ 38 đến 378, Checksum tập ID: `df934ee9fb1b...` cố định không đổi.
3. Phân bổ trạng thái: 340 WP ở status 1 (NEW), 1 WP ở status 37 (Draft).
4. Phân bổ loại (Types): 272 Tasks, 57 Epics, 12 Stories.
5. **Thời điểm cập nhật cuối cùng (`last_wp_updated_at`):** `2026-10-29T10:08:56Z`. Hoàn toàn KHÔNG có bất kỳ thao tác ghi (write/mutation) nào xảy ra trong suốt các hoạt động của ngày 30/10/2026.
6. Danh sách thành viên và phân quyền (Roles): Bảo toàn 100% 5 tài khoản.

---

## 6. ĐỐI SOÁT CHUỖI GITHUB PULL REQUESTS

Truy vấn đối soát trực tiếp với repository `https://github.com/Luim3141/mini-task-manager`:
- **PR #1:** `OPEN`, base `main`, head `1aa7c395`, mergeable `MERGEABLE`.
- **PR #2:** `MERGED` vào nhánh feature branch của PR #1 (`codex/openclaw-create-list-persistence-v1`), head `29ff0ec1`. (Chưa vào `main`).
- **PR #3:** `OPEN`, base là nhánh của PR #2, head `d00f8c5f`, mergeable `MERGEABLE`.
- **PR #4:** `OPEN`, base là nhánh của PR #3, head `def9d0a8`, mergeable `MERGEABLE`.
- **GitHub Review Submissions & Statuses:** Cả 4 PRs đều chưa có review submissions chính thức trên GitHub REST API (`reviews=[]`) và chưa cấu hình GitHub Actions / check runs (`statuses=[]`, `check-runs=[]`). Việc báo cáo trước đây ghi nhận "Review: PASS" là xuất phát từ kết quả của tác nhân `Reviewer Agent` nội bộ trong OpenClaw, chứ không phải GitHub Approved PR Review. Cần thể hiện minh bạch trên giao diện.
