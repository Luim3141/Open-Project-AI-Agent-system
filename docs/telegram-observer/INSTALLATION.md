# Cài bổ sung vào QLDAPM MAIN hiện có

Đây là cài additive cho workspace `D:\AI project\QLDAPM chat`, không phải dựng lại OpenProject/n8n. Giữ nguyên runtime `%LOCALAPPDATA%\QLDAPM`, database, volumes, provider và worker hiện có. Trạng thái instance đã cài ở `FINAL_REPORT.md`; nếu các receipt/private files đã tồn tại thì dùng read-back, không tạo lại để ép xanh.

## 1. Preflight

Đọc `openproject/ai/README.md`, `CHECKPOINT.md`, `architecture.md` và runbook hiện hành. Docker Desktop phải sẵn sàng; Native Core/Gateway/n8n Main healthy, target projects5/6 đúng identifiers. Dùng virtualenv hiện có `openproject/ai/.venv`; CLI helper import các module vận hành có sẵn của workspace. Repo mới clone chỉ các feature commits không thay thế toàn bộ baseline source local chưa tracked.

Capture baseline mới trước thay đổi; không ghi đè baseline evidence đã có:

```powershell
Set-Location 'D:\AI project\QLDAPM chat\openproject\ai'
.\.venv\Scripts\python.exe -m automation.telegram_rollout audit --baseline <new-evidence-file.json>
.\.venv\Scripts\python.exe -m automation.telegram_rollout init
```

`init` tạo private directories/defaults nếu thiếu và giữ nguyên file hiện có. Các rollout source Core/Gateway dùng exact approved file whitelist, current image base, qualified bundle, idle/OFF và worker fence; không dùng candidate cũ sau khi MAIN đã đổi. Không cần chạy lại rollout trên instance hiện tại.

## 2. Cấu hình local

Mở `%LOCALAPPDATA%\QLDAPM\openproject-ai\telegram-ai\.env`, nhập bot token và key Gemini trên máy. File mẫu là `openproject/ai/telegram-ai/.env.example`. Không gửi key/token vào chat, source, screenshot hoặc shell arguments.

Giữ `GEMINI_MODEL=gemini-3.5-flash-lite`. Chỉ bật `GEMINI_PROJECT_DATA_CONSENT=true` khi Owner chấp thuận dùng dữ liệu Task với project Free Tier chưa bật billing; không tự chuyển model/project billing để qua quota. Bot có key riêng; fallback read-only tới key cũ không thay config/provider Coding Agents.

Dedicated Gateway token được enroll bằng Native principal18/AI_SYSTEM_OWNER thật:

```powershell
.\.venv\Scripts\python.exe -m automation.telegram_rollout enroll-service
```

Lệnh xác minh Native identity trước khi lưu; refuse nếu token file đã tồn tại. Không ghi đè credentials cũ. `notification.key` riêng được init tạo, mount read-only; tokenTTL30ngày. Service bind state riêng và chỉ ở network nội bộ, không publish port8091 ra host.

## 3. Build service và workflow

```powershell
docker compose -p qldapm-ai --env-file "$env:LOCALAPPDATA/QLDAPM/openproject-ai/.env" -f compose.yml build telegram-ai
docker compose -p qldapm-ai --env-file "$env:LOCALAPPDATA/QLDAPM/openproject-ai/.env" -f compose.yml up -d --no-deps telegram-ai
.\.venv\Scripts\python.exe -m automation.telegram_n8n_install
```

Installer dùng authenticated local n8n owner hiện có, backup encrypted database vào private operator directory trước lần cài đầu, thêm đúng2credentials và1outgoing workflow rồi activate/read-back. Không update/delete workflow hay credential cũ. Partial/duplicate/config mismatch bị chặn để đối soát. Không thêm Telegram Trigger; chỉ aiogram long polling đọc updates. Không xóa webhook hoặc pending updates nếu chưa có Owner cho phép.

## 4. Pair, smoke và xác minh

```powershell
docker exec qldapm-ai-telegram-ai-1 python -m app.main check
docker exec qldapm-ai-telegram-ai-1 python -m app.main pair --user-id <numeric-ID> --projects 5,6
```

Owner gửi `/start`, rồi `/pair <mã>` trong private chat; mã dùng một lần/5phút. Kiểm tra `/status`, hỏi một Task được phép, mở Agent Studio trong OpenProject, kiểm cả business status và acceptance. `check` dùng metadata, không inference. Một inference smoke có chủ đích dùng `check --provider-probe`; không bật tự động lúc startup.

Controlled delivery test có nhãn rõ, không biến Task thành completed:

```powershell
docker exec qldapm-ai-telegram-ai-1 python -m app.main notify-test --user-id <numeric-ID> --project-id 6 --task-id <existing-visible-ID>
```

Chỉ gọi kênh thành công khi outbox SENT có actual message_id ACK. Business E2E cần Task mới được Owner duyệt, actual BA/Dev/Reviewer/QA/Native handoff và Owner final acceptance; không replay task cũ, không dùng fixture/test event làm TASK_COMPLETED. Instance hiện tại đã có proof397/message16, không lặp lại các script one-shot acceptance/reconciliation.

Startup, revoke, expiry, failure handling, backup và rollback chi tiết trong `OPERATIONS.md`. Không reset volumes, DB hoặc security controls để cài.
