# 02 — TEST MATRIX / CLAIM-TO-EVIDENCE / EXECUTION WAVES

**Định nghĩa PASS:** test THỰC CHẠY trong lượt audit, assertions kiểm đúng behavior, có exit code + raw log (đã che secret), đối chiếu source/target và timestamp. Mock-only có thể PASS_UNIT nhưng không là PASS_E2E. `NOT_RUN`, `SKIPPED`, `XFALL`, `BLOCKED` không là PASS. Test thất bại phải mở defect ID.

| Case ID | P | Vùng | Thực hiện | Expected/Oracle | Evidence |
|---|---|---|---|---|---|
| CLM-01 | P0 | 113 tasks | Parse `TASKS.json`, đối chiếu 113 task và status với source, test, artifacts | Không thấy DONE thiếu chứng cứ; ghi VERIFIED/UNVERIFIED riêng | claim_ledger.csv |
| CLM-02 | P0 | 37 suites /184+ | Parse runner và thực chạy; liệt kê ID, test names, skipped, mocks, exits | Count thực khớp hoặc báo sai lệch; không coi unit = E2E | raw stdout, suite manifest |
| CLM-03 | P1 | Runtime RAM | `docker stats`, WSL/task-manager snapshot đo trong tình huống mô tả | Dùng measurement thực, không suy từ phép cộng ước tính | measurements.csv |
| BASE-01 | P0 | Dirty Git | `git status`, `git diff`, branch, SHA | Không ghi đè thay đổi có sẵn | baseline.md |
| BASE-02 | P0 | Main/staging isolation | Inspect compose projects, volume names, DB host, ports, image digests | Không trộn DB, volume, project IDs; destructive tests chỉ trên disposable staging | isolation.md |
| BASE-03 | P0 | Secrets | Scanner redacted + manual bind/env/log/code review | Không key/token trong Git hoặc phản hồi public | secret_finding_redacted.md |
| OPS-01 | P1 | Bootstrap | Bật Docker Engine từ trạng thái tắt, đo thời gian đến health, không nhập key lại | Container đủ thành phần tự phục hồi; readiness thật, không chỉ running | video/health log |
| OPS-02 | P1 | Restart exceptions | Kiểm tra `unless-stopped`, manual stop behavior; thử trong stage | Document exceptions, không khẳng định always restart | restart.log |
| OPS-03 | P1 | Persistence | DB, n8n credentials (không xuất secret), queue receipts qua restart | Không mất task/write receipt, snapshot ổn | before-after IDs |
| QTT-01 | P0 | Tunnel owner intent | Cloudflared container config/exposed service, không auto-remove | Quick Tunnel tồn tại, đúng target, không public nhầm dịch vụ | quick_tunnel_audit.md |
| QTT-02 | P0 | Remote anonymous | Test từ ngoài LAN không auth; thử route hợp lệ, route private; không fuzz | App public entry permitted, protected data 401/redirect; private API inaccessible | raw HTTP status scrubbed |
| QTT-03 | P0 | Remote role session | Playwright E2E 2 users khác role, logout/session fixation/IDOR checks | No cross-account read; RBAC đúng, cookie/CSRF/proxy headers hợp lệ | traces/screenshots sanitized |
| QTT-04 | P1 | URL rotation | Staging tunnel restart khi được phép và capture URL trước/sau | Detect changed URL, share securely; không break stack | log scrubbed |
| QTT-05 | P1 | Streaming | Detect SSE/WebSocket app paths and test through tunnel | SSE không mặc định hoạt động; polling fallback nếu cần; WebSocket được kiểm thực | browser network trace |
| QTT-06 | P0 | Origin isolation | Enumerate router/controller mappings của n8n editor, operator, DB, Rails internal | Privileged endpoints không reachable qua remote unauthenticated | route/access matrix |
| QTT-07 | P1 | Traffic safety | Small remote smoke only, DNS/TLS/redirect check | App usable, no secret/host header spoof, errors explained | HAR sanitized |
| AUTH-01 | P0 | PM-only-write | Real PM can create/update/transition on stage fixture | Native receipts/changes present with matching actor | native readback |
| AUTH-02 | P0 | Non-PM denied | BA/FE/BE/QA cannot create/update via UI/REST/MCP | Each denied, comment allowed as policy | 5x role matrix |
| AUTH-03 | P0 | Gates/consent | Forged approve/replay/stale version/out of scope | Host/native deny, no side-effect | before-after native hashes |
| AUTH-04 | P0 | Multi-project ACL | Cross-project work package/comment/memory retrieval | No data leaked by RAG/list/search/insights | negative test |
| USERS-01 | P1 | 20 accounts | 20 independent stage identities and permission mapping | 20 concurrent sessions (not 20 LLM calls), no session bleed | browser artifacts, user matrix |
| USERS-02 | P1 | Load 1→5→10→20 | k6 realistic read-only workload LAN/staging only | Error rate/latency measured, no impossible SLO assumptions | k6 summary, CPU/RAM |
| USERS-03 | P1 | Queue fairness | Virtual clock/fake provider test 20 users + 1 abusive user | No starvation within defined service policy; bounded memory | queue logs + assertions |
| AI-01 | P0 | API free guard | Inspect app setting plus verify AI Studio tier/billing with owner | Backend cannot silently switch paid; tier externally verified or BLOCKED | billing check redacted |
| AI-02 | P1 | Quotas | fake provider at RPM/TPM/RPD boundaries; retries/timezones reset | No override assumptions; `WAITING_QUOTA`; deterministic still works | test outputs |
| AI-03 | P1 | 429 vs 503 | Distinguish quota response, transport/proxy errors, service unavailable | bounded retry/backoff, no retry storms | redacted trace |
| AI-04 | P0 | Write ambiguity | Timeout after provider proposes mutation / native maybe succeeded | reconcile receipt/idempotency, no duplicate write | native readback IDs |
| AI-05 | P1 | Model registration | SDK runtime `models.list` or safe equivalent and compatible model name | Model actually available for project; no invented version assumption | metadata redacted |
| AGT-01 | P1 | Supervisor | Plan/order/delegation, partial agent failure, stop/restart | contracts and checkpoint hold, no silent fake success | structured trace |
| AGT-02 | P1 | Role agents | PM/BA/QA/DEV/Reviewer task fixtures with independent output assertions | Correct tools, scope, and human approval | JSON result assertions |
| MEM-01 | P0 | Second Brain ACL | Add dummy docs across two actors/projects on staging | Unauthorized query cannot retrieve other project content | exact retrieval list |
| MEM-02 | P1 | Retrieval accuracy | source provenance/date/duplicate test | Result cites correct source, stale marked | golden set recall |
| N8N-01 | P0 | n8n security | Webhook auth/scope/editor/public API isolation | n8n admin private, events signed/authorized | endpoint map |
| N8N-02 | P1 | Daily/Sprint reports | stage fixture known tasks, run once twice, duplicate event | Counts correct, idempotent, read-only for non-PM | report-vs-query reconciliation |
| N8N-03 | P1 | Retry/restoration | Queue stops during n8n execution then resumes | Durable result and no duplicate business write | events/receipts |
| UI-01 | P1 | AI Control Center | actor-specific audits/queue/quota/approval E2E | Correct scope, no other users' private chats | screenshots+API response |
| BUG-01 | P1 | Negative cases | missing IDs, ambiguous natural language, non-working dates, stale gate | Clarifies; no unauthorized side effect | test matrix |
| REC-01 | P0 | Backup restore | only disposable stage verified; same DB+attachments+SQLite receipts | data parity, SHA-256 snapshot, restore within agreed plan | restoration log |
| SEC-01 | P0 | Dependency/secrets | static scanning (Trivy/manual); confirm license & images pinned | No unaddressed high severity exploitable in exposed path | triage register |
| SEC-02 | P1 | Browser baseline | Playwright and optional ZAP PASSIVE staging, no brute/active scan public | Findings reviewed, no red critical | report |

## Execution waves
1. **Wave 0 (read-only):** BASE, CLM, QTT route mapping, secrets metadata, billing eligibility; STOP if destructive test not isolated.
2. **Wave 1 (offline deterministic):** unit/contracts/fake providers/fair queue; mutation code not exercised on main.
3. **Wave 2 (staging integration):** native workflows, n8n, Second Brain, REST/MCP identity; ensure test fixtures and DB isolation.
4. **Wave 3 (user E2E):** browser 5 roles + 20 test sessions, Quick Tunnel remote authenticated/anonymous.
5. **Wave 4 (resilience):** staging restart, quota/503 injection, rollback, backup-restore, low-rate load (public smoke only).
6. **Wave 5 (release):** code review + fresh tests + user acceptance + handoff.

## Evidence schema
- `case_id,claim_id,scope,environment,commit_sha,command,test_name,started_at,ended_at,exit_code,assertions,expected,actual,status,evidence_relative_path,defect_id,notes`
- Không ghi API key, public token, session cookie, full query strings chứa bí mật hay chính xác tunnel URL vào artifacts đưa lên Git.
- Mỗi PASS phải liên kết ít nhất một file raw evidence. Screenshot có thể bổ sung, không thay assertions.
