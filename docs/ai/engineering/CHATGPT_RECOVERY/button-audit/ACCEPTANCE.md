# AI Control Center — button audit, 05/11/2026

**CORE_SAFE_ACTIONS_MAIN_VERIFIED — PERFORMANCE_GATE_OPEN. Chưa đạt `AI_CONTROL_CENTER_DEMO_READY`.**

Đây là nghiệm thu có giới hạn và checkpoint mới nhất, không phải tuyên bố đã hoàn thành toàn bộ mục tiêu Owner. Root làm tuần tự, không tạo subagent hoặc lịch chạy lại. Lịch one-shot đã được xóa khỏi app sau khi chạy.

MAIN cuối: Gateway `sha256:77213702ef933943a1fbee6feffc0d410062b8f16928dd3d1621f9489e581a12`; Core `sha256:5ee7a24482be81dd7312e8c4560773aede32ec9f8bc2f6da9593c9f223e1b822`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`.

## Inventory và mức bằng chứng

Actual frontend có **70 vị trí khai báo button**, gồm các nhánh điều kiện loại trừ nhau. Snapshot DOM cuối có **567 button instances,302 links,283 summary,12 inputs,4 select,1 textarea =1169 controls**, gồm tab ẩn và các hàng lặp. Snapshot đầu1174 controls/570 buttons/305 links giữ riêng; khác biệt không phải số chức năng bị xóa. Không gọi567instances là567chức năng độc lập.

Theo70binding sites: **57 MAIN_UI_PASS,7 CLONE_PASS_ONLY,4 SAFETY_NOT_EXERCISED,2 NOT_TESTED**. MAIN_UI_PASS là đã thao tác một instance/branch đại diện của binding đó, không xác nhận mọi hàng lặp. Hai NOT_TESTED là nhánh toast success/error server-rendered không xuất hiện trong UAT JSON command. Nút đóng toast client đã bấm trên Sync thật. Bốn safety rows là RAG ingest/search/file-search/file-read ngoài phạm vi, không tiêu quota để kiểm giao diện.

[Bảng đầy đủ70buttons với đủ handler/endpoint/operation/permission/precondition/response/persistence/UI feedback/evidence/result](button-acceptance.csv), [JSON](button-acceptance.json), [source inventory](source-inventory.json), [DOM cuối](dom-final.json), [ledger mọi instance, chưa tự nâng PASS](dom-control-ledger.csv). Binding-level coverage và instance-level presence là hai thước đo khác nhau.

| Tab | Button | Expected | Actual | MAIN_UI | MAIN_API | CLONE | Error Path | Evidence | Result |
|---|---|---|---|---|---|---|---|---|---|
| Global | RUN ONCE no-work | Reject, không replay |422/NO_ELIGIBLE_WORK, pending disabled, không admission |PASS|PASS|PASS fixture|No-work MAIN; eligible/provider/PAUSED fixture|browser-uat; main-control-readback|MAIN_UI_PASS|
| Global | OFF/AUTO/PAUSE/TẮT PAUSE |Desired/effective/revision bền vững |OFF→AUTO_IDLE11/11→PAUSED; TẮT PAUSE→OFF→PAUSED; finalrev44 |PASS|PASS|PASS|Revision/race/quota fixtures|main-control-readback|MAIN_UI_PASS|
| Execution | Resume/Cancel |Safe checkpoint/own run; reject unsafe/completed |Không tạo blocked/active MAIN; completed391 dedup/no-cancel trong actual Native clone |Safety not exercised|Safety not exercised|PASS contracts/Native|Unsafe/duplicate/queued/cancel/checkpoint contracts|qualification; image-regression|CLONE_PASS_ONLY|
| Global/GitHub | Sync |ACK→operation→completion, refresh không F5 |12checked/0changed; hai final operations completed; chuyển tab khi pending |PASS|PASS|PASS|Concurrent/transport/restart unknown fixture|browser-uat; main-control-readback|MAIN_UI_PASS|
| Global/Reports |Schedule Save/Close/X |Versioned save, validation, preserve other fields |Daily08:00→08:01→08:00; final Weekly09:00→09:01→09:00; invalid99 blocked, close restores |PASS|PASS|PASS actual Native|Stale/CAS race/duplicate/invalid timezone fixtures|browser-uat; schedule-200-main.png; main-control-readback|MAIN_UI_PASS|
| Reports |Full text/Raw/sections/close/Copy/Export |Read exact stored document |6766chars/6sections, actual clipboard paste6766, export7242bytes |PASS|Read PASS|Reader contracts|Loading guards MAIN; timeout/stale/error fixture|browser-uat|MAIN_UI_PASS|
| Backlog/Workforce/Execution |Inspector,Copy IDs,intake open/close |Correct run/full ID; no empty-copy action |b7fd COMPLETED/WP391, related96b4 and301db; five inspector panels; empty Supervisor Copy disabled |PASS|Monitor reads PASS|Focus contracts|Clipboard fallback source; no artificial live outage|browser-uat|MAIN_UI_PASS|
| Global |Snapshot+AI / Intake submit |Guarded single side effect |Controlled fixture contracts only, no MAIN provider/task execution |Not exercised|Not exercised|PASS contracts|Duplicate/budget/planning guards|image-regression|CLONE_PASS_ONLY|
| Notifications |Open/read |Correct run; dismiss persisted |301db inspector; earlier owned notification124→123 |PASS|PASS|Contracts|Permission/idempotency contracts|browser-uat|MAIN_UI_PASS|
| Integrations |Workflow details/action |Metadata and correct target tab |WF01 expanded; action selects knowledge without query |PASS|Metadata read|Contracts|Stale/unknown labels remain explicit|browser-uat|MAIN_UI_PASS|
| Knowledge |RAG actions |Preserve frozen scope |Mapped DOM/source, not executed |Not exercised|Not exercised|No semantic claim|Frozen per Owner|source-inventory|SAFETY_NOT_EXERCISED|
| All |Tabs/F5/Back/Forward |Correct tab/history, responsive |36switches correct,9tab F5 restores, Back backlog/Forward reports; slow F5 remains |PASS functional|N/A|Navigation contracts|Final reload tool timeout recovered to reports|tab-switch-main; f5-main; final-page-smoke|MAIN_UI_PASS with performance FAIL|
| Links |Native WP |Open exact Native record |391/activity, #391, READY FOR RELEASE visible |PASS|Six source records v10|Native clone|None forced|browser-uat; final-live-verification|MAIN_UI_PASS|
| Links |GitHub/n8n |Navigate correct URL; respect external session |PR12 logged-out404; n8n signin redirect |Navigation only|GH Sync reads12|N/A|External content not accepted in browser|browser-uat|SAFETY_NOT_EXERCISED for authenticated content|
| Reports |Filter/pagination |Inventory existing controls |Không có report-filter/pagination widget trong modern source/DOM; không thêm feature |N/A|N/A|N/A|N/A|source-inventory; dom-final|NOT_APPLICABLE|

## Những thay đổi đã triển khai

- Schedule: expected_updated xuyên suốt catalog/Service/Rails/DOM, SQL CAS chống lost update, giữ các trường không sửa, reject timezone không hợp lệ, Save liên tiếp cập nhật version. Sửa thiếu allowlist từng làm MAIN trả422.
- Report: actions disabled khi loading/error; giữ Markdown gốc, timeout/stale response guards; modal focus/Tab/ShiftTab/Escape và overflow. Ở zoom200% sửa số trong form lịch bị CSS OpenProject ghi đè thành chữ tối/nền trong suốt; thêm accessible labels, wrapping và chiều cao theo viewport.
- Navigation/transport: Turbo before-cache từng ngắt submit handler khi trang vẫn hiện; dùng pagehide/pageshow và root guard. HTML POST fallback dùng303 về canonical path, không mắc `/commands#tab-backlog`; reject empty schedule payload.
- Copy: empty Run ID disabled và có lý do, không báo copy thành công với chuỗi rỗng.
- Performance: Gateway CPU1→2 sau đo saturation99.49% và throttling; RAM giữ384MiB. Reporting/engineering/lifecycle schema chỉ khởi tạo một lần mỗi Store sau commit, không tranh writer lock trong warm dashboard reads. Không cache authorization hoặc dữ liệu nghiệp vụ/RAG. Held-writer regression RED trên image v9 → GREEN trong221tests image v10.

## Hiệu năng: có cải thiện, chưa nghiệm thu

Mỗi batch Gateway có30 HTTP samples trên cùng laptop/runtime, endpoint engineering_status, normal polling có thể đồng thời. Resource/image thay đổi theo từng stage được ghi riêng; không gộp thành một phân phối. p95 dưới đây là nearest-rank estimate của batch30, không khẳng định tail ổn định lâu dài.

| Stage | n | p50(s) | p95(s) | Evidence |
|---|---:|---:|---:|---|
| Phase baseline,1CPU |30|2.78145|23.1726|before.json|
| Resource-only,2CPU |30|3.1975|10.8432|resource-after.json|
| Earlier v2 |30|1.81075|5.2506|performance-v2.json|
| v9 |30|2.4168|7.1408|performance-v9.json|
| Final v10 |30|2.4294|5.8609|final.json|

Final first request7.2403s; payload khoảng638.5KB. Snapshot resource: Gateway30.77%CPU/159.5MiB/384MiB, Core3.10%CPU/1.249GiB, n8n0.48%CPU/576MiB. Không có bằng chứng thiếu RAM384MiB trong batch này, nên không tăng RAM. DockerVM16CPU/12GB và laptop24GB được kiểm trước tăng CPU; không tăng vô hạn hoặc dừng dịch vụ khác.

36tab click+DOM read-back automation roundtrips: p50=331.5ms, range201–580ms. Đây gồm overhead công cụ, **không phải paint latency**; chưa chứng minh gate<200ms. Nine successful reload/selection observations trên cặp v9 cùng Core cuối: median8.076s, range6.309–11.588s; không khẳng định stable browser p95 từ9mẫu. Một reload final v10 vượt deadline công cụ, sau đó đúng tab Reports/PAUSED, console không có error. Không lấy tool timeout làm giá trị HTTP/paint cụ thể.

Read profile trước: một warm call370SQLite statements, khoảng0.85s trong execute,31connections;5Native calls khoảng0.38s, process tổng1.72s. Đây là một profile chẩn đoán, không phải batch distribution. Đã tái hiện warm setup tranh writer lock và sửa; tail end-to-end vẫn5.86s. Aggregation, synchronous Native dependencies và full-panel render/poll payload vẫn là các ứng viên bottleneck; **chưa có trace đủ để chia chính xác Rails render/DB lock/network/browser long tasks/re-render cost**. Warm initial usable<4s, paint<200ms và control ACK<2s healthy chưa có đủ phép đo browser đáp ứng. Giữ performance P0 OPEN, không đổi5samples cũ thành một p95 ổn định.

## 16 câu trả lời Owner

1. **Bao nhiêu?**70button declaration sites; DOM cuối567button instances +302links +283summary +17form fields. Có repeated rows/hidden tabs.
2. **MAIN UI PASS?**57/70binding sites với instance đại diện, lineage ghi trong browser-uat.json; không phải567/567.
3. **Chỉ clone?**7sites. Bao gồm fixture/contract trong immutable image; không gọi unit fixture là browser clone PASS.
4. **Nút bấm không làm gì?**Đã sửa empty Copy, loading reader actions và submit lifecycle. Không thấy core enabled no-op trong các thao tác đã làm. Hai server-toast branches và4RAGsites chưa được thao tác, không suy ra chúng PASS.
5. **AUTO/OFF/PAUSE MAIN?**Có, actual idle/all11units delivered, receipts/revision/read-back; final PAUSED44/queue0. TẮT PAUSE riêng cũng được bấm.
6. **Resume/Cancel?**Safe/unsafe/duplicate/queued/active-cancel logic trong contracts; completed391 dedup/no-cancel trong actual Native clone. Không tạo blocked live task và không Resume391/394.
7. **Schedule ghi thật?**Có. Daily và Weekly đều thay đổi có hoàn nguyên, Save hai lần cùng modal; read-back cuốiDaily08:00/WeeklyMonday09:00; updated token mới hợp lệ. Không sửa SQLite để giả thao tác.
8. **Copy/Export?**Có, clipboard paste6766characters, actual export7242UTF8bytes; Run/Plan/Workforce ID paste đúng.
9. **Zoom200%?**Owner xác nhận; đo DPR2.5/557x478. Final Core form lịch readable, modal429px trong478px và không tràn ngang. Earlier report có internal scroll. Sau F5 zoom quan sát trở vềDPR1.25; không coi mọi scenario sau đó là200%. Screenshot schedule-200-main.png.
10. **p50/p95 trước/sau?**Gateway30/batch:2.78145/23.1726→2.4294/5.8609s. Tab tool-roundtrip36samples median331.5ms; paint/before-after page p95 chưa đo đủ. F5 vẫn chậm; performance gate FAIL/UNVERIFIED.
11. **Polling mất state?**Search391 vẫn một row qua polling, sau blur/switch tab vẫn giữ. Modal edit không bị reset; schedule CAS bảo vệ stale editor. Node tests xác minh non-overlap/unknown no-replay, không khẳng định mọi field/long task đã đo.
12. **F5/Back/Forward?**Đúng trang/panel khi scripts khởi tạo xong; Back backlog và Forward reports đúng hash. Final reload có tool timeout rồi phục hồi; đây vẫn là lỗi trải nghiệm tải chậm.
13. **Native WP?**Six386/387/389/390/391/394 READY FOR RELEASE/v10, actual391 link đúng.391 và394 SUCCEEDED, không replay/Done giả.
14. **Gateway/n8n/Worker regression?**Exact source/images +221tests +actual Native/Core clone +Main health/read-back. Gateway/Core healthy,n8n readiness200/16active workflows, workerALIVE; không có business E2E mới. **OpenClaw Gateway health DOWN/CONNECTIVITY_CHECK_FAILED**, không được gọi inference-ready chỉ vì workerALIVE.
15. **Project5?**PASS13hash scopes;341WPs/344relations/968journals giữ nguyên, global roles/workflows/settings/users không đổi. native-integrity-after.json.
16. **Cản demo?**F5/initial usable và tail latency còn chậm; thiếu precise browser/Rails tracing và ACK distribution; OpenClaw Gateway DOWN; GitHub/n8n browser chưa có authenticated content proof. Các provider-backed actions chỉ clone/contract,2server-toast branches chưa test. Không cấp chứng nhận DEMO_READY.

## Evidence và bàn giao

[Final runtime/source/counters](final-live-verification.json), [control/schedule receipts](main-control-readback.json), [221 immutable tests](image-regression-reports.json), [exact Core/Native clone](clone-qualification-caption.json), [qualification gate](qualification.json), [schema lock RED→GREEN](schema-lock-red-green.json), [browser record](browser-uat.json), [protected data](native-integrity-after.json), [rollback/deployment receipt](candidate-v10/deployment.json).

Core cuối reuse đúng image đã qua actual Rails login/session/CSRF/render clone; v10 clone ghi rõ reuse, Gateway v10 vẫn qua actual Native integration. Minimal rollback snapshot ở private operator release directory; không restore DB/DR hoặc roll back user data. Không push/merge GitHub, không thay Mini Task Manager, RAG semantic FAILED/FROZEN, không tạo coding admission;21runs/531provider receipts giữ nguyên. Final PAUSED/delegationOFF/queue0 và lịch restored.

Công việc còn dở: đo request-stage Rails/Gateway/DB/network và browser long tasks bằng instrumentation hợp lệ, tối ưu bottleneck đã đo, kiểm OpenClaw readiness mà không tạo coding task/provider quota, rồi đo lại đủ browser/control samples. Chỉ rerun các regressions bị ảnh hưởng sau thay đổi; không chạy coding E2E hoặc RAG qualification. Không tự lên lịch lại.
