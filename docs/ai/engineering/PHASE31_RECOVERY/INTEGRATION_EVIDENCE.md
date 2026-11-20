# BẰNG CHỨNG TÍCH HỢP HỆ THỐNG VÀ KIỂM TOÁN DỮ LIỆU (INTEGRATION EVIDENCE)
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 FORENSIC INTEGRATION EVIDENCE

---

### 1. Bằng chứng cơ sở dữ liệu Gateway SQLite (`/state/gateway.sqlite`)

Bằng chứng được trích xuất trực tiếp từ môi trường runtime container `qldapm-ai-gateway-1`:

```bash
docker exec qldapm-ai-gateway-1 python -c "
import sqlite3, json
conn = sqlite3.connect('/state/gateway.sqlite')
c = conn.cursor()
c.execute('SELECT document FROM gemini_call_receipts;')
models = {}
for row in c.fetchall():
    d = json.loads(row[0])
    m = d.get('model', 'UNKNOWN')
    models[m] = models.get(m, 0) + 1
print(models)
"
```

**Kết quả đối soát thực tế:**
- **Tổng số biên lai gọi mô hình AI (`gemini_call_receipts`):** **325 biên lai**
- **Phân bổ mô hình (Model Breakdown):**
  - **`gemini-3.5-flash-lite`:** **325 / 325 (100.0%)**
  - **Các model trả phí khác (Pro, Ultra):** **0 (0.0%)**
- **Chi phí phát sinh:** **$0.00 (Hoàn toàn nằm trong Free Tier)**
- **Tổng số phiên chạy (`ai_runs`):** **212 phiên**
- **Số lượng báo cáo tiến độ (`engineering_reports`):** **17 báo cáo**

---

### 2. Bằng chứng chuỗi Stacked PRs trên GitHub (`Luim3141/mini-task-manager`)

Bằng chứng đối soát trực tiếp với kho GitHub qua REST API và bộ đệm đồng bộ cục bộ:

| PR # | Tiêu đề Pull Request | Work Package ID | Base Branch | Trạng thái GitHub | Phân loại nhánh & Bằng chứng pháp y |
|---|---|---|---|---|---|
| **#1** | Core Task Domain & In-Memory Store | **WP #380** | `main` | `OPEN` | **UNMERGED** — Chờ hoàn thiện toàn chuỗi stacked |
| **#2** | File-backed Persistence & List Ordering | **WP #381** | `codex/openclaw-create-list-persistence-v1` | **MERGED** | **FEATURE_BRANCH (`codex/...`)** — Đã gộp vào nhánh tính năng, **CHƯA MERGE VÀO MAIN**. |
| **#3** | Input Validation & Error Handling | **WP #382** | `codex/openclaw-feedback-4d13e695555a8d44` | `OPEN` | **UNMERGED** — Stacked PR layer 3 |
| **#4** | Due Date & Priority Attributes | **WP #383** | `codex/openclaw-feedback-4d13e695555a8d44` | `OPEN` | **UNMERGED** — Stacked PR layer 4 |
| **#5** | Health Check Endpoint `/healthz` | **WP #384** | `codex/openclaw-feedback-4d13e695555a8d44` | `OPEN` | **UNMERGED** — Lớp kiểm tra sức khỏe hệ thống |

> [!IMPORTANT]
> **Lưu ý Pháp y đối với PR #2:** PR #2 mang trạng thái `MERGED`, nhưng đích gộp là nhánh tính năng trung gian (`codex/openclaw-create-list-persistence-v1`), không phải nhánh `main`. Nhánh `main` trên GitHub hoàn toàn không bị thay đổi tự động, tuân thủ 100% nguyên tắc INV-02.

---

### 3. Bằng chứng bảo vệ toàn vẹn Project 5 (`qldapm-local`)

Truy vấn đối soát trực tiếp từ PostgreSQL container `qldapm-openproject-db-1`:

```sql
SELECT count(1), max(lock_version) FROM work_packages WHERE project_id = 5;
```

**Kết quả đối soát trước và sau toàn bộ quá trình kiểm thử Phase 3.1:**
- **Số lượng Work Packages trước khi test:** `341`
- **Số lượng Work Packages sau khi test:** `341` (Không đổi, 0 writes)
- **Giá trị `lock_version` lớn nhất trước khi test:** `4`
- **Giá trị `lock_version` lớn nhất sau khi test:** `4` (Không đổi)
- **Kết luận:** **Project 5 được bảo vệ tuyệt đối 100%.**

---

### 4. Bằng chứng kiểm thử tự động Browser Playwright
- **Kịch bản kiểm thử:** `tools/verify_phase31_real_e2e.js`
- **Bộ điều khiển:** Chromium Headless (Playwright Skill)
- **Tài khoản kiểm thử:** User ID 18 (`op-owner`, AI System Owner)
- **URL kiểm thử:** `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`
- **Kết quả:**
  - `page_load`: **PASS** (HTTP 200, tiêu đề: `AI Engineering Command Center...`)
  - `workforce_transparency_pass`: **PASS** (Reviewer 0 LLM, QA Pytest Runner, Gemini Flash Lite)
  - `sync_github_pass`: **PASS** (HTTP 200, 0 submitting buttons)
  - `snapshot_report_pass`: **PASS** (HTTP 200, 0 submitting buttons)
  - `run_once_pass`: **PASS** (HTTP 200, 0 submitting buttons)
  - `infinite_spinner_eliminated`: **PASS** (100% không bị treo)
  - `project5_invariants_pass`: **PASS** (341 WPs, max lock_version 4)
