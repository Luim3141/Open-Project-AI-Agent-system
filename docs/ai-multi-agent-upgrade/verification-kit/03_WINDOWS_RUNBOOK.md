# 03 — WINDOWS / POWERHELL OPERATIONS RUNBOOK

Mọi lệnh dưới đây để Gemini **tham khảo và điều chỉnh đúng repo**, không phải một tập lệnh được phép chạy mù. Dùng Terminal PowerShell tại root dự án. Kiểm tra `AGENTS.md`, `README.md`, compose files, script đã tồn tại rồi mới chạy. GHI nhật ký command, exit code, timestamp. KHÔNG in secret.

## A. Preflight read-only
```powershell
Set-Location 'D:\AI project\QLDAPM chat'
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git diff --stat
git diff --name-status
docker info --format '{{.ServerVersion}}'
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker compose ls
Get-ChildItem .\openproject\ai -Filter '*.yml' -File
Get-ChildItem .\openproject\ai -Filter '*.ps1' -File
```
Nếu Docker Engine chưa chạy, STOP Docker tests và ghi `BLOCKED_DOCKER_OFFLINE`. Không thay đổi environment để fake success.

## B. Compose inspect
Chỉ khi đã tìm **đúng** compose file thực tế, ví dụ `openproject/ai/stage.yml`, và các overlays bắt buộc:
```powershell
# Sử dụng danh sách -f đúng như runbook dự án; lệnh này chỉ minh họa:
docker compose -f .\openproject\ai\stage.yml config --services
docker inspect <container-name> --format '{{json .HostConfig.RestartPolicy}}'
docker inspect <container-name> --format '{{json .NetworkSettings.Ports}}'
docker stats --no-stream
```
**Tránh `docker compose config` không che secret**: output có thể chứa env/password. Nếu cần export config, redaction bảo vệ trước khi lưu.

## C. Basic API read-only checks (đường dẫn phải suy ra từ routes hiện tại)
```powershell
# Đọc cổng trong manifest/running containers, KHÔNG đoán port staging.
$base = 'http://localhost:18092'
try {
  $r = Invoke-WebRequest -Uri "$base/health" -Method Get -TimeoutSec 10 -UseBasicParsing
  "status=$($r.StatusCode)"
} catch { "ERROR: $($_.Exception.GetType().Name)" }
```
`/health` 200 chỉ chứng minh process lắng nghe; cần readiness riêng cho DB/Gemini/n8n. Không in body nếu có thể rò bí mật. Không tạo fake endpoint `/ready` khi source chưa có.

## D. Quick Tunnel safe checks
```powershell
# Chỉ kiểm tra metadata/ports/route tại máy cục bộ; sanitize output.
docker ps --filter 'name=tunnel'
docker ps --filter 'name=cloudflared'
# Không copy URL tunnel thật lên Git hoặc screenshot công khai.
# Lấy đúng hostname của phiên từ logs an toàn; trích xuất trong bộ nhớ (không vào artifact public).
# Remote smoke: thử bằng trình duyệt/Playwright từ mạng bên ngoài LAN và tài khoản test.
```
Test HTTPS, login, logout, redirect/cookie, route deny-list trên tunnel; không chạy stress từ public URL. Nếu url thay sau restart, báo expected behavior và cập nhật người dùng theo quy trình bảo mật.

## E. Runner kiểm thử từng lớp
```powershell
# Python suite hiện tại theo handoff (phải kiểm tra .venv có thật):
.\openproject\ai\.venv\Scripts\python.exe -m unittest discover -s .\openproject\ai\tests -v
# Runner được báo cáo (đọc mã trước khi chạy vì có thể chứa side effects):
python .\openproject\ai\run_full_regression.py
# Playwright/k6 chạy từ sandbox test harness đã xác minh, không cài global bừa bãi.
```
Nếu cwd ảnh hưởng Python imports, làm theo `openproject/ai/README.md`: thay đổi cwd hợp lệ, ghi chính xác command. Không cho test `unittest` tự chạy fixtures live.

## F. Test sequence an toàn
1. `git status` baseline → 2. backup+verify stage isolation → 3. offline unit → 4. read-only integration → 5. stage writes → 6. E2E → 7. load LAN → 8. Quick Tunnel remote smoke → 9. resiliency/stage restart → 10. final regression.

### Quản lý log
- Lưu stdout/stderr vào `verification_runs/<timestamp>/raw_logs` qua `Tee-Object`; dùng redaction trước khi lưu/chia sẻ.
- Không in value ENV hoặc docker inspect Config.Env thô.
- Không dùng `--rm` trên container nghiệp vụ thật; không dùng `docker volume prune`, `down -v`.
- Khi có lỗi Windows/WSL file permission, xác định path conversion thực tế; không khởi tạo DB trống thay thế volume cũ.
