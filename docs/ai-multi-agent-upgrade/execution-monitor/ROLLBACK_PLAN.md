# PHƯƠNG ÁN DỰ PHÒNG & KHÔI PHỤC (ROLLBACK PLAN) — ĐÃ CẬP NHẬT & XÁC MINH
## EXECUTION MONITOR UI/UX REFINEMENT

- **Mục tiêu:** Khôi phục hệ thống Staging về trạng thái baseline ngày 19/10/2026 của Codex (`sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20`) trong trường hợp phát sinh sự cố sau triển khai.
- **Thời gian phục hồi ước tính:** 45 – 90 giây (thời gian khởi động Puma OpenProject và vượt qua health check `/health_checks/default`).
- **Phạm vi an toàn dữ liệu:**
  - Database PostgreSQL (`stage-db`) và SQLite Gateway (`/state/gateway.sqlite`) hoàn toàn không bị ảnh hưởng do nâng cấp chỉ gồm 4 Rails view partials UI, không có database migration và không thay đổi schema/API contracts.
  - Toàn bộ dữ liệu AI runs, Gemini receipts, proposal records và Second Brain đều được bảo toàn nguyên vẹn.
  - Bản backup trước triển khai được tạo và kiểm tra tính toàn vẹn độc lập trước khi thực hiện bất kỳ thay đổi nào.

---

### 1. Thông số Kỹ thuật Baseline để Rollback

- **Baseline Core Image:** `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20`
- **Baseline Gateway Image (Giữ nguyên):** `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`
- **Database Image (Giữ nguyên):** `sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3`
- **Candidate Image (Cần thay thế khi rollback):** `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b`

---

### 2. Lineage Guard Analysis & Đã khắc phục

ChatGPT đã phát hiện chính xác:
Trong phiên bản cũ của `provision_local_stage.py`, hàm `daily_report_core` kiểm tra:
`candidate['RootFS']['Layers'][:len(layers)] != layers`
với `layers` là các layer của image đang chạy.
- Khi triển khai candidate (28 layers) từ baseline (27 layers): 28 >= 27 nên pass.
- Khi rollback từ candidate (28 layers) về baseline (27 layers): `len(layers)` là 28, nhưng candidate chỉ có 27 layers nên lệnh slice trả về 27 layers != 28 layers, gây lỗi `DAILY_REPORT_CORE_BASE_OR_SCOPE_MISMATCH`.

**Biện pháp khắc phục đã được kiểm chứng bằng thực nghiệm (Unit Test PASS 100%):**
Hàm `daily_report_core` đã được cập nhật để chấp nhận cả quan hệ mở rộng tiến trình (forward) và quan hệ tổ tiên (ancestor rollback):
```python
cand_layers = candidate['RootFS']['Layers']
forward_match = (len(cand_layers) >= len(layers) and cand_layers[:len(layers)] == layers)
rollback_match = (len(cand_layers) <= len(layers) and layers[:len(cand_layers)] == cand_layers)
```
Đồng thời, chế độ `--core-only` đã được bổ sung vào `provision_local_stage.py`, đảm bảo lệnh rollback chỉ tác động tới đúng dịch vụ `staging-web`, không recreate hay làm gián đoạn `staging-gateway`, `quick-tunnel`, `local-backup`, `n8n`, hay database `db`.

---

### 3. Điều kiện kích hoạt Rollback

1. Container `qldapm-ai-stage-staging-web-1` không đạt trạng thái `healthy` sau 120 giây kể từ khi apply.
2. Route `/projects/qldapm-local/qldapm-ai/executions` trả về HTTP status 500 hoặc 503.
3. JavaScript runtime crash ngăn cản việc tải Execution Detail hoặc đồ thị Multi-Agent.
4. Lỗi hiển thị nghiêm trọng phá vỡ trải nghiệm người dùng trên các viewport chuẩn.
5. Yêu cầu hủy bỏ trực tiếp từ Chủ dự án QLDAPM.

---

### 4. Quy trình Thực thi Rollback (2 Phương án Độc lập)

#### Phương án 1: Dùng script chuẩn của dự án với cờ `--core-only` (Khuyến nghị)

Phương án này giữ nguyên lease locking, snapshot backup tự động, và cập nhật đồng bộ các lock file runtime:

```powershell
Set-Location 'D:\AI project\QLDAPM chat'
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\provision_local_stage.py' --core-only --core-image 'sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20'
```

*Cơ chế vận hành:*
- Chiếm lock an toàn `operator_lease('staging')`.
- Snapshot `gateway.sqlite` và secrets sang thư mục backup runtime.
- Kiểm tra tính hợp lệ của baseline image `7d76c1eb...` qua `daily_report_core`.
- Khởi động lại duy nhất `staging-web` với baseline image bằng `--no-deps --no-build --pull never`.
- Cập nhật `stage-image-lock.json` và `stage-runtime.json` về baseline image.
- Không khởi động lại `staging-gateway`, `local-backup`, `quick-tunnel`, `n8n`, hay `db`.

#### Phương án 2: Khôi phục trực tiếp qua Docker Compose (Dự phòng khẩn cấp khi Python runtime gặp sự cố)

Chạy lệnh rollback khẩn cấp bằng script Python đã ghim cụ thể biến môi trường:

```powershell
Set-Location 'D:\AI project\QLDAPM chat'
& '.\openproject\ai\.venv\Scripts\python.exe' -c "
import os, subprocess, json
from pathlib import Path

runtime = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
env = {
    **os.environ,
    'AI_RUNTIME': runtime.as_posix(),
    'CORE_IMAGE': 'sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20',
    'AI_IMAGE': 'sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b',
    'POSTGRES_IMAGE': 'sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3',
    'QLDAPM_N8N_KEY_PATH': (runtime / 'n8n-stage/encryption.key').as_posix(),
    'QUICK_TUNNEL_IMAGE': 'sha256:a80f54e29918ec66c82cdc7ad8fd9a65e3082e59825c0356d5737916959884c6',
    'LOCAL_BACKUP_IMAGE': 'sha256:9713d54aad003b084e58035965156902f86c0ba7a638e41ab880d119ba9cbba8'
}
argv = [
    'docker', 'compose', '--project-name', 'qldapm-ai-stage', '--env-file', str(runtime / '.env'),
    '-f', 'openproject/ai/stage.yml', '-f', 'openproject/ai/deep-ai.stage.yml',
    '-f', 'openproject/ai/gemini-free.stage.yml', '-f', 'openproject/ai/local-runtime.stage.yml',
    '-f', 'openproject/ai/quick.stage.yml', '-f', 'openproject/ai/backup.stage.yml',
    'up', '-d', '--no-deps', '--no-build', '--pull', 'never', 'staging-web'
]
res = subprocess.run(argv, env=env, capture_output=True, text=True)
print('COMPOSE_RETURNCODE:', res.returncode)
print(res.stdout)
if res.returncode == 0:
    lock_file = runtime / 'stage-image-lock.json'
    data = json.loads(lock_file.read_text())
    data['staging-web'] = 'sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20'
    lock_file.write_text(json.dumps(data, indent=2))
    print('STAGE_IMAGE_LOCK_REVERTED_SUCCESSFULLY')
"
```

---

### 5. Kiểm tra Hậu Rollback (Post-Rollback Verification)

1. **Xác minh Container:**
   ```powershell
   docker inspect qldapm-ai-stage-staging-web-1 --format '{{.Name}} | {{.Image}} | {{.State.Health.Status}}'
   ```
   *Yêu cầu bắt buộc:* Image ID phải là `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20` và trạng thái `healthy`.

2. **Kiểm tra Quick Tunnel URL:**
   - Lấy URL từ `http://localhost:18090/`.
   - Kiểm tra mã HTTP 200 tại `/projects/qldapm-local/qldapm-ai/executions`.
   - Kiểm tra mã HTTP 200 tại `/projects/qldapm-local/qldapm-ai/executions/38fdb479-5566-4a18-b2da-6a9cf15aad3c`.

3. **Báo cáo cho Chủ dự án:**
   Lập báo cáo sự cố kèm log container và trạng thái hoàn tất khôi phục.
