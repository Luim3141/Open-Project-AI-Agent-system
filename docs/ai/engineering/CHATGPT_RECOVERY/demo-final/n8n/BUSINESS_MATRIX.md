# 16 workflow business scenarios — clone qualification

16/16 kịch bản nghiệp vụ có bằng chứng thực tế. Không đồng nghĩa mọi nhánh của 16 workflow đã được nghiệm thu toàn diện. MAIN deployment/read-back được ghi riêng trong `deployment.json` và `main-history-readback.json`.

| WF ID | Purpose | Trigger | MAIN/CLONE | Expected | Actual | Evidence | Status |
|---|---|---|---|---|---|---|---|
|WF01|Native ingestion → SQLite/Qdrant|Authenticated webhook|CLONE|Native fixture ingestion→SQLite/Qdrant read-back|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF02|Native incremental event synchronization|Authenticated webhook|CLONE|Incremental scan of isolated Native fixture and actual persisted status|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF03|Native deterministic natural-language intake/status|Authenticated webhook|CLONE|Published start/status/replay Native deterministic query|Expected business result/read-back observed|wf03-native-orchestration.json|BUSINESS PASS (bounded scenario)|
|WF04|Canonical lifecycle history/correlation|Authenticated webhook|CLONE|Canonical signed source trace observed and correlated|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF05|Exact human proposal preview|Authenticated webhook|CLONE|Exact persisted Native proposal preview, no implicit approval|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF06|Exact human decision/rejection|Authenticated webhook|CLONE|Exact explicit rejection persists and prevents execution|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF07|Scheduled daily brief for valid readers|Signed scheduled branch, bounded webhook|CLONE|Scheduled Daily branch selects valid20–23, Native GET-derived reports READY|READY 4/4, actor19 remains denied|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF08|Sprint risk report|Authenticated webhook|CLONE|Real Native sprint risk engine returns evidence|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF09|Explicit Native bug target/context|Authenticated webhook|CLONE|Explicit Native fixture target, no synthetic fallback|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF10|WBS draft and exact-hash read-back|Authenticated webhook|CLONE|Draft WBS persisted and exact hash read-back, no approval bypass|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF11|QA automated Native assertions/signed evidence|Authenticated webhook|CLONE|QA actor runs fixed Native assertion and reads signed evidence, no approval|PASSED, exact evidence replay stable|wf11-qa-readback.json|BUSINESS PASS (bounded scenario)|
|WF12|Scheduled weekly report for valid readers|Signed scheduled branch, bounded webhook|CLONE|Actual scheduled weekly branch valid readers20–23 READY with Native sources|READY 4/4, actor19 remains denied|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF13|Source-bound RAG feedback|Authenticated webhook|CLONE|Source-version-bound feedback persists/read-back; unreviewed feedback not promoted|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF14|Durable ingestion job status|Authenticated webhook|CLONE|Own persisted index job status from actual ingestion, not fake job|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF15|SQLite/Qdrant reconciliation/integrity|Authenticated webhook|CLONE|Actual SQLite/Qdrant/source integrity engine reports drift truthfully|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|
|WF16|Dependency/resources/backlog monitoring|Authenticated webhook|CLONE|Machine monitor persists real dependency/resource/backlog report|Expected business result/read-back observed|business-clone-result.json|BUSINESS PASS (bounded scenario)|

## Giới hạn nghiệm thu

- One explicitly listed valid scenario per workflow; not every generation/approval/write/error branch.
- WF03 actual start question used the Native deterministic count route. Gemini generation is not claimed by this suite.
- WF05/06 exact preview/reject only in isolated clone, no Owner approval or Native execution was fabricated.
- WF12 scheduler branch was reached through a clone-only bounded webhook; actual production cron definition is retained.
- Shared auth/error/signed-contract tests and Store idempotency tests complement these scenarios; branch-complete live retries for every workflow are not claimed.
- Raw harness 15/16 retained. WF11 was re-run through actual webhook with documented PASSED enum and repeated request identity.
