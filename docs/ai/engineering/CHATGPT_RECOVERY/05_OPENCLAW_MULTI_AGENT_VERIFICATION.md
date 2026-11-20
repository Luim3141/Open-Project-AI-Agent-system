# Phase2 current — 01/11/2026

Phase2 current: full worker.execute→DeliveryJournal→real temporaryGatewayStore/admit/claim/checkpoint/resume/finish tests7PASS, coveringReviewer/QAfail→rework, knownpartial/completedreworkresume, unknownno-replay/treefence and originaldiff/receiptsretention. Additional2tests use real disposable childprocess to verifyAUTO survivespoll andPAUSE/CANCEL/failedfence terminate. ExternalNative/provider/git/GitHub/acceptanceleaves in7tests arefixtures. No freshliveOpenClaw/Geminisession, loadedliveworker version not proved until authorizedidle restart. Totalfinalaffected182PASS; prior PM/BAreceipt correction below preserved.

---

# Workforce receipts — source recovery, 01/11/2026

Phạm vi: `gateway/engineering.py::build_workforce_profiles` và regression tests riêng. Đây là kết quả kiểm tra source với Store tạm; **deployment/runtime acceptance: NOT VERIFIED** trong tác vụ này.

## Lỗi tái hiện

- Empty Store vẫn hiển thị `325 Gemini Receipts`, Reviewer clean/PASS, `21/21 Pytest PASS`, PRs #1–#5 và tên trajectory cố định.
- Model lấy từ quota config; Reviewer bị gắn `local-policy (0 LLM Calls)` dù receipt có thể ghi LLM thật.
- Receipt lookup không lọc Project6/OpenClaw; chọn theo UUID thay vì thời gian `document.at`.
- Một executing run khiến cả sáu role thành RUNNING; configured skill được hiển thị như đã loaded.

## Sửa tối thiểu

- Join `gemini_call_receipts` với `ai_queue` theo `run_id` và actor; chỉ nhận queue payload `project_id=6`, `engine=openclaw`. `receipts.project` là provider billing project, không bị nhầm với Native project ID.
- Receipt gần nhất theo numeric `document.at`, sau đó rowid nếu cùng thời gian. Model/provider/session/run/state/usage hiển thị từ receipt; không suy acceptance, review sạch hoặc PR từ provider success.
- Supervisor phản ánh coordinator `LOCAL_DETERMINISTIC`, không gán quota model. Queue record được ghi rõ là stored queue evidence.
- RUNNING lấy latest role lifecycle event của từng queue executing đúng scope (native sequence, đúng event project/actor). `AGENT_STARTED`/`REVIEW_STARTED` cho một role; `AGENT_COMPLETED`/`AGENT_FAILED`/`REVIEW_COMPLETED` kết thúc active handoff. Chỉ khi run chưa có lifecycle event mới dùng `ai_runs.result.agent`. Các role còn lại STANDBY; STANDBY không có nghĩa đã hoàn thành.
- Thiếu dữ liệu trả `NOT VERIFIED — Chưa có bằng chứng`. `skill` vẫn là catalog configuration; `skills_loaded` không tự nhận đã nạp.
- Giữ nguyên các field UI đang đọc; không đổi schema, provider policy/quota, queue hay Native data.

## Evidence đã chạy

Python sử dụng: `openproject/ai/.venv/Scripts/python.exe`. System Python có package `tests` khác nên lệnh đầu bằng system Python không import được module; đây không phải RED của bug.

- RED trước patch: `-m unittest tests.test_engineering_profiles_recovery -v`, 7 tests, **6 failures + 1 pass**, exit 1. Log: `profiles_red.log`.
- GREEN/regression: `-m unittest tests.test_engineering_profiles_recovery tests.test_engineering_continuation tests.test_engineering -v`, **37 tests PASS**, exit 0. Log: `profiles_green.log`. Existing Starlette/httpx và anyio deprecation warnings được giữ trong log; không thay dependencies trong phạm vi này.
- Tests mới dùng Store trong `TemporaryDirectory`, bao gồm kiểm tra database dump không đổi sau projection. Fixtures kiểm tra Project5/engine/actor isolation, timestamp thay UUID, actual Reviewer/QA LLM, missing fields và role status.

Snapshot nguyên file trước sửa: `backups/profiles/engineering.before.py`, SHA256 `4280e10a15a0fe0a490d8988932e5ccab6c025c7515af944765e615262f26dca`. Không dùng snapshot này để ghi đè các thay đổi song song tại `status()`; rollback nếu cần phải hẹp trong function profiles.

## Follow-up sau review: PM/BA lifecycle

Inspection xác nhận `engineering_planning.generate()` emit `AGENT_STARTED`/`AGENT_COMPLETED` cho BA và PM nhưng không ghi `result.agent`. Do đó bản sửa chỉ dựa result.agent bỏ sót RUNNING của planning. Regression mới gọi `execution_events.append()` thật trên temporary Store; không gọi generate/provider.

- RED follow-up: 10 tests, **2 failures + 8 pass**, exit 1 (`profiles_lifecycle_red.log`): BA có start event vẫn STANDBY; PM stale result.agent vẫn RUNNING sau failure event.
- Snapshot function ngay trước follow-up: `backups/profiles/build_workforce_profiles.before-lifecycle.py`, SHA256 `ef16b33a170a32b293dd5d2ab4300c37a0c544f6e799db5f4d57e12dce30b468`.
- Bổ sung tests cho BA→PM handoff, completed role, failed role override, queue finished/queued, sai project/engine/actor. Patch chỉ trong profiles; không đổi event emitter hay planning behavior.
- GREEN follow-up dùng cùng ba module phía trên: **40 tests PASS**, exit 0 (`profiles_lifecycle_green.log`). Đây là validation source; candidate r1 trước follow-up cần rebuild nếu muốn chứa thay đổi này.

## Giới hạn

Không gọi provider, không admission/replay live, không GUI, không deploy. Chưa kiểm thử runtime/image đang serving hay Human UAT. Không kết luận model, loaded skills, test acceptance hoặc review outcome của một run thật từ fixtures. Full integration qualification do tác vụ gốc tổng hợp riêng.
