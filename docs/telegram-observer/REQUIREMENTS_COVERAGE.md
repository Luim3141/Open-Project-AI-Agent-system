# Tiến độ theo master prompt — 06/11/2026

Phạm vi: attachment `21f610dd-956a-4005-a58b-c6f7aa0c2471/Pasted text.txt`, với model được Owner chốt lại thành `gemini-3.5-flash-lite`, chỉ một Codex agent tiếp tục. Không dùng phần trăm ước lượng để thay chứng cứ.

**Luồng chính đã hoàn thành E2E thật:** Owner duyệt Task mới397 → BA/PM → Dev → Reviewer → QA → Native publication/knowledge → Owner nghiệm thu DONE/v11 → Observer8gatesPASS → n8n completion/message16 → Owner reply19 vào16 → Gateway đọc397 thay memory391 → Gemini trả đúng → actual Telegram answer20. Không operator retry trong lượt cuối. PR14 là artifact OPEN, không tự merge/deploy ứng dụng.

## 20 deliverables bắt buộc (§80)

| # | Deliverable | Đã có / bằng chứng |
|---|---|---|
| 1 | Telegram AI Service | `openproject/ai/telegram-ai/app/main.py`, aiogram sole poller live |
| 2 | Gemini integration | `app/engine.py`, SDK real receipts, exact model lock |
| 3 | System instructions | `app/system_instructions.py` |
| 4 | Tool registry/schema | `app/tools.py`, strict Pydantic validation |
| 5 | Gateway adapters | `app/gateway.py`, fixed endpoint, actual Native ACL |
| 6 | Auth/pairing | `app/storage.py`, numeric Owner1916909968, private pairing thật |
| 7 | Conversation persistence | SQLite bind mount, memory/reply context + restart proof |
| 8 | Agent Observer | `gateway/agent_observer.py`, existing runtime/read-back |
| 9 | Minimal telemetry | Existing execution events/receipts/checkpoints reused; Native final journal + reply provenance |
| 10 | Shared Observer API | Gateway3observer commands, same projection with Rails JSON bridge |
| 11 | Embedded Visualizer | Rails Agent Studio, real Main UI397,51events,3stages |
| 12 | Notification outbox | SQLite unique(event,chat), lease, retry, actual ACK |
| 13 | n8n integration | Published workflow `bDpuIXfCgEkVOb7B`,5actual SENT receipts |
| 14 | Docker Compose | Same qldapm-ai project, non-root/read-only/no host port/socket, unless-stopped |
| 15 | Configuration examples | `.env.example`, secret refs and private root |
| 16 | Automated tests | Bot54tests, Gateway103tests, Ruby3tests/7assertions, Node client tests; scopes below |
| 17 | Installation guide | `INSTALLATION.md` for existing baseline, no reset |
| 18 | Operations guide | `OPERATIONS.md` |
| 19 | Rollback guide | Operations + exact-source release/backup/image rollback helpers |
| 20 | Final report | `FINAL_REPORT.md`, `HANDOFF.json`, immutable image/source evidence |

20/20 có artifact triển khai/bàn giao. Điều này không đồng nghĩa mọi nhánh đã được kiểm trên live hoặc mọi chức năng của hệ thống cũ đều đã được chứng nhận.

## Test matrix (§61–67)

| Nhóm | Đã xác minh | Phân loại / phần còn giới hạn |
|---|---|---|
| §61 Auth | /start paired/unpaired, valid/invalid/expired/reused pairing, private-only, unauthorized and revoked scope | Real Owner pairing; remaining negative cases isolated Repo/aiogram dispatch, không revoke Native user trên Main để test |
| §62 Gemini | Vietnamese actual conversation, multi-turn/reply context, schema/tool validation, timeout/error,429/nonretryable errors, bounded5xx, budget before HTTP, model mismatch lock, usage audit | Actual SDK/read dialogue; quota/failure/model mismatch dùng controlled fixtures, không cố gây quota/billing thật |
| §63 Observer | Full/partial/missing history, real running/complete, stale/UNKNOWN/conflicts, checkpoint, retry/resume | Real397 snapshots; real same-run plan resume after exact lost-ACK reconciliation; negative invariants isolated |
| §64 Visualizer | Main login, Task397, matching snapshot/stages/events, artifact/detail, timestamps, mobile, project denial/reload; polling recovery | Polling là implementation được §42 cho phép; không triển khai SSE để rồi giả test SSE. Client503 injection và Node lifecycle kiểm phục hồi |
| §65 Commands | Create proposal2-step; execution/mode/resume/pause guarded; duplicate/expired/wrong-user callback; backend503 single request; stale Task/control denial | Real Gateway queue admission/resume in E2E; actual aiogram→ToolExecutor→GatewayClient tested với HTTP MockTransport/network none. Không gọi đây là live callback writes |
| §66 Notifications | Gate-dependent completion, QA/review denial, owner pending, dedup/lease/expiry/preferences/revoke, temporary failures/retry, restart persistence, reply context | Actual SENT: test8, blocked13, awaiting14, PR15, complete16; actual answer20. Provider outages/revocations tested isolated, không ngắt Main/n8n của người dùng |
| §67 Fresh E2E | All14steps,397/plan8f93/codinga3f5,63pytestPASS, actual Owner/journal1251, notification16, reply19/answer20 | Scope `/healthz` được Owner chấp nhận riêng; không replay task cũ hoặc giả business completion |

Không cộng các suite overlap/subtests thành một tổng unique. Không lấy fixture, CSS preview hoặc candidate-process read-back thay Main evidence.

## Việc làm tiếp trong đợt rà này

1. **Sửa confirmation pause:** trước đây chỉ Task fingerprint, sau đó đọc control revision mới tại click. Test chứng minh project mode/control đổi mà Task không đổi vẫn đi tới write. Đã bind preview với Native version/run/stage/agent/acceptance/checkpoint và control revision; đổi trạng thái quyết định phải preview lại. Heartbeat đơn thuần không làm reject nhầm pause. Backend vẫn CAS expected_revision.
2. **Hoàn thiện kiểm thử:** thêm real aiogram callback dispatch qua actual GatewayClient + mock HTTP,429/5xx/model-lock/budget, private/auth/revoked dispatch, exact resume/mode và stale control/heartbeat cases. Tất cả chạy cô lập, không inference hoặc business writes trên Main.
3. **Sửa warning polling:** cảnh báo kết nối cũ từng không được clear sau recovery. Node RED→GREEN và Main client503 recovery test; dữ liệu freshness cảnh báo riêng vẫn giữ đúng nguồn.
4. **Bàn giao rõ scope:** bảng này liên kết20deliverables/test groups với artifact và remaining boundaries; source/images/config/integrity được read-back sau deploy.

## Phần không tự mở rộng ngoài đặc tả hiện hành

- **Project6 generic create/update, independent request_review/request_qa:** backend chưa có API an toàn tương đương; registry không cấp một executor mới để bù. Đây là exception được §23 cho phép, không phải quyền tự bỏ approval hoặc dựng runner thứ hai. Project5 create/update proposal và Project6 engineering admission/control/resume hiện có vẫn được dùng.
- **Merge/deploy PR14, Windows reboot, public hosting, paid plan/add-ons:** không tự thực hiện. Task397 nghiệm thu artifact/tests, không là cho phép release ứng dụng.
- **RAG algorithm/performance toàn hệ thống:** giữ checkpoint cũ; prompt feature này không làm những phần frozen tự thành PASS.
- **Large load, multi-user Native credential mapping, audit retention policy:** chưa qualification/triển khai thêm; hiện single Owner, bounded history, laptop-local.
- **Lượt reply cũ và full users auth delta:** thiếu metadata baseline để kết luận toàn bộ nguyên nhân lịch sử. Giữ nguyên chứng cứ/limitation, không sửa data/counter để ép hash PASS; lượt reply397 mới và Native current permissions đã được xác minh.

Các giới hạn này được ghi riêng; không cần tạo thêm coding task hoặc gọi thêm model chỉ để tăng số test/report.
