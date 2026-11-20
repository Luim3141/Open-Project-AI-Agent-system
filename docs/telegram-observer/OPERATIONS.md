# Vận hành Telegram Commander và Agent Studio

Workspace chính: `D:\AI project\QLDAPM chat`. Trạng thái và giới hạn nghiệm thu ghi tại `FINAL_REPORT.md`; tài liệu cũ bên ngoài thư mục này không chứng minh rollout mới.

## Sử dụng

- Bot: https://t.me/qldapm_commander_bot. Owner đã pair numeric ID `1916909968`, private chat, projects5/6. Username không cấp quyền.
- Agent Studio: http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/observer. Đăng nhập tài khoản OpenProject có role PM/AI_SYSTEM_OWNER của Project6. Chọn Task hoặc nhập ID; mở stage, run, timeline và artifacts. Polling dừng khi tab ẩn.
- Hỏi: “Task #391 hiện đang ở đâu?”, “Dev đã làm gì?”, “Có Task nào BLOCKED không?”. Trạng thái mỗi lượt được đọc từ Gateway; memory chỉ giữ lịch sử/ngữ cảnh. Reply vào notification để chọn đúng Task/Run.
- `/help`, `/status`, `/projects`, `/tasks`, `/active`, `/blocked`, `/settings 6`, `/notifications on`, `/notifications off`, `/cancel`.
- Chọn loại thông báo: `/notifications types TASK_COMPLETED,TASK_BLOCKED,AGENT_FAILED,QA_FAILED,AWAITING_APPROVAL,PR_CREATED`.
- Lệnh ghi cần callback xác nhận một lần, TTL180s, đúng current revision. Create/update Project5 còn cần duyệt exact Gateway proposal ở bước hai. Project6 dùng engineering admission có sẵn; generic create/update và independent review/QA execution chưa có API nên bot từ chối. Pause/mode có tác động queue project, không chỉ Task đang hỏi.

`Runtime COMPLETED` hoặc `READY FOR RELEASE` chưa phải Task đã nghiệm thu. `TASK_COMPLETED` chỉ phát khi runtime gates áp dụng và Native DONE journal do PM/Owner thật xác minh được. STALE/UNKNOWN và history bị giới hạn phải được đối chiếu trước quyết định.

Đối soát câu trả lời sai Task: xem audit `INCOMING_CONTEXT` để lấy incoming/reply-to message ID, notification mapping và conversation Task; so với `READ_TOOL` và `BOT_REPLY_SENT`. Không suy ra một tin có reply metadata chỉ từ việc người dùng gõ “Task này”. Parser ưu tiên notification context của reply trước memory; metadata audit không lưu raw Telegram update.

## Start và kiểm tra

Docker Desktop phải hoạt động; service nằm trong Compose project `qldapm-ai`, restart policy `unless-stopped`. Windows logon/Docker Desktop autostart là cấu hình môi trường hiện có. Không chạy replica hoặc n8n Telegram Trigger với cùng bot token.

```powershell
Set-Location 'D:\AI project\QLDAPM chat'
docker start qldapm-ai-telegram-ai-1
docker exec qldapm-ai-telegram-ai-1 python -m app.main health
docker exec qldapm-ai-telegram-ai-1 python -m app.main check
```

`health` kiểm liveness Gateway qua HTTP; không chứng minh Native/model inference đã READY. Gemini chỉ READY300s sau inference thật trong process; startup không gọi inference. `check` đọc Telegram getMe/webhook, Gateway identity và Gemini model metadata; không gửi message hoặc xóa webhook. `check --provider-probe` dùng quota/model request, chỉ chạy có chủ đích.

Sau khi sửa file env local, recreate riêng bot:

```powershell
docker compose -p qldapm-ai --env-file "$env:LOCALAPPDATA/QLDAPM/openproject-ai/.env" -f openproject/ai/compose.yml up -d --no-deps telegram-ai
```

Không chạy `down -v`, không reset queue/AgentRun, không thay các override/pins Gateway/Core bằng image cũ. Start toàn hệ thống dùng runbook/manager hiện có; Telegram được thêm vào Start chính.

## Secrets, pairing và quyền

Private root: `%LOCALAPPDATA%\QLDAPM\openproject-ai\telegram-ai`.

| File | Mục đích |
|---|---|
| `.env` | Bot token, key Gemini riêng của bot, exact model và flags; không commit |
| `secrets\gateway.token` | Dedicated bearer principal18, Native ACL kiểm lại mỗi lệnh; TTL30 ngày từ enrollment |
| `secrets\notification.key` | Header auth n8n/internal ACK, mount read-only |
| `state\telegram.sqlite` | Pairing, memory, processed updates, confirmations, audit, provider budget, outbox và reply context |
| `ui-uat.json` | Chỉ dùng UAT headless theo tài khoản Owner cung cấp; không đưa vào source/evidence |

Hiện chỉ pair Owner. Không pair người khác rồi coi đó là Native identity riêng: service bearer hiện thuộc Owner18. Muốn multi-user phải thiết kế mapping credential/principal riêng trước.

```powershell
docker exec qldapm-ai-telegram-ai-1 python -m app.main pair --user-id <numeric-ID> --projects 5,6
docker exec qldapm-ai-telegram-ai-1 python -m app.main revoke --user-id <numeric-ID>
```

Mã pair một lần, hạn5phút, tối đa5lần thử, gắn numeric ID. Gửi `/pair <mã>` ở private chat. Không gửi token/key qua Telegram hoặc Codex. Khi bearer hết hạn, enroll token riêng bằng Native enrollment hiện có dưới quyền Owner; không sửa token cũ hoặc dùng SQL giả gia hạn.

Giữ `gemini-3.5-flash-lite`; không tự đổi model khi Google route khác. Key bot riêng được Owner xác nhận Free Tier chưa bật billing, Coding Agents giữ key/config cũ. Local budget20 model requests/ngày tính cả retry; tối đa một retry HTTP5xx, không retry quota429/model khác. Metadata thành công không phải bằng chứng billing; không bật billing để vượt quota.

## Notifications và sự cố

Workflow n8n mới: http://127.0.0.1:5679/workflow/bDpuIXfCgEkVOb7B. Đây là outgoing webhook workflow, không phải poller. Webhook nhận event/lease; service kiểm lại pairing/preferences; n8n gửi Telegram và ACK actual message_id. Outbox có unique(event_id,chat_id), lease, backoff, tối đa6attempts rồi FAILED; SENT chỉ có sau actual ACK.

- Bot thiếu cấu hình: `WAITING_CONFIGURATION`; sửa đúng file local rồi recreate service.
- Webhook Telegram cũ: `BLOCKED_EXISTING_WEBHOOK`; không tự xóa. Chỉ chuyển bằng flag removal khi Owner đã cho phép.
- Gateway maintenance/offline: hiển thị chưa xác minh; không tự replay lệnh ghi. Đọc lại sau recovery. Callback outcome unknown phải đối soát request key trước thao tác tiếp.
- n8n/Internet offline: execution của Task độc lập notification; outbox giữ sự kiện và retry. Không đánh dấu SENT thủ công. Kiểm tra workflow published và credential riêng; không thay credentials của workflow cũ.
- Telegram nhận nhưng ACK mất: at-least-once có thể gửi trùng hiếm gặp; không tuyên bố exactly-once.
- Laptop tắt/ngủ: bot dừng theo máy. State còn trên bind mount; không có hosted service chạy thay laptop.
- Completion chưa có: đọc `acceptance.missing_gates`, Native final journal, source conflicts và current revision; không chuyển Task DONE để ép notification.

## Backup và rollback

Backup SQLite bằng SQLite backup API hoặc dừng riêng service trước khi sao chép toàn state. Giữ secrets trong ACL private hiện có. Không commit raw databases, `.env`, UAT password, mã pair hoặc encrypted n8n database vào Git.

Rollback chức năng mới: stop riêng Telegram; giữ state/outbox để đối soát các message đã gửi. Gateway/Core dùng immutable images và private release backups trong `candidate-*/deployment.json`; release helper kiểm idle/OFF, fence worker, source/image parity, Compose parity và có image rollback. Khôi phục image/pins/source theo đúng snapshot đã chọn; không tự restore business databases hoặc xóa dữ liệu phát sinh sau rollout.

`reconcile_planning_relation.py` là one-shot cho lost ACK của đúng E2E run đã ghi: đọc Native relation thật, kiểm exact payload/project/source/idle, backup trước rồi CAS duy nhất receipt pending sang actual read-back. Không gửi lại POST, không sửa runtime thành success. Không tái dùng cho request khác.

Kiểm thử local: Gateway `unittest` và bot `pytest`; các kết quả đã chạy, Main screenshots, restart proof và giới hạn coverage ghi trong báo cáo. Không gọi CSS preview, unit fixtures hoặc operator retry là toàn bộ Main E2E tự động.
