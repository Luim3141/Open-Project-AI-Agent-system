# Telegram AI Commander

Dịch vụ Python/aiogram Long Polling, không mở inbound Telegram webhook. Cùng nguồn Observer với Agent Studio; không có Supervisor/Coding runner riêng. n8n chỉ gửi thông báo outgoing.

## Cấu hình local

File `.env` của MAIN được tích hợp tại `%LOCALAPPDATA%\QLDAPM\openproject-ai\telegram-ai\.env`. Không ghi đè credentials cũ. Dùng file mẫu `.env.example` và nhập `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY` tại máy local, không gửi secret qua chat. Compose có thể đọc secret từ `*_FILE` thay cho environment nếu được mount read-only. `QLDAPM_SERVICE_CREDENTIAL_REF` trỏ tới token Gateway riêng đã được liên kết với principal thật; Gateway kiểm lại Native ACL trên từng lệnh. Không dùng Telegram username làm quyền.

Model `gemini-3.5-flash-lite` theo chỉ đạo Owner ngày05/11/2026. Không tự fallback. Owner đã nhập key riêng cho bot và xác nhận project Free Tier chưa bật billing; key local được ưu tiên, mount key cũ chỉ là fallback khi cấu hình local trống. Credentials/provider của Coding Agents được giữ nguyên. Local call budget là giới hạn bổ sung, không chứng minh provider miễn phí. Nếu API trả modelVersion khác model đã cấu hình, brain khóa inference và yêu cầu đối soát thay vì dùng model bị route ngầm.

Thiếu cấu hình: container vẫn sống với `WAITING_CONFIGURATION`; `/health` trên port8091 nội bộ cho biết tên cấu hình thiếu, không hiện secret. File env thay đổi cần recreate service qua Compose chính (root runbook). Service không tự xóa webhook hiện có; cần quyền riêng rồi bật `TELEGRAM_ALLOW_WEBHOOK_REMOVAL=true`. Không drop pending updates.

## Ghép nối

1. Owner mở bot và gửi `/start`; bot trả numeric User ID.
2. Trên terminal local, chạy qua container của Compose chính:

```powershell
docker exec <telegram-container> python -m app.main pair --user-id <numeric-ID> --projects 5,6
```

3. Gửi `/pair <mã>` trong private chat. Mã random, chỉ có hiệu lực5phút, một lần, tối đa5lần thử, gắn numeric User ID. Không dùng group chat.
4. Thu hồi: `docker exec <telegram-container> python -m app.main revoke --user-id <numeric-ID>`.

## Sử dụng

`/start`, `/help`, `/status`, `/projects`, `/tasks`, `/active`, `/blocked`, `/notifications`, `/settings`, `/cancel`. Chọn project bằng `/settings 5` hoặc `/settings 6`. Bật/tắt thông báo bằng `/notifications on`/`off`.

Ví dụ: “Task #391 tới đâu rồi?”, “Dev đã làm gì?”, “Có Task nào bị BLOCKED không?”. Reply vào notification để giữ đúng Task/Run. Bot lấy trạng thái thật mỗi lượt, memory chỉ giữ context/history; không coi trạng thái cũ là live.

Lệnh ghi tạo nút xác nhận riêng có TTL180s, gắn user/chat/project/task/run/revision. Callback claim atomic trước khi gửi lệnh, không replay sau restart hoặc timeout. Gateway quyết định quyền và gates. `pause_task` và mode có tác động queue toàn project; UI ghi rõ. Create/update ở Project5 chỉ tạo proposal Gateway, cần bước xác nhận thứ hai cho exact hash hoặc duyệt trên UI hiện hành; generic create/update ở Project6 chưa được backend hỗ trợ. Review/QA chỉ được đọc evidence; backend chưa có API chạy riêng thì bot báo chưa hỗ trợ. Không merge/deploy/delete qua bot.

## Kiểm tra

```powershell
docker exec <telegram-container> python -m app.main health
docker exec <telegram-container> python -m app.main check
# Chỉ sau khi Owner cho phép một inference smoke:
docker exec <telegram-container> python -m app.main check --provider-probe
```

`check` chỉ kiểm tra Telegram getMe/webhook, Gateway identity và model metadata. Không xóa webhook hoặc gửi message. Probe có dùng một model request/function-call và ghi budget local. Không ghi PASS nếu chưa có bot token/key/pairing thực.

Local tests:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## Persistence và rollback

SQLite `/state/telegram.sqlite` giữ pairing, memory, processed update IDs, pending confirmations, audit, provider budget, notification context và notification outbox. Mount vào thư mục runtime riêng; không mount Docker socket. File lock bảo đảm chỉ một polling process dùng state này. Chỉ một replica/service được cấp token này; không chạy Telegram Trigger n8n với cùng bot token.

Rollback: stop riêng service Telegram, giữ nguyên volume/state/secret; restore image/file snapshot theo runbook chính. Không xóa volumes hoặc sửa Agent Runs. Khi callback có timeout hoặc outcome unknown, đối soát Gateway audit theo `request_id`, không tạo key mới để retry. Processing confirmation không tự được chạy lại sau crash.

## Tài liệu SDK đã đối chiếu

- [aiogram Long Polling](https://docs.aiogram.dev/en/latest/dispatcher/long_polling.html)
- [aiogram Dispatcher/backoff](https://docs.aiogram.dev/en/latest/dispatcher/dispatcher.html)
- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)

Giới hạn: bounded recent16messages và historical summary5kchars; kết quả thiếu evidence ghi UNKNOWN/NOT_RECORDED. Không gọi unit tests là real Telegram/Gemini/n8n E2E. At-least-once delivery có thể có duplicate hiếm khi Telegram nhận nhưng ACK bị mất.
