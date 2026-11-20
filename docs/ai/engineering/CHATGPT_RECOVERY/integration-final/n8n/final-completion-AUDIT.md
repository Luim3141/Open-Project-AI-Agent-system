# n8n final completion — audit và bằng chứng mới

Audit `2026-11-03` đọc `workflow_history` qua `activeVersionId` của actual MAIN. 16/16 published và active; bản nguồn đầy đủ giữ ở private operator directory, artifact công khai chỉ chứa hashes, IDs, trigger, fixed endpoint và timezone. `final-completion-published-audit.json` là before-change snapshot; không suy rằng active đồng nghĩa business PASS.

| WF / actual ID | Contract, authority và side effect | MAIN evidence / giới hạn tại audit |
|---|---|---|
|01 `X2O2QdPY6QLOrWqL`|HeaderAuth + caller Bearer; explicit Native ID hoặc registered pinned file; actor/canonical SQLite, FTS, Qdrant và exact citation|Existing Project6 file ingest/replay/search/read proof giữ nguyên; candidate bổ sung observer cho completed Command Center file command|
|02 `Anl8LNdN4NNTKRpe`|Human sync hoặc signed source event → fixed callback; Native visibility/version inventory, không physical delete|Existing33 source-event receipts; source392 event3388 `SOURCE_OBSERVED` mới. Không thử Native delete trên MAIN|
|03 `XoP4M520TMG3WgeY`|Caller-bound natural request start/status; candidate signed planning observation đọc actual admission; Engineering Worker vẫn sở hữu planning|Candidate observer cần deploy/read-back; historical clone deterministic Native request không được coi là Gemini planning mới|
|04 `elfapV5D2PTnLiHW`|Signed execution lifecycle / GitHub delivery observation; durable correlation và ACK|Existing retained3074 và11 GitHub receipts không replay|
|05 `xCZFw45fmDQG5gNq`|Authenticated exact owned proposal preview; không approval|`PENDING_OWNER_ACTION` cho positive MAIN human approval path|
|06 `Jq18aFSqfuUybEic`|Authenticated exact decision/hash → Native transaction/read-back; no impersonation|`PENDING_OWNER_ACTION`; không fake Owner approval|
|07 `BpCQrGR866vg4BqQ`|Daily08:00 Asia/Bangkok cron + signed collector; valid readers20–23, immutable receipt reuse|Existing actual cron3089 READY4/4 giữ nguyên; không phát thêm model request|
|08 `RXWjVUL8ozqhjY4w`|Native Sprint/date/relation risk snapshot và persisted operational report/notification|Audit tìm thấy actual human contract bỏ `project_id`; candidate strictP6 scope + completed command observation sửa đường này|
|09 `tOyBIPw6sGjgzjtU`|Explicit context / Bug triage / exact proposal; Native transition thuộc approved action riêng|Candidate P6read-only triage; P6approved transition không được tự giả lập. MAIN transition còn `PENDING_OWNER_ACTION`|
|10 `tOY7QUa9SrWPOe9e`|Immutable WBS draft/get; approved materialization riêng; candidate reads real PUBLISHED PM/BA Native unit mapping|Candidate strictP6 draft/get và planning observer; P6adopt/next/dependency không được mở tự động|
|11 `LeRVT3LWNBkJ2iz3`|QA evidence + signed tested commit/command/Reviewer/QA result; does not grant Native approval|Existing10 MAIN QA observations giữ nguyên|
|12 `ZkgS8RZbPRA2zbhQ`|Friday17:00 Asia/Bangkok `0 0 17 * * 5`; signed weekly collector,4valid readers and persisted receipt|Current Tuesday03/11. Existing human READY + isolated actual-service cron proof giữ nguyên; current-period MAIN `ACTUAL_CRON_FIRED` chưa có, không đổi production schedule|
|13 `2tr0jpqaaAiq9IOU`|Owned feedback / `INDEX_VERIFIED` → exact Native version, vector+lexical and citation verification|New actual3394 `INDEX_VERIFIED`, source392/v0; historical385DEAD preserved|
|14 `8ycOUQy9gtT60nkN`|Owned recovery / `INDEX_FAILED`; Gateway knowledge worker owns bounded retry, n8n observes durable job|New actual3393 `WAITING_RETRY` → worker attempts2verified → actual3394 `INDEX_VERIFIED`; positive MAIN proof below|
|15 `NLugfE3U8dBS88Wg`|Human integrity / signed quarter-hour reconciliation; fixed Native/SQLite/vector read and bounded cache repair|Existing2MAIN receipts; new proof did not delete/corrupt vectors or reset verified jobs|
|16 `5FRYNPSot18UDpKa`|Quarter-hour monitor + HeaderAuth machine webhook; persisted health/notification, no inference|Existing healthy-after-recovery bucket preserved; health is separate from provider/business readiness|

All machine integration events carry durable event ID, source ID/version, minimal bounded payload, Project6, timestamp, idempotency key and correlation. HeaderAuth protects ingress; fresh HMAC plus exact stored-event equality and numeric execution ID protects callback. Gateway durable outbox owns five attempts/backoff/DEAD; callback receipts/claims ensure idempotency. Existing normal worker cadence remains five seconds; no fast drain or rate limit changes in this qualification.

## New WF14 actual MAIN evidence

One newly authorized noncoding Project6 source392/v0, immutable marker and frozen text in `final-completion-source392-frozen.json`; no Native delete, no Project5 business write. The failure was a process-local override of that single Service instance's `sync_canonical_native` method. The serving Gateway worker, Qdrant service and all other jobs were untouched.

First fixture job naturally retried in five seconds before its callback was observed, so actual3389 correctly returned `SUPERSEDED`; this remains explicitly recorded in `final-completion-main-wf14-recovery-attempt1.json`, not a WAITING_RETRY PASS.

Second job reused the same source. After an actual failed first attempt it held **only its own** `next_at` for30seconds so the normal outbox could observe the durable retry state. It did not shorten a retry, reset attempts, change global backoff, or add a worker. Actual3393 observed `WAITING_RETRY` attempts1; the existing worker subsequently verified attempts2; actual3394 verified current Native version/citation. `final-completion-main-wf14-recovery.json` contains job/event/correlation/execution IDs and the explicit30second controlled observation hold.

`final-completion-main-wf14-readback.json` independently confirms: Native392/v0; canonical and actor20 SQLite documents; one FTS row/chunk per document; two actual Qdrant points; current `/work_packages/392` citation; retained actual3393/3394 SUCCESS with stored exact event IDs; API projection binding; engineering OFF; zero pending integration events at readback. One historical385DEAD remains protected. This proves failure/recovery plumbing and exact citation, not semantic benchmark quality or browser interaction.

## Architecture delta awaiting final root integration

Candidate strictP6 scope is explicit, numeric6 only, on WF08/09/10; omitted scope keeps legacy contract. It exposes read/draft/proposal routes while rejecting P6WBS materialization through this adapter. Actual Native actor membership/role is revalidated by Gateway and callback. Fixed planning events observe actual admission and PUBLISHED PM/BA Native units, without starting a second planning/coding scheduler. Fixed UI command events observe previously successful Gateway commands and re-read report/source/index/draft; callbacks never repeat their business command. These candidate changes require exact-source clone qualification and root deploy/publish before MAIN claims.
