# Phase2 current — 01/11/2026

Phase2 sourceversioning current:587allowlistedfiles/privateGitcommit27db752d686d86b9683e7e7a6b15f6a223f48939; no rootremote/push. Final15packagedsourcehashesmatch; hostdelivery/adapter version separatelyrecorded. Actualrestore221PGtables+2SQLite completed. Read FINAL_PRE_ROLLOUT_ACCEPTANCE.md; audit below is baselinePhase1.

---

# Kiến trúc và source audit — 01/11/2026

Đây là baseline và batch repair đầu tiên, không phải nghiệm thu toàn bộ hệ thống. Không Computer Use; không thực thi historical live fixtures. Repo chính đang `codex/local-multi-agent-upgrade`, HEAD `de7fe8f`, chỉ 2 tracked files, không remote; phần lớn source untracked. Repo demo đang `codex/mini-task-manager-ready`, HEAD `def9d0a`, origin `Luim3141/mini-task-manager`, `dev/` untracked. Không reset/clean/commit toàn bộ workspace.

## Baseline thực tế

- Web MAIN `qldapm-core:engineering-continuation-r24-20261031`, image `a4fa8150728b…`; Gateway MAIN `qldapm-ai:engineering-continuation-r24-20261031`, image `fcb44c49afb9…`. `run-20261101T035551Z/runtime-before.json` lưu ID đầy đủ/mounts; không xuất env/secrets.
- Source/runtime baseline: 155/162 file khớp SHA256. 7 file không có trong image: e2e_demo, intent_evals, n8n_indexing_hook, proposal_aggregation, proposal_ux, scheduler_registry, supervisor_isolation. Thiếu file không tự chứng minh đường production nào đang gọi nó; chưa sửa Dockerfile để copy tất cả một cách mù quáng.
- Project5 SQL: 341 WP, max lock4, updated_at `2026-10-29T10:08:56.897949Z`. Project6: 7 WP; #379 status7 lock4; #386 status1 lock2; #385 vắng. Chưa có business write từ batch này.
- Gateway control OFF; active ai_queue rỗng; 358 provider receipts tại baseline sau restart. Không inference mới. OpenClaw CLI `2026.10.8`, gateway health `ok=true`, heartbeat0, Node runtime24.22.2; Windows scheduled task QLDAPMEngineeringDelivery Running. Health không chứng minh fresh delivery.

## Call graph đã đối chiếu

Các đường dẫn source bên dưới tương đối với `openproject/ai/`.

| Tuyến | Caller → endpoint/callee | State/auth/failure boundary | Evidence và phân loại |
|---|---|---|---|
| UI→Rails | `_engineering_command_center.html.erb` forms → `QldapmAIController#commands` | Login, role PM/AI_SYSTEM_OWNER, action allowlist, JSON arguments | CONNECTED source; Ruby contract tests, UAT pending |
| Rails→Gateway | controller `bridge` → AiBridge → `gateway/bridge.py`, `service.py` command | Signed assertion/nonce, actor/project scope | CONNECTED source + isolated bridge tests; chưa live command mới |
| Gateway→Native/PG | `service.native_actor` → `native.Native` APIv3 → Rails/PG | Per-user credential, identity/project check, deadline, NativeError | CONNECTED source; PG read-only baseline |
| Gateway→SQLite | `engineering.py` → Store ai_queue/ai_runs/agent_runs/events | BEGIN IMMEDIATE, actor/project, lease, receipt | CONNECTED; core queue tests, three fixes |
| Admission→host | `engineering.claim` → `automation/engineering_worker.py` operator CLI | TaskScheduler, one executing slot, worker heartbeat | CONNECTED source; worker task live, fresh delivery NOT VERIFIED |
| Host→OpenClaw | worker `agent_process` → WSL CLI | Dedicated user/worktree, gate, deadline/pause/cancel polling | AUTO fence BROKEN→PATCHED SOURCE; CLI health only live |
| OpenClaw→provider | `automation/openclaw_provider_gate.py` → shared Gemini client | Existing quota/admission, no provider/model change | Receipt history exists; no new inference/retry stress test |
| OpenClaw→Git | worker/delivery adapter worktree/test/revision stages | Revision evidence and durable stage journal | Historical artifacts; fresh execution NOT VERIFIED |
| Git→GitHub | delivery publication → commit/push/PR | Exact head/base, no auto merge | PR1–6 read through GitHub plugin; no push this batch |
| GitHub→Gateway | `engineering_github_sync.fetch_pull_requests/reconcile…` | TTL/force, pagination/deadline, repository/child scope | Multiple defects PATCHED SOURCE; isolated tests; live mutation pending |
| Gateway→Native writeback | `engineering_operator.native_once`, sync activities POST | Pending outcome guard, Native receipt/version | Owner resume bypass PATCHED SOURCE; sync crash window remains |
| Native→n8n | WF02 webhook | Header auth/caller bearer | Event publisher NOT VERIFIED; no automatic push observed |
| Gateway↔n8n | WF04 → `/api/v1/agent-runs/{id}/trace` | Resolve project from owned stored run | CONNECTED read contract; no Gateway lifecycle webhook publisher |
| n8n→knowledge | WF02/13/14/15 Gateway commands | Authorization, durable sync/recovery | Published graph audited; new business event NOT TESTED |
| Native→knowledge | Gateway incremental scan → knowledge_sync | Actor/project/version, durable queue | Source/historical state; fresh WP indexing NOT TESTED |
| Knowledge→vectors | ingester → Ollama/BGE-M3 + Qdrant | ACL/version/chunk hash; pending repair | ISOLATED tests; no live embedding this batch |
| Retrieval→citations | knowledge_search → service Native recheck → UI | ACL scope, current Native version | RAG policy PATCHED SOURCE; corpus calibration pending |
| Gateway→Reports | `engineering_reporting` collect/persist/list/get → controller report | Project6 scope, SQLite document/narrative | Factual provider dependency PATCHED SOURCE; DB has narrative |
| Events→Inspector | execution_events/engineering_monitor → `get_execution_monitor` → Rails execution JSON | Actor/project permissions, stored receipts | Isolated contract tests; no UI acceptance |

Không tạo Supervisor/scheduler thứ hai. n8n active không đồng nghĩa coding pipeline đã nối đủ. Upstream Paperclip/Agency/Superpowers chỉ là local adaptation; chưa kiểm toán upstream HEAD hay tuyên bố parity đầy đủ.
