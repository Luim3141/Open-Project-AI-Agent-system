# Independent review Phase2 — hiện hành

Reviewer độc lập đọc journal/outbox/routes/n8n persistence và full delivery resume. Findings đã tái hiện và sửa: header name/value + Basic redaction gap; ACK timeout không bao trùm headers/body; resume sau rework lấy stale review; partial resume ghi đè original reviewed diff. RED/GREEN và re-review lưu trong runPhase2.

Kết quả cuối: outbox8/8 và delivery7/7 được reviewer chạy độc lập; journal10/10 đã kiểm trước đó. Root chạy182 affected Linux tests và các candidate/clone checks sau các thay đổi cuối. Không còn finding Medium/High đã biết trong phạm vi review này. Đây không phải live OpenClaw/provider hoặc Owner acceptance; RAG semantic gap và các production boundaries được ghi riêng.

---

# Independent recovery source review — 2026-11-01

**Trạng thái cuối sau re-review:** findings 1–2 đã sửa và reviewer xác minh offline; không còn must-fix đã biết trong phạm vi batch này. Chi tiết phát hiện ban đầu được giữ nguyên bên dưới, kết quả xác minh ở cuối tài liệu. Đây không phải deployment hoặc Human UAT sign-off.

Review này so sánh trực tiếp 8 file trong `run-20261101T035551Z/serving-source/{gateway,core/overlay}` với source tương ứng dưới `openproject/ai/`; worker host so với `backups/core/engineering_worker.before.py`. Không dùng `git diff` làm baseline vì source phần lớn untracked. Đã đọc `RECOVERY_PLAN.md`, callers và tests liên quan.

Batch này sửa AUTO polling, atomic claim/mode gate, owner resume dùng actor của run, GitHub child mapping/cache/pagination/error reporting, bỏ PR rows giả, factual reports/provider independence/JSON escaping, RAG relevance policy và workforce receipt projection. Không thay provider/model, không Computer Use, không live API/provider calls, không merge, không ghi Project5 hoặc live state. Reviewer chỉ tạo tài liệu này; diagnostics dùng SQLite tạm và mock.

## Must fix — P2 correctness

1. **PM/BA đang chạy nhưng workforce hiển thị STANDBY.** `openproject/ai/gateway/engineering.py:69-73` chỉ lấy active role từ `ai_runs.result.agent`. Luồng planning thực tại `engineering_planning.py:117-126` ghi `AGENT_STARTED` vào `execution_events`, nhưng không ghi `result.agent`; result vẫn là `{stage: PLANNING, status: running, text: PLANNING}`. Vì vậy card PM/BA chuyển thành STANDBY trong lúc inference đang hoạt động. Đây là regression của projection mới, không phải thiếu receipt lịch sử.

   Reproduction offline: dùng `make_service()` từ `test_engineering_auto_mode`, admit unit `engineering_planning.PLANNING`, claim và `engineering.progress(..., 'PLANNING', {})`; bind run bằng `bind_run`; patch `service.knowledge` và `service.gemini.structured` trước `engineering_planning.generate`. Ngay tại mocked structured callback, output quan sát: `active model role=ba profile.status=STANDBY`, trong khi event đã lưu là `AGENT_STARTED/ba/RUNNING`. Không gọi provider. Probe exit 0 sau dừng chủ động trước provider.

   Sửa tối thiểu: dùng scoped execution events hiện có để xác định role chưa có completion/failure, hoặc cập nhật progress bằng agent tại handoff thực. Regression phải kiểm tra trong luồng planning thật với provider boundary mocked, gồm kết thúc role để không giữ RUNNING sau completion. Không suy RUNNING từ receipt cũ.

2. **Dense response lỗi parse bị coi là healthy no-match và mất lexical fallback.** `openproject/ai/gateway/knowledge_search.py:297` mới dùng `dense_state == 'READY'` để bắt complete lexical match. Nhưng `_dense_search` đặt READY trước khi duyệt/validate hits; except handler tại `knowledge_search.py:247-249` chỉ log fallback mà không trả state về FALLBACK. Khi một hit có payload lỗi, search abstain thay vì giữ partial lexical fallback đã cam kết.

   Reproduction offline: dùng `RAGRecoveryTests` fixture, ingest document mặc định, đặt `vector.hits=[{'payload': None, 'score': 0.99}]`, query `authorization requirements missingterm`, actor7/project5 fixture tạm. Kết quả thực: `0 READY` và warning fallback. Cùng query khi `embed_texts` raise `RuntimeError('synthetic outage')` trả `1 FALLBACK`. Đây là simulated project5 trong temporary SQLite, không phải live Project5.

   Sửa tối thiểu: set `self.dense_state='FALLBACK'` trong except; thêm test cho lỗi sau khi nhận dense response (không chỉ embed/search transport failure). READY chỉ dùng cho response hợp lệ đã kiểm tra.

## Follow-up / giới hạn đã biết

- GitHub comment sync **không có exactly-once/crash-safe/concurrent idempotency**: POST xảy ra trước lưu hash, không durable claim/reservation; hai requests đồng thời hoặc crash sau POST có thể tạo comment trùng. Đây là preexisting gap ở `_get_cached_hash` → `native.call` → `_set_cached_hash`, không được tính là regression mới. Batch chứng minh retry failed writes và normal cache dedup, không chứng minh đầy đủ idempotency. Không chạy live writes để thử.
- Các PR1–6 mappings vẫn có static baseline trong `PR_WP_MAP`; dynamic receipt mappings mới được validate project/repository và mỗi changed write đọc lại Project6/parent379 scope. Không có bằng chứng batch ghi parent379 hoặc Project5 qua GitHub sync. Chưa thử TOCTOU khi admin di chuyển WP giữa package read và POST.
- Report reader trống theo user **NOT REPRODUCED**. Source/test contract chứng minh narrative có đường list/get và JSON được escape; không chứng minh GUI/modal thực đã hết lỗi vì không Computer Use.
- Các hardcoded pipeline/safety claims khác trong command-center view (ví dụ count341/100% invariant) còn là preexisting UI debt ngoài patch PR/report/workforce. Không coi việc bỏ fallback PR rows là đã audit toàn bộ UI factuality.
- Không sửa n8n event publishing trong batch này. Không suy workflow graph/executions là business-side-effect acceptance.
- RAG single-token literal anchor và complete lexical match khi dense healthy/no-hit là tradeoff bảo thủ đã ghi trong báo cáo RAG; chưa có live corpus calibration/recall UAT. Không coi unit fixtures là semantic acceptance.

## Validation reviewer thực chạy

- 52 isolated tests **PASS**, exit0: `test_engineering_core_recovery`, `test_engineering_worker_recovery`, `test_engineering_github_recovery`, `test_engineering_profiles_recovery`, `test_engineering_reporting`, `test_engineering_reporting_contract`, `test_rag_recovery`. Runtime 28.017s. Runner nạp explicit local `tests` namespace để tránh package `tests` cài sẵn của system Python. Lần đầu chạy plain `python -m unittest tests...` exit1 vì namespace collision, không phải test assertion failures.
- Hai probes offline ở trên tái hiện gaps mới ngoài 52 tests. Lần đầu probe workforce dùng sai tên event column và một probe thiếu mock attribute nên exit1; đã sửa probe, kết quả cuối exit0. Không chỉnh source để làm test qua.
- Review đọc callers trong `engineering_operator.py`, `engineering_planning.py`, `engineering.py`, `service.py`, `store.py`, worker và view/controller; xác nhận worker AUTO branch vẫn giữ PAUSE/OFF/CANCEL/deadline fences trong tests; scope/hash retry tests PASS; report JSON escaping dùng `json_escape(...to_json).html_safe`.

**Verdict tại snapshot review:** sửa findings 1–2 trước khi gọi batch source-repair hoàn tất. Các fixes tiếp theo phải được read-back và test lại; bản review này không tự xác nhận deployment hoặc Human UAT.

Không kiểm tra live deployment/provider/UI/n8n business effects hoặc full regression. Rủi ro còn lại: GitHub duplicate comments khi crash/concurrent, report UI chưa reproduce và RAG chưa calibrated trên live corpus.

## Reviewed resolution — sau hai fixes

Reviewer đã đọc lại source thực, callers và tests, không chỉ dựa vào thông báo agent hoặc image build:

- **Finding 1 RESOLVED.** `build_workforce_profiles` hiện đọc lifecycle events từ queue đang executing, có join run/actor và filter project6/openclaw; event mới nhất quyết định handoff, completion/failure xóa active role. `result.agent` vẫn là fallback khi không có lifecycle event. Tests mới bao gồm BA → PM handoff, completion, failure đè stale result.agent và loại finished/queued/khác project/engine/actor. Reviewer chạy lại chính probe `engineering_planning.generate` trước provider boundary: lần này `active model role=ba profile.status=RUNNING`, event thực đã lưu `AGENT_STARTED/ba/RUNNING`; assertion PASS, exit0. Như vậy không chỉ test một projection row được dựng thủ công.
- **Finding 2 RESOLVED.** `_dense_search` except hiện set `self.dense_state='FALLBACK'` trước log/return. Regression `test_malformed_dense_response_preserves_partial_lexical_fallback` dùng đúng case payload None và query đã tái hiện, PASS. Regression trạng thái READY/FALLBACK/READY/DISABLED qua successive searches cũng PASS.

Lệnh reviewer thực chạy từ `openproject/ai`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_engineering_profiles_recovery tests.test_rag_recovery.RAGRecoveryTests.test_malformed_dense_response_preserves_partial_lexical_fallback tests.test_rag_recovery.RAGRecoveryTests.test_partial_lexical_fallback_requires_dense_unavailable_and_resets_each_search -v
```

Kết quả **12 tests PASS, exit0, 2.952s** (10 workforce + 2 RAG); probe planning thật với provider mocked **exit0**. Không mở rộng test scope hoặc sửa implementation trong re-review. Các 52 tests trước fixes vẫn là evidence của snapshot trước; không cộng 12 lượt rerun thành 64 test độc lập.

**Final review verdict:** source fixes được chấp nhận trong phạm vi đã review; không còn finding phải sửa trước source-repair handoff. Giữ nguyên follow-up GitHub duplicate/crash/concurrency, hardcoded UI debt, report empty UI NOT REPRODUCED, n8n event publication chưa sửa, RAG calibration và Human UAT chưa xác minh. Reviewer không xác nhận candidate image đã serving hoặc live state đã được sửa.
