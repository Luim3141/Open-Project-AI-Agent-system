> **HỒ SƠ LỊCH SỬ — không dùng làm serving readiness hiện hành.** Đọc [kết quả tiếp quản28/10](CODEX_TAKEOVER_20261028_RESULT.md), [operator guide](CODEX_FULL_PROJECT_OPERATOR_GUIDE.md) và [UAT checklist đã sửa](OPERATOR_UAT_SPECIFICATION_AND_CHECKLIST.md). Hiện READY_FOR_OPERATOR_UAT có giới hạn, chưa human sign-off. Counts/IDs/DR commands và go-live claims bên dưới là lịch sử; không thực thi lại fixture/restore/restart từ tài liệu này trên MAIN.

# SỔ TAY VẬN HÀNH HỆ THỐNG QLDAPM MAIN (OPERATOR RUNBOOK)
## Hướng Dẫn Vận Hành Môi Trường Local Production (Go-Live Standard)

**Phiên bản:** 1.2.0 (Hardened Production Standard)  
**Môi trường:** QLDAPM MAIN (Project ID 5: `qldapm-local`)  
**Ngôn ngữ:** Tiếng Việt (Giữ nguyên thuật ngữ kỹ thuật và tên lệnh)  
**Chính sách an toàn:** Zero False-PASS · An Toàn Thông Tin Tuyệt Đối · Safe Preflight Isolation First  

---

## 1. TỔNG QUAN KIẾN TRÚC VÀ DANH MỤC DỊCH VỤ

Hệ thống QLDAPM MAIN vận hành trên nền tảng Docker kết hợp các tiến trình local self-hosted, bao gồm 5 subsystem cốt lõi:

| Dịch Vụ | Container / Process | Cổng (Port) | Chức Năng Chính | Đường Dẫn Dữ Liệu / State |
|---|---|:---:|---|---|
| **OpenProject Web & DB** | `qldapm-openproject-web-1`<br>`qldapm-openproject-db-1` | `18088` (Web qua Proxy)<br>`5432` (PostgreSQL nội bộ) | Giao diện Web OpenProject & Cơ sở dữ liệu quan hệ chính thức | PostgreSQL Container Volume |
| **AI Gateway** | `qldapm-ai-gateway-1` | `18089` (`:8090` nội bộ) | Cầu nối AI, RBAC, Control Center API | `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway` |
| **n8n Automation** | `qldapm-n8n-main` | `5679` | Động cơ điều phối 16 workflows tự động | Docker Volume: `qldapm-n8n-main-data` |
| **Qdrant Vector DB** | `qldapm-qdrant` | `6333` | Lưu trữ vector nhúng Second Brain (Dense) | Bind mount: `C:\Users\LUIM\AppData\Local\QLDAPM\qdrant_storage` |
| **Ollama Local LLM** | `ollama.exe serve` (Host) | `11434` | Mô hình nhúng đa ngữ `bge-m3:latest` (1024D) | `%USERPROFILE%\.ollama` |

> [!IMPORTANT]
> **Ranh giới cô lập:** Tuyệt đối không can thiệp vào các cổng Staging (`18091`, `18092`, `15678`). Mọi thao tác vận hành chỉ tác động trên các cổng MAIN được liệt kê ở trên.

---

## 2. QUY TRÌNH KHỞI ĐỘNG, DỪNG VÀ KIỂM TRA SỨC KHỎE

### 2.1. Khởi động toàn bộ hệ thống
Khi khởi động máy chủ hoặc bảo trì xong, thực hiện theo thứ tự:
1. **Khởi động Ollama (Embedding Daemon):**
   ```powershell
   # Chạy nền nếu chưa hoạt động
   Start-Process -NoNewWindow "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" "serve"
   ```
2. **Khởi động Docker Containers:**
   ```powershell
   # Đảm bảo các container chính thức đang chạy
   docker start qldapm-qdrant qldapm-n8n-main qldapm-ai-gateway-1 qldapm-openproject-db-1 qldapm-openproject-web-1 qldapm-openproject-proxy-1
   ```

### 2.2. Kiểm tra sức khỏe nhanh (Health Check 60 Giây)
Chạy script kiểm tra tự động đã tích hợp trong WF16 bằng cách đọc secret từ tệp an toàn (không hardcode secret):
```powershell
python -c "
import urllib.request, json, os

secret_path = r'C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\webhook_secret.json'
with open(secret_path, 'r', encoding='utf-8') as f:
    token = json.load(f)['token']

req = urllib.request.Request('http://127.0.0.1:5679/webhook/qldapm-monitoring', 
    data=b'{}', 
    headers={'Content-Type':'application/json', 'X-QLDAPM-Webhook-Token': token})
with urllib.request.urlopen(req) as resp:
    d = json.loads(resp.read().decode('utf-8'))
    print('Trạng thái hệ thống:', d.get('result', {}).get('state'))
    print('Chi tiết probes:', json.dumps(d.get('result', {}).get('checks'), indent=2))
"
```
*Kết quả kỳ vọng: `state: "OK"`, tất cả các thành phần `openproject`, `qdrant`, `ollama` đều đạt `OK`.*

---

## 3. QUY TRÌNH SAO LƯU DỰ PHÒNG & PHỤC HỒI AN TOÀN (SAFE BACKUP & DISASTER RECOVERY)

### 3.1. Sao lưu định kỳ toàn diện không gây gián đoạn (Zero-Downtime Backup)
Hệ thống hỗ trợ sao lưu toàn diện cả 5 kho lưu trữ dữ liệu mà không cần dừng hệ thống:
- **PostgreSQL:** Dùng `pg_dump -Fc` (nén custom format).
- **SQLite (Gateway & Knowledge):** Dùng cơ chế transactionally consistent snapshot `VACUUM INTO`.
- **n8n SQLite & Config:** Dùng `VACUUM INTO` trong container kết hợp sao lưu tệp khóa giải mã `/home/node/.n8n/config`.
- **Qdrant Vector DB:** Lưu trữ nén Volume Cold Archive của thư mục collection `qldapm_knowledge_dense`.

Chạy kịch bản sao lưu và diễn tập tự động toàn diện:
```powershell
python "D:\AI project\QLDAPM chat\openproject\ai\automation\gemini_backup_recovery_drill.py"
```
*Tệp tin sao lưu được lưu tại:*  
`C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill`

---

### 3.2. Quy trình phục hồi khi xảy ra sự cố (Disaster Recovery)

> [!CAUTION]
> **NGUYÊN TẮC AN TOÀN DỮ LIỆU TỐI THƯỢNG:**  
> **TUYỆT ĐỐI KHÔNG chạy lệnh `pg_restore --clean` hoặc giải nén đè trực tiếp lên cơ sở dữ liệu production MAIN khi chưa kiểm định phục hồi trong môi trường cô lập.**  
> Việc phục hồi đè trực tiếp có thể xóa sạch các dữ liệu mới phát sinh hoặc làm mất đồng bộ giữa OpenProject, Gateway và Second Brain.

#### A. Phục hồi OpenProject PostgreSQL DB (Quy trình An toàn 2 Bước)

##### Bước 1: Kiểm định phục hồi trong cơ sở dữ liệu cô lập (Mặc định)
Chạy công cụ kiểm định an toàn để tạo cơ sở dữ liệu tạm thời `op_restore_isolated_test`, xác thực schema, số lượng Work Packages (376 WPs / 339 Project 5 WPs), kiểm tra mẫu và đối chiếu dữ liệu phát sinh (data drift) so với database hiện hành:
```powershell
python "D:\AI project\QLDAPM chat\openproject\ai\automation\safe_postgres_restore.py" "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\openproject_backup_<TIMESTAMP>.dump"
```
*Kết quả kỳ vọng:*  
- Hiển thị đầy đủ số lượng WPs phục hồi: 376 (Project 5: 339).
- Đối chiếu data drift: Thông báo `[OK] Zero data drift detected` (hoặc cảnh báo số bản ghi mới nếu live database có dữ liệu phát sinh sau backup).
- Tự động xóa database tạm `op_restore_isolated_test`. Database production `openproject` được giữ an toàn 100%.

##### Bước 2: Phục hồi đè vào Production MAIN (Chỉ thực hiện thủ công ngoài luồng khi thảm họa thực sự)
> [!CAUTION]
> Để bảo đảm an toàn dữ liệu tuyệt đối, công cụ `safe_postgres_restore.py` **không cho phép tự động ghi đè cơ sở dữ liệu production qua câu lệnh hay cờ tự động**. Không tồn tại chuỗi token tĩnh nào có thể thay thế quyền phê duyệt của Operator.
> Khi cơ sở dữ liệu production thực sự gặp thảm họa không thể tự phục hồi và Quản trị viên quyết định rollback, quy trình phục hồi thủ công có kiểm soát thực hiện như sau:

1. **Tạo snapshot cứu sinh khẩn cấp (Emergency Pre-Recovery Snapshot):**
   ```powershell
   docker exec qldapm-openproject-db-1 pg_dump -U postgres -d openproject -Fc -f /tmp/emergency_pre_recovery.dump
   docker cp qldapm-openproject-db-1:/tmp/emergency_pre_recovery.dump "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\emergency_pre_recovery.dump"
   docker exec qldapm-openproject-db-1 rm -f /tmp/emergency_pre_recovery.dump
   ```
2. **Sao chép tệp backup đã được kiểm định vào container:**
   ```powershell
   docker cp "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\openproject_backup_<TIMESTAMP>.dump" qldapm-openproject-db-1:/tmp/recovery_target.dump
   ```
3. **Thực hiện phục hồi đè có kiểm soát (Manual Controlled pg_restore):**
   ```powershell
   docker exec qldapm-openproject-db-1 pg_restore -U postgres -d openproject --clean --if-exists --no-owner /tmp/recovery_target.dump
   docker exec qldapm-openproject-db-1 rm -f /tmp/recovery_target.dump
   ```
4. **Kiểm tra đọc lại số lượng WPs ngay sau phục hồi:**
   ```powershell
   docker exec qldapm-openproject-db-1 psql -U postgres -d openproject -t -c "SELECT count(*) FROM work_packages WHERE project_id = 5;"
   # Kỳ vọng: 339
   ```

---

#### B. Phục hồi Qdrant Vector Database

> [!NOTE]
> **Đặc thù kỹ thuật:** Trên môi trường Docker Desktop Windows với VirtioFS bind mount, lệnh gọi REST API `PUT /snapshots/recover` bị từ chối bởi lỗi Linux syscall `syncfs()`. Vì vậy, quy trình Disaster Recovery chính thức và đã được kiểm định cho Qdrant là **Cold Volume Restore**:

##### Bước 1: Kiểm định bản sao lưu Qdrant trên Instance cô lập
Trước khi thay thế dữ liệu, chạy công cụ kiểm định để khởi chạy một container Qdrant tạm thời trên cổng `6335` nhằm giải nén bản sao lưu, kiểm tra trạng thái green, số lượng 1,745 points, và kiểm tra tìm kiếm mẫu:
```powershell
python "D:\AI project\QLDAPM chat\openproject\ai\test_qdrant_isolated_restore.py"
```
*Kết quả kỳ vọng:* `DRILL VERDICT: QUALIFIED_ISOLATED_RESTORE_PASS`.

##### Bước 2: Thay thế dữ liệu Cold Volume có Rollback Backup
1. Dừng container Qdrant:
   ```powershell
   docker stop qldapm-qdrant
   ```
2. Đổi tên thư mục collection hiện tại để dự phòng rollback:
   ```powershell
   Rename-Item "C:\Users\LUIM\AppData\Local\QLDAPM\qdrant_storage\collections\qldapm_knowledge_dense" "qldapm_knowledge_dense.bak"
   ```
3. Giải nén bản sao lưu vào thư mục `collections`:
   ```powershell
   tar -xzf "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\qdrant_collection_backup_<TIMESTAMP>.tar.gz" -C "C:\Users\LUIM\AppData\Local\QLDAPM\qdrant_storage\collections"
   ```
4. Khởi động lại container Qdrant:
   ```powershell
   docker start qldapm-qdrant
   ```
5. Kiểm tra sức khỏe collection qua API:
   ```powershell
   curl -s http://127.0.0.1:6333/collections/qldapm_knowledge_dense
   # Kỳ vọng: status "green", points_count: 1745
   ```
6. Khi xác nhận hoạt động bình thường, xóa thư mục dự phòng `.bak`.

---

#### C. Phục hồi AI Gateway & Knowledge SQLite
1. Dừng container Gateway:
   ```powershell
   docker stop qldapm-ai-gateway-1
   ```
2. Sao lưu tệp hiện tại sang đuôi `.corrupt`:
   ```powershell
   Copy-Item "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\gateway.sqlite" "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\gateway.sqlite.bak" -Force
   Copy-Item "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\knowledge.sqlite" "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\knowledge.sqlite.bak" -Force
   ```
3. Chép snapshot sao lưu thay thế:
   ```powershell
   Copy-Item "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\gateway_backup_<TIMESTAMP>.sqlite" "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\gateway.sqlite" -Force
   Copy-Item "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\knowledge_backup_<TIMESTAMP>.sqlite" "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\knowledge.sqlite" -Force
   ```
4. Khởi động lại container và kiểm tra tính toàn vẹn:
   ```powershell
   docker start qldapm-ai-gateway-1
   docker exec qldapm-ai-gateway-1 python -c "import sqlite3; db = sqlite3.connect('/state/gateway.sqlite'); print('Integrity Gateway:', db.execute('PRAGMA integrity_check').fetchone()[0])"
   docker exec qldapm-ai-gateway-1 python -c "import sqlite3; db = sqlite3.connect('/state/knowledge.sqlite'); print('Integrity Knowledge:', db.execute('PRAGMA integrity_check').fetchone()[0])"
   ```

---

#### D. Phục hồi n8n Automation Engine & Khóa Mã Hóa
1. Dừng container n8n:
   ```powershell
   docker stop qldapm-n8n-main
   ```
2. Chép database và khóa mã hóa vào volume của container:
   ```powershell
   docker cp "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\n8n_backup_<TIMESTAMP>.sqlite" qldapm-n8n-main:/home/node/.n8n/database.sqlite
   docker cp "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill\n8n_config_backup_<TIMESTAMP>.json" qldapm-n8n-main:/home/node/.n8n/config
   ```
3. Đặt quyền sở hữu cho user `node` bên trong container:
   ```powershell
   docker start qldapm-n8n-main
   docker exec -u 0 qldapm-n8n-main chown -R node:node /home/node/.n8n
   docker restart qldapm-n8n-main
   ```

---

## 4. QUẢN LÝ VÀ XOAY VÒNG TOKEN (TOKEN LIFECYCLE MANAGEMENT)

### 4.1. Kiểm tra thời hạn Token PM hiện tại
Token PM được quản lý dưới dạng mã băm SHA-256 trong Gateway database và nạp vào Bearer Auth credential của n8n. Chạy lệnh kiểm tra thời hạn an toàn:
```powershell
python -c "
import hashlib, time, json, subprocess

secret_file = r'C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\test_pm_token.secret'
with open(secret_file, 'r', encoding='utf-8') as f:
    token = f.read().strip()
h = hashlib.sha256(token.encode('utf-8')).hexdigest()

py_code = f'''
import sqlite3, time
conn = sqlite3.connect(\"/state/gateway.sqlite\")
c = conn.cursor()
c.execute(\"SELECT user_id, role, expires, revoked FROM tokens WHERE hash = '{h}'\")
row = c.fetchone()
if row:
    rem = round((row[2] - time.time()) / 86400, 2)
    print(f\"Token PM (Role: {{row[1]}}, User ID: {{row[0]}}): Còn {{rem}} ngày. Revoked: {{bool(row[3])}}\")
'''
subprocess.run(['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', py_code])
"
```

### 4.2. Xoay vòng Token PM Tự Động (Production-Safe Token Rotation)
Tuyệt đối không dùng câu lệnh SQL chèn trực tiếp trên host để tránh xung đột khóa file SQLite (NTFS Lock Contention) và tránh làm sai lệch credentials của n8n.

Sử dụng kịch bản xoay vòng đồng bộ tự động đã được kiểm định:
```powershell
python "D:\AI project\QLDAPM chat\openproject\ai\automation\rotate_pm_token.py"
```
**Quy trình tự động hóa được thực thi an toàn trong kịch bản:**
1. Sinh token mới ngẫu nhiên mật mã chuẩn `OFSO_<hex>` (Thời hạn: 30 ngày).
2. Chèn SHA-256 của token mới vào Gateway SQLite bên trong container (loại trừ lock contention).
3. Tái mã hóa credential `DBWkxwb2izrbu17C` (`QLDAPM Bearer Auth (PM)`) của n8n bằng OpenSSL AES-256-CBC với encryption key của n8n.
4. Cập nhật token mới vào `test_pm_token.secret` với phân quyền NTFS hạn chế.
5. Kiểm định kết nối HTTP 200 tới Control Center API với token mới.
6. Đánh dấu thu hồi token cũ (`revoked = 1`).
7. Xác thực token cũ bị từ chối với **HTTP 401 Unauthorized**.

### 4.3. Kiểm toán Phân quyền Windows NTFS ACL (Security Hardening)
Các tệp bí mật (`test_pm_token.secret`, `webhook_secret.json`) bắt buộc phải tuân thủ nguyên tắc đặc quyền tối thiểu (Least Privilege). Chỉ cho phép `SYSTEM` và tài khoản quản trị `LUIM` truy cập:
```powershell
Get-Acl "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\test_pm_token.secret" | Format-List
Get-Acl "C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\webhook_secret.json" | Format-List
```
*Yêu cầu bắt buộc: Không chứa các quyền truy cập rộng như `Everyone`, `Users`, hoặc `Authenticated Users`.*

---

## 5. CHÍNH SÁCH DỌN DẸP LỊCH SỬ THỰC THI N8N (EXECUTION PRUNING)

Khi chạy lâu dài, số lượng bản ghi execution trong n8n sẽ tăng lên. Để cơ sở dữ liệu SQLite của n8n không bị phình to:
- **Tình trạng hiện tại:** ~273 executions chiếm ~9.0 MB (Rất an toàn, ngưỡng cảnh báo là > 50 MB).
- **Cấu hình tự động dọn dẹp chính thức (Official Auto-Pruning via Environment):**
  Trong n8n phiên bản hiện hành, tính năng dọn dẹp lịch sử thực thi được kích hoạt thông qua các biến môi trường cấu hình trong container:
  ```yaml
  environment:
    - EXECUTIONS_DATA_PRUNE=true
    - EXECUTIONS_DATA_MAX_AGE=336          # Tự động xóa execution cũ hơn 14 ngày (336 giờ)
    - EXECUTIONS_DATA_PRUNE_MAX_COUNT=1000 # Giữ tối đa 1,000 executions gần nhất
    - EXECUTIONS_DATA_SAVE_ON_ERROR=all
    - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
  ```
> [!CAUTION]
> **Lưu ý kỹ thuật:**  
> 1. n8n CLI phiên bản hiện hành không có lệnh `execute:prune` (lệnh này đã bị loại bỏ ở các phiên bản n8n hiện đại để chuyển sang cơ chế auto-prune của daemon).  
> 2. Tuyệt đối **KHÔNG** sử dụng câu lệnh SQL thô `DELETE FROM execution_entity` để dọn dẹp dữ liệu, vì n8n có các bảng liên kết và cơ chế locking nội bộ. Việc xóa bằng SQL thô có thể gây phân mảnh hoặc khóa database n8n.

---

## 6. ĐỒNG BỘ SECOND BRAIN & ĐỐI CHIẾU DỮ LIỆU (RECONCILIATION)

### 6.1. Cơ chế đối chiếu & ranh giới dữ liệu đã được chứng minh (Proven Inventory)
Qua kiểm toán cơ sở dữ liệu thực tế:
- **Tổng số Work Packages vật lý trong database:** **376 WPs**
  - Project ID 1: 14 WPs (IDs 1..14)
  - Project ID 2: 23 WPs (IDs 15..37)
  - Project ID 5 (`qldapm-local`): **339 WPs** (IDs 38..376)
- **Tổng số tài liệu trong Second Brain (`knowledge.sqlite`):** **376 tài liệu**
  - **Phân loại theo `doc_type`:**
    - `WORK_PACKAGE`: 340 tài liệu (gồm 327 Work Packages tiêu chuẩn + 13 Actor snapshots).
    - `ARCHITECTURE`: 25 tài liệu (gồm 12 Epics chức năng #38..#48, #372 + 13 tệp tài liệu kiến trúc).
    - `SPRINT_REPORT`: 7 tài liệu (7 Sprints từ S1 đến S7).
    - `ADR`: 4 tài liệu (4 Architectural Decision Records).
    - *Tổng cộng: $340 + 25 + 7 + 4 = 376$ tài liệu.*
  - **Phân loại theo `source_id`:**
    - `op:wp:*`: 339 tài liệu (toàn bộ 339 WPs của Project 5, IDs 38..376).
    - `actor:*`: 13 tài liệu (các snapshot theo vai trò cho các WPs của Project 5).
    - `file:*`: 17 tài liệu (4 ADRs + 13 tài liệu kiến trúc).
    - `op:sprint:*`: 7 tài liệu (7 Sprints).
    - *Tổng cộng: $339 + 13 + 17 + 7 = 376$ tài liệu.*
  - **Chứng minh ranh giới:** Hoàn toàn **KHÔNG có bất kỳ Work Package nào từ Project 1 hoặc 2** lọt vào Second Brain. Ranh giới dữ liệu được bảo vệ an toàn 100%.

### 6.2. Đối chiếu toàn vẹn dữ liệu định kỳ (Reconciliation Probe)
Kích hoạt WF15 để đối chiếu tính toàn vẹn giữa dữ liệu Native OpenProject, SQLite FTS5 và Qdrant:
```powershell
python -c "
import urllib.request, json

secret_path = r'C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\webhook_secret.json'
with open(secret_path, 'r', encoding='utf-8') as f:
    token = json.load(f)['token']

req = urllib.request.Request('http://127.0.0.1:5679/webhook/qldapm-reconciliation', 
    data=b'{}', 
    headers={'Content-Type':'application/json', 'X-QLDAPM-Webhook-Token': token})
with urllib.request.urlopen(req) as resp:
    d = json.loads(resp.read().decode('utf-8'))
    res = d.get('result', {})
    print('Trạng thái đối chiếu:', res.get('status'))
    print('Số gói tin visible:', res.get('native_visible_packages'))
    print('Số tài liệu (Documents):', res.get('documents'))
    print('Số điểm Vector trong Qdrant:', res.get('points_in_project'))
    print('Điểm dữ liệu lịch sử bảo toàn:', len(res.get('unmatched_points', [])))
"
```
*Kết quả kỳ vọng: 339 visible packages, 376 documents, 1,745 vector points (gồm 1,742 chunks và 3 legacy points bảo toàn).*

---

## 7. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

| Hiện tượng | Nguyên nhân có thể | Cách khắc phục |
|---|---|---|
| **Lỗi HTTP 403 `FILE_SOURCE_NOT_ALLOWED` khi gọi WF01** | Tệp tin truyền vào không nằm trong allowlist của `config.json` | Chỉ sử dụng các tệp tin được allowlist (`main-workflow-contract`) hoặc nạp trực tiếp Native Work Package theo cú pháp `{"id": <ID>, "request_id": "<UUID>"}`. |
| **Lỗi HTTP 409 `OUTCOME_UNKNOWN_RECONCILE_FIRST` tại WF06** | Proposal đã kết thúc hoặc đang ở trạng thái cần đối chiếu, kích hoạt cơ chế fail-closed chống replay | Đây là tính năng bảo vệ an toàn dữ liệu, không phải lỗi! Không gọi lại proposal cũ. Tạo proposal mới thông qua luồng BA/Supervisor trước khi gửi phê duyệt. |
| **Lỗi HTTP 422 `CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE` tại WF11** | Gọi API gate kiểu mock cũ thay vì dùng Native QA Evidence | Chuyển sang gọi đúng nghiệp vụ Native QA Evidence: `{"operation": "list"}` hoặc `{"operation": "get", "evidence_id": "fc0479a8-b30a-5e88-9e4a-10748cb30415"}`. |
| **Ollama không phản hồi (Connection Refused cổng 11434)** | Tiến trình daemon Ollama bị dừng | Chạy lại lệnh: `& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve`. |
| **Lỗi khóa SQLite `unable to open database file` khi mở DB** | Khóa xung đột giữa tiến trình host và container VirtioFS mount | Luôn thực hiện các tác vụ ghi vào SQLite thông qua container (`docker exec qldapm-ai-gateway-1 python ...`) hoặc dùng `VACUUM INTO`. |

---
*Tài liệu hướng dẫn vận hành chính thức dành cho Quản trị viên hệ thống (Operator) QLDAPM MAIN.*
