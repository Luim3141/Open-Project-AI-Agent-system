# Engineering core recovery — 2026-11-01

Phạm vi: intake/admission, queue claim, actor 18/20 lifecycle, AUTO/RUN_ONCE, host worker dispatch/recovery. Chỉ đọc source và chạy CLI/unit tests trên `TemporaryDirectory`; không Computer Use, deploy, native/business writes, provider calls, paid/model/config changes, merge, push hoặc xóa dữ liệu. Không chạy qualification scripts/fixtures lịch sử. Không thao tác Project 5 hoặc WP379 live.

## Kết quả đã chứng minh và sửa

### 1. AUTO worker tự dừng ở lần poll đầu tiên

`automation/engineering_worker.py:agent_process` chỉ chấp nhận `RUN_ONCE` sau `communicate(timeout=2)`. Khi CLI thực thi lâu hơn 2 giây trong `AUTO`, host đóng provider gate, stop OpenClaw Gateway rồi terminate process và báo `ENGINEERING_PAUSED_CHECKPOINT_REQUIRED`, dù queue vẫn executing và deadline còn hạn. Đây là điều kiện host, không phải kết luận provider gặp lỗi.

Sửa 2 điều kiện dùng cùng tập `{RUN_ONCE, AUTO}`: tiếp tục polling và phân loại lỗi deadline. Giữ nguyên fence cho PAUSED/OFF/CANCEL, claim state và cả hai deadline.

### 2. Owner18 resume bỏ qua pending Native receipt của PM20

Admission ánh xạ owner18 sang run actor20. `lifecycle.resume` lại kiểm tra Native receipts bằng actor người thao tác (18). Một receipt actor20 chưa biết kết quả khiến PM20 bị chặn `ENGINEERING_NATIVE_OUTCOME_RECONCILIATION_REQUIRED`, nhưng owner18 vẫn requeue chính run đó. Owner cũng không nhận ra successful owned receipt khi source version thay đổi vì cùng lỗi namespace actor.

Sửa 2 dòng sử dụng `run.actor_id` đã được Store kiểm tra quyền: `source_matches` và truy vấn pending requests. Authorization người thao tác vẫn dùng `authorized(service, actor)`; audit vẫn ghi đúng actor người thao tác. Không đổi ownership hoặc cho phép replay unknown writes.

### 3. PAUSE có thể xen giữa mode check và atomic claim

`engineering.claim` kiểm tra mode trước khi gọi `Store.claim_run`; mode check nằm ngoài transaction claim. Regression chèn PAUSED đúng khoảng này và quan sát queue trở thành executing trong khi control vẫn PAUSED.

Sửa `Store.claim_run`: với `openclaw_only=True`, đọc lại engineering mode trong cùng `BEGIN IMMEDIATE` trước lựa chọn/claim queue row. Nếu OFF/PAUSED, trả None. Giữ API/signature, global executing slot, lease expiry và generic/supervisor scheduling. Chỉ có caller production `engineering.claim` sử dụng `openclaw_only=True`, và caller này gọi `engineering.setup` trước, nên bảng control đã tồn tại.

## Validation thực tế

Tất cả lệnh unittest bên dưới chạy trong `D:\AI project\QLDAPM chat\openproject\ai`, dùng venv hiện hữu; fixture Native/Gemini mock, SQLite temp và mock subprocess. Mock là bằng chứng cho logic host, không chứng minh live WSL/OpenClaw/provider.

Baseline trước sửa:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_engineering tests.test_engineering_auto_mode tests.test_engineering_continuation
```

```text
Ran 40 tests in 41.151s
OK (exit 0)
```

RED worker, trước sửa:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_engineering_worker_recovery
```

```text
Ran 2 tests in 0.007s
FAILED (failures=1, errors=1), exit 1
active AUTO poll: RuntimeError ENGINEERING_PAUSED_CHECKPOINT_REQUIRED
AUTO expired deadline: expected ENGINEERING_DEADLINE_EXCEEDED, got ENGINEERING_PAUSED_CHECKPOINT_REQUIRED
```

RED core, trước sửa lifecycle/Store:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_engineering_core_recovery
```

```text
Ran 3 tests in 1.194s
FAILED (failures=3, errors=1), exit 1
owner pending Native receipt: expected ValueError, none raised
owner verified source receipt: ENGINEERING_SOURCE_STALE
PAUSED race: expected None, got claimed actor20 executing contract
```

GREEN worker sau sửa và bổ sung PAUSED/OFF/CANCEL coverage:

```text
Ran 3 tests in 0.006s
OK (exit 0)
```

GREEN core/worker/generic queue sau sửa:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_engineering_core_recovery tests.test_engineering_worker_recovery tests.test_ai_queue tests.test_agent_queue
```

```text
Ran 28 tests in 15.013s
OK (exit 0)
```

Đợt 28 tests trên gồm 3 core regressions; sau đó thêm test hai thread AUTO chỉ claim đúng một global slot và chạy lại đúng command trên:

```text
Ran 29 tests in 32.144s
OK (exit 0)
```

Baseline rerun sau cả ba production fixes:

```text
Ran 40 tests in 22.689s
OK (exit 0)
```

Có Starlette/httpx và anyio deprecation warnings; không sửa dependency trong đợt này. TestClient HTTP dùng `testserver`, không gửi tới live OpenProject. Các dòng `Auto daily/weekly report generated` đến từ temporary test Store, không là live reports.

## Files, scope và rollback

Production:

- `openproject/ai/automation/engineering_worker.py`: 2 dòng sửa.
- `openproject/ai/gateway/engineering_lifecycle.py`: 2 dòng sửa.
- `openproject/ai/gateway/store.py`: 4 dòng thêm, chỉ nhánh openclaw claim.

Tests mới:

- `openproject/ai/tests/test_engineering_worker_recovery.py`.
- `openproject/ai/tests/test_engineering_core_recovery.py`.

Trước mọi production edit đã snapshot byte-for-byte 3 file ở `backups/core/*.before.py`; `backups/core/manifest.json` lưu before/after SHA256. Source production đang untracked từ trước; không dùng `git diff` rỗng để suy ra không có thay đổi. Self-review dùng unified diff against snapshots, thấy đúng 8 dòng production thay đổi/thêm nêu trên.

Rollback local: khôi phục đúng 3 file từ snapshot nếu cần, không reset repository hoặc restore DB/volumes. Không thực hiện rollback tự động. Parent agent cập nhật `architecture.md` cùng changeset; worker này không sửa file architecture chung.

## Giới hạn và runtime gaps

- Chưa deploy nên không kết luận serving container/host worker đang dùng code đã sửa. Cần runtime fingerprint và deployment do parent điều phối theo quyền hiện có.
- Chưa chạy actual WSL CLI, Gemini generation, physical host reboot/logon hoặc operator/human UAT. Không đổi policy/model/key/provider gates.
- `build_workforce_profiles` trong `engineering.py` hiện còn literal claims như `325 receipts`, `21/21 Pytest PASS`, `PRs #1-#5` và reviewer PASS. Đây là source observation; các chuỗi đó không chứng minh actual current runtime evidence. Đã báo parent, không sửa presentation/reporting ngoài scope.
- AUTO scheduler vẫn là một flow nhiều transaction (mode check, provider/backlog evaluation, admission, reset AUTO). Chưa chứng minh hoặc sửa concurrent control/admission race khác trong flow này; atomic claim fix chỉ giải quyết PAUSED xen trước queue claim.
- Không chạy toàn bộ historical/live regression suite. WP379 IN PROGRESS và Project5 được bảo toàn theo nghĩa không có live write từ phần việc này; trạng thái live cần chứng cứ read-only riêng của parent.
