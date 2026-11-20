## Continuation hiện hành

PM/BA planning, feedback unit, CANCEL và RESUME đã nối backend/UI. Native task/actor vẫn revalidate. `engineering_operator` OS-only hỗ trợ status/source/admit/cancel/resume/checkpoint/signal; công cụ product tương ứng engineering_plan/engineering_run_once/engineering_cancel/engineering_resume/engineering_control.

Kiểm tra run đang hoạt động trước restart. Resume dùng cùng run và checkpoint version từ status. Unknown/pending Native writes không replay. Host delivery-steps.json + history giữ từng stage/response; role templates /opt/qldapm/agents/<unit>/<role>, application-scoped root-owned AGENTS/SOUL, agents.entries.*.contextInjection=always và skills allowlist riêng. Original defaults contextInjection=never giữ nguyên cho agent ngoài scope. Thực hiện verification qua runtime systemPromptReport, không chỉ nhìn file.

Sau verified feedback delivery, `python -m automation.engineering_demo --update-run <run-id>` promotes exact release, giữ SQLite path, rollback wrapper/service nếu startup thất bại; không chạy lại full UAT/fixture suite. Base commands/baseline bên dưới chỉ đọc theo current state; không rerun installer baseline.

> Continuation hiện hành: FEATURE_IMPLEMENTATION_IN_PROGRESS; USER_UAT_DEFERRED. Đọc PHASE2_CONTINUATION_REQUEST.md và FEATURE_COMPLETENESS.md. Các kết quả trước là baseline; không dừng ở READY_FOR_USER_UAT, không yêu cầu người dùng nghiệm thu, không computer use hoặc chạy lại full suite.

# Vận hành và phục hồi Phase 2

Workspace `D:\AI project\QLDAPM chat`. Đọc `deployment.json`, `FINAL_QUALIFICATION.json` và `IMPLEMENTATION_STATE.json` trước thao tác. Không replay publication: PR #1/#2 và Native #380/#381 đã tồn tại.

## Runtime và địa chỉ

- OpenProject: `http://127.0.0.1:18088`.
- QLDAPM Gateway: `http://127.0.0.1:18089`.
- n8n: `http://127.0.0.1:5679`, giữ nguyên16workflow active/published.
- OpenClaw: một WSL2 distro `OpenClawGateway`, loopback18789; root provider gate18890.
- Mini Task Manager: `http://127.0.0.1:18791`, user service `qldapm-mini-task-manager.service`.
- Data demo: `/home/openclaw/engineering/demo-data/tasks.sqlite`; giữ nguyên khi restart/update.

## Kiểm tra / start

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat'
wsl --list --verbose
docker ps
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/bin/dbus-launch true
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/local/bin/openclaw --version
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/local/bin/openclaw gateway health --json
Get-ScheduledTask -TaskName QLDAPMEngineeringDelivery
Start-ScheduledTask -TaskName QLDAPMEngineeringDelivery
```

Task dùng current interactive user, hidden PowerShell, logon trigger, cho phép chạy bằng pin, IgnoreNew. Wrapper chỉ boot đúng distro và poll queue; không tự admit công việc. Log private: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/engineering-delivery.log`. Đã start thật/kiểm tra idle; Windows reboot/logon trigger chưa thử.

```powershell
$env:PYTHONPATH='openproject/ai'
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('status'))"
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='PAUSED'))"
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='OFF'))"
```

PAUSE giữ job chưa claim. RUN ONCE tiếp tục cùng job chưa thực thi sau kiểm tra source mới. OFF có thể hủy job chưa claim; RUN ONCE chỉ tái kích hoạt khi chứng minh `served=0`. Job đã chạy/unknown không tự replay. In-flight PAUSE/OFF dừng tại checkpoint; nếu worker mất, lease kết thúc và mode về OFF, giữ outcome để đối soát.

## Lỗi cài Node ban đầu

Installer đã dùng Node24.19.0, CLI yêu cầu `>=24.22.1 <25 || >=26.12.1`, npm exit1. Installer tự `wsl --unregister OpenClawGateway` lúc rollback; vì vậy không còn distro cũ để sửa tại chỗ. Log gốc giữ tại `%APPDATA%/OpenClawTray/Logs/Setup/` (run `f93f29404270`).

Đã tạo lại đúng một Ubuntu24.04 WSL2 bằng `wsl --install --distribution Ubuntu-24.04 --name OpenClawGateway --location ... --no-launch --web-download`; cài private Node24.22.2 sau kiểm SHA256 chính thức, prefix `/home/openclaw/.openclaw/tools/node-v24.22.2`, npm11.19.1 và `openclaw@2026.10.8 --allow-scripts=openclaw --no-fund --no-audit`. Wrapper `/usr/local/bin/openclaw` đặt PATH vào prefix này. Windows Node25.8.2 không đổi.

Không chạy installer Windows lại để quay về Node cũ. Không unregister distro hoặc global WSL shutdown. Chỉ mount repo demo; Windows drive automount/interop bị tắt. Source thực thi dùng ext4 linked worktrees để tránh lỗi staged-file publish trên drvfs; các smoke artifacts cũ được giữ.

## Gemini / quota / receipts

Model đã chạy thật: `google/gemini-3.5-flash-lite`, không fallback. Real key root-only `/root/.qldapm-openclaw/google-key`0600; OpenClaw chỉ có local gate token. Không in key/.env/config auth. Gate OFF mặc định; shared QLDAPM quota được reserve trước allowance/deadline hữu hạn; retry tính trong allowance. Giữ13RPM/450RPD/225000TPM policy hiện hữu; bounded wait75s, không tăng quota hoặc đổi paid tier.

Nếu OpenClaw báo sign-in nhưng transport hết `remaining`, có thể là gate allowance hết; không tự rotate key. Xem dispatch/result/transport/trajectory trong `runs/<run>/attempt-N`. Unknown: OFF gate/fence own Gateway, export/reconcile trước tiếp tục. `openclaw gateway stop --force` là lệnh dừng service đã kiểm chứng. Không gọi lại thao tác Native/GitHub có outcome unknown.

Metadata IDs nay gồm session UUID + step + sequence. Script `engineering_reconcile_usage.py` đã chạy một lần để khôi phục56request thực từ transport, lưu before archive và SHA; không chạy lại tự động. Counter quota không bị sửa. Tokens là provider-reported; có usage thiếu ở lỗi503, không là chứng từ billing. Không kiểm tra Google billing console live.

## Tests / source

```powershell
$env:PYTHONPATH='openproject/ai;openproject/ai/tests'
& 'openproject/ai/.venv/Scripts/python.exe' -B -m unittest tests.test_engineering tests.test_agent_queue tests.test_ai_queue tests.test_agent_registry tests.test_openclaw_provider_gate tests.test_native_incremental_sync tests.test_execution_monitor tests.test_knowledge_sync -q
```

External acceptance ở `/opt/qldapm/acceptance/`, root-owned; chạy bằng user openclaw, không chạy application code bằng root. Demo release theo commit ở `/home/openclaw/engineering/releases/29ff0ec1e531d917ce96737d768c8e16dad895c5`. `engineering_demo.py` đã install/test; không rerun installer khi port18791 đang dùng. Restart app qua systemd user, giữ datafile.

## Rollback

Prior images/private backup ở `deployment.json`. Chặn admission, đối soát active run trước rollback. Restore image/config bằng compose cho riêng Gateway/Core web; không tự restore business DB. Các additive metadata tables có thể giữ. Không xóa Docker volumes, source untracked, VHDX hoặc demo data.

**SQLite live bind mount do Linux sở hữu. Không mở bằng Windows sqlite3.** Bước backup từng giữ Windows connection gây disk I/O; đã đóng đúng process và Linux quick_check=ok. Không xóa WAL/SHM/restore DB để sửa. Backup helper đã chuyển vào Linux và explicit closing.

Handoff: cập nhật state/journal/evidence rồi chạy `engineering_checkpoint.py`. Snapshot code không chứa credentials; sáu hồ sơ handoff hiện hành vẫn ở thư mục này.
