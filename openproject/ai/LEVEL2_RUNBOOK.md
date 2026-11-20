# Gemini Assistant Level 2 — staging

**Hiện hành15/10/2026 — Không giới hạn số thao tác Gemini:** hard cap6 tool calls/batch/model turns/write_scope_ids đã bỏ trên staging18091/18092. Deadline120s, tài nguyên, quota và quyền native vẫn áp dụng; xem [checkpoint mới](UNLIMITED_CHECKPOINT_2026-10-15.md). Các ghi chú giới hạn6 bên dưới là lịch sử.

Hiện hành15/10: staging business context/preview dễ hiểu/checkbox và native results đã nghiệm thu. Đọc BUSINESS_CHECKPOINT_2026-10-15.md và BUSINESS_COMMANDS.md trước các lệnh/chính sách metadata-only lịch sử. Key/continuous consent/quota ledger giữ nguyên; không host-open gateway SQLite đang chạy. Native scope/actor/hash/TTL/idempotency/workflow/unknown-write guards vẫn áp dụng.

## Hiện hành15/10 — chạy liên tục theo owner consent

Đọc `CONTINUOUS_CHECKPOINT_2026-10-15.md` trước các mốc14/10 bên dưới. User đã cung cấp ảnh Free tier và cho phép Gemini sử dụng không hết hạn, chấp nhận chi phí. Staging `authorized`, `expires:null`; owner consent/ảnh được lưu private, bound đúng existing key/project/model và metadata scope. Không có yêu cầu gia hạn mỗi giờ; không giả vờ cập nhật ngày xác minh billing/quota. OFF vẫn thu hồi quyền chạy. Không tự set up billing/đổi plan/key/model/live.

117Windows regression và53Linux tests (1OS skip), actual Google smoke +metadata329/REST/MCP/replay PASS. Human browser chat/automatic GET refresh và final DB/web/gateway restart PASS; quyền authorized/expiresNone vẫn giữ. Terminal/receipt đọc checkpoint mới. Local quota caps10RPM/175000TPM/350RPD theo snapshot cũ vẫn giữ; ảnh tier không phải quota mới. Lỗi429 chờ1h; timeout/network/408/5xx chờ60s trước yêu cầu mới. Không auto replay run hoặc ghi native; lỗi auth/key/client/schema cần sửa. Service chạy theo yêu cầu, không tự inference liên tục khi idle; Docker/máy/API phải hoạt động.

Owner có thể tắt bằng quy trình hiện có: stop staging gateway rồi `free_tier_staging.py disable`, StartStage với exact image lock. Lệnh tạo consent cho lần thiết lập mới (local only, gateway đã stop, chỉ khi owner đã authorize bằng lời rõ ràng):

```powershell
./.venv/Scripts/python.exe free_tier_staging.py authorize-continuous --evidence 'C:\path\billing.png' --user-authorization 'C:\path\exact-user-authorization.md'
./.venv/Scripts/python.exe free_tier_staging.py smoke
./.venv/Scripts/python.exe free_tier_staging.py enable
./Manage-OpenProjectAI.ps1 -Action StartStage
```

Không cần chạy lại lệnh consent/smoke khi restart bình thường. Changed key/model cần enrollment/proof đúng; không gửi key vào chat. Rollback image/config/proof theo backup `operator/continuous-541b3360-5e8b-47e2-bc29-8ae27df5df3e`; giữ SQLite usage hiện tại, không restore counters cũ để hoàn lại quota. Legacy helper `verify` tạo proof1h và xóa continuous consent; không chạy nó để làm provider liên tục trừ khi muốn chủ động quay lại chế độ cũ.

Nguồn hiện hành: [Google billing](https://ai.google.dev/gemini-api/docs/billing), [quota](https://ai.google.dev/gemini-api/docs/rate-limits), [transient errors/backoff](https://ai.google.dev/gemini-api/docs/troubleshooting). Owner cost consent không sửa giới hạn Google hoặc chứng minh guaranteed24/7 uptime. Các mục14/10 bên dưới là lịch sử trước consent mới.

Đọc `LEVEL2_CHECKPOINT_2026-10-14.md` trước khi tiếp tục. Candidate đã triển khai staging và Gemini SDK đã chạy Google thật; live chưa deploy. Proof Free có hạn, không tự gia hạn.

## Khởi chạy an toàn

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat\openproject\ai'
# Chỉ start container đã được khóa đúng image; không seeder, không recreate volumes.
./Manage-OpenProjectAI.ps1 -Action StartStage
```

Mở [AI Assistant staging](http://localhost:18091/projects/qldapm-local/qldapm-ai), đăng nhập bình thường bằng tài khoản staging của bạn. AI không bỏ qua password/TOTP. Main vẫn ở `http://localhost:8088`; không coi main đã có UI mới.

## Thao tác và quyền

- `gateway/config.json` hoặc `stage-ai/config.json`: `gateway_mode` là `strict` hoặc `native`; default `strict`, giá trị khác bị từ chối. Sửa config khi gateway đã dừng, backup trước rồi restart. Không đổi mode live trong lượt này.
- Strict giữ **schema2** hiện có và atomic custom mutation receipts; không hạ về schema1. Native gọi API v3 và không yêu cầu custom capabilities. Native không hỗ trợ `get_gate`/`change_gate`; core đang có hard gate vẫn kiểm tra tại backend.
- REST/MCP/UI ghi mặc định trả proposal. Nhấn Approve/Reject với đúng actor, hash, TTL và lock version. Proposal không thể confirm sau Reject hoặc đổi gateway mode. Privileged operations vẫn qua broker/local approval riêng.
- `auto_execute=true` chỉ cho `create_work_package`, `update_work_package`, `comment`, `transition` trong Native Mode, khi caller trực tiếp yêu cầu. Chat mặc định chỉ đề xuất; checkbox `allow_routine_writes` cấp consent cho đúng một run, `write_scope_ids` tối đa6 ID hiện có. Gemini chỉ cập nhật/comment/transition ID trong phạm vi đã chọn hoặc ID vừa tạo cùng run. Model không được tự cấp consent; code/gate/admin/deploy không kế thừa quyền này.
- Mỗi thao tác ghi cần `idempotency_key` duy nhất, replay cùng key/payload trả receipt cũ. Timeout/UNKNOWN không tự gọi lại POST/PATCH; Native PATCH chưa có atomic remote receipt nên chưa tự reconcile. Kiểm tra OpenProject và audit trước quyết định tiếp theo.
- Subtask có `parent_id` cần quyền OpenProject `manage_subtasks`. Người dùng đã duyệt bổ sung duy nhất quyền này cho role12 QLDAPM PM trên staging project3; đã áp dụng và kiểm thử hierarchy thật PASS. Live/role khác không đổi. Rollback permissions ở private `stage/level2-pm-permission-before-20261014.json`.
- Update dùng `changes.subject/description/assignee_id` hoặc `assignee_role`, `due_date` (YYYY-MM-DD/null), `priority_id`. Role selector BA/PM/BE/FE/QA chỉ resolve khi có đúng một registered member và native role hiện hành còn khớp; không tự mời thành viên hoặc nâng quyền.
- Query: `list_work_packages`/`analyze` nhận `query` và `parent_id`. Overdue tính theo ngày Asia/Bangkok, loại DONE/CLOSED và percentageDone100; không dùng làm điểm đánh giá nhân sự.
- Một Gemini run tối đa6 tool calls. Nhiều đề xuất nhỏ được duyệt từng proposal; chưa có UI bulk approval hoặc batch lớn. Backlog/work breakdown được đề xuất qua create/update tools, không có dữ liệu capacity/estimate được tự bịa.

## Gemini Settings và API key

SDK chính thức `google-genai==2.30.1`; key backend hiện có được giữ ở private runtime, không nhập key vào chat hoặc UI. Model đọc từ `gemini.json` và phải khớp proof cùng model/key/project/Free/no billing/quota. Không paid fallback. API 429/503/timeout mở circuit, SDK retry và automatic function execution/continuation đều tắt (1 attempt). Cách đối soát model tại local:

```powershell
docker stop qldapm-ai-stage-staging-gateway-1
./.venv/Scripts/python.exe free_tier_staging.py configure-model --model gemini-3.5-flash-lite
# configure-model giữ key/usage và OFF; không phải xác minh Google/model/quota.
./.venv/Scripts/python.exe free_tier_staging.py verify
# Người vận hành kiểm tra đúng project tại official console rồi xác nhận exact hash.
./.venv/Scripts/python.exe free_tier_staging.py smoke
./.venv/Scripts/python.exe free_tier_staging.py enable
./Manage-OpenProjectAI.ps1 -Action StartStage
```

Không chạy các bước Google khi Free/no billing/quota chưa được kiểm tra lại. `verify` mặc định public demo; không tự mở project-metadata scope, gia hạn proof hoặc reset usage. Proof hiện tại dựa trên người dùng xác nhận lại evidence official-console trước đó, expires14/10/2026 **23:26:49+07**; không phải assistant vừa kiểm tra billing API. Real SDK smoke, metadata329 và synthetic create/update đã có receipt. Full private ticket/code/personnel không được gửi vào Unpaid Services theo [Google terms](https://ai.google.dev/gemini-api/terms). Đổi model không chứng minh nó có Free quota.

SDK Developer `count_tokens` không nhận tools/system config. Adapter đưa phần đó vào probe và reserve ít nhất toàn bộ JSON byte length cho general turn, để không đánh giá thấp input budget. Usage và circuit lưu SQLite, giữ qua restart. Không mở SQLite từ Windows đồng thời gateway Linux dùng WAL; dùng HTTP/ContainerState, chỉ dùng helper host SQLite khi gateway đã dừng.

UI Settings/status không gọi Google để probe. `verified` là local proof còn hợp lệ và circuit đóng, không phải một inference vừa thành công. Receipt Google thật mới là acceptance của provider.

## Kiểm thử

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py' -q
# Sau khi stage healthy; tạo dữ liệu giả và chỉ dọn exact ID/UUID của lượt này:
./.venv/Scripts/python.exe -m tests.stage_level2 "$env:LOCALAPPDATA\QLDAPM\openproject-ai"
docker exec qldapm-ai-stage-staging-web-1 bundle exec rails runner /qldapm-core/deep_stage_test.rb
./.venv/Scripts/python.exe -m tests.stage_transport "$env:LOCALAPPDATA\QLDAPM\openproject-ai" --main
./.venv/Scripts/python.exe -m tests.stage_restart_level2 "$env:LOCALAPPDATA\QLDAPM\openproject-ai"
```

`stage_level2` trả PARTIAL và liệt kê BLOCKED khi thiếu parent permission; không coi exit0 là tất cả yêu cầu PASS. Native UI tests dùng synthetic session/HTTP fixture, không thay thế browser/TOTP acceptance. REST 503 có `source=gateway|openproject|gemini`; upstream Google message/credential không được echo.

Final acceptance14/10:112Windows units,61Linux tests (1OS skip),28UI/bridge,10native groups, MCP HTTP+stdio và staging DB/web/gateway restart PASS. Restart giữ329native attributes/key/config/proof/usage/circuit/runs; expiry chặn Gemini đúng. Không còn test đang chạy. Xem TEST_MATRIX và checkpoint cho receipt cụ thể; browser thật/full new qualification/production chưa nghiệm thu.

## Production và rollback

Chưa deploy production. Cần qualification mới cho final pair/source, backup/restore rehearsal và preview main cụ thể, sau đó user phê duyệt production riêng. Không dùng proof cũ hoặc ghép các log PASS thành qualification envelope.

Backup Level2 nằm ngoài Git tại private `operator/level2-stage-*` và `operator/level2-final-*`: gateway stopped state, stage DB dump, old image lock/IDs và proof. Nếu rollback staging cần dùng đúng hai old immutable IDs trong `images-before.json`, restore config khi gateway dừng và khóa lại stage-image-lock; không restore database mù, không xóa volumes. Native fixtures đã được dọn chính xác và source329 đã đối soát.

Nguồn kỹ thuật: [Google Function Calling](https://ai.google.dev/gemini-api/docs/function-calling), [Google GenAI SDK](https://github.com/googleapis/python-genai), [OpenProject API Work Packages](https://www.openproject.org/docs/api/endpoints/work-packages/). Bằng chứng thực thi nằm trong checkpoint/artifacts, tài liệu API không phải chứng cứ deployment.
