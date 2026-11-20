> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

**Current: VERIFIED / QUALIFIED_NOT_DEPLOYED.520Windows,30Linux,64browser checks PASS; exact candidate hashes in candidate-images.json.**

# Source code review — remaining development

42 mismatches classified individually; initial hashes/container paths/callers/imports are retained in SOURCE_RUNTIME_MATRIX.json. No live completion inferred from source review.

Critical fixes: Control Center fresh Native authorization; direct duplicate executor closed; real actor/project queue/worker integration; Native-only knowledge indexing, fresh retrieval ACL/version, persistence/FTS/chunks; false model/quota/readback flags removed.

Seven development/prototype modules are intentionally excluded from image context; none is a public business tool. No blind35-module copy. Other modules form runtime call graph or internal libraries, with exact decisions below.

- **agent_models.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Strict bounded Pydantic contracts; terminal result/scope/transition invariants; no native authority from IDs.
- **agent_registry.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED_WITH_LIMITATIONS. Registered handlers are local deterministic templates/rules. Historical Gemini provider metadata is not execution proof; runtime API projects local engine explicitly.
- **agent_status.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Fixed actor-scoped status and separate local status from provider circuit; database availability is not provider health.
- **app.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Authenticated shared REST/MCP/HMAC bridge. New actions use same middleware; engine documented; published schemas must be regenerated.
- **ba_agent.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Local draft templates; removed invented1.5s SLA. Citation verifies source ID/version, not business acceptance.
- **control_center_state.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Actor/project SQL pagination; registry actual local execution metadata, no role supplied by browser.
- **conversation_memory.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. In-memory convenience library, not authoritative durable context. Product continues stored AgentTask references with fresh ACL/version.
- **daily_brief.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Existing signed durable automation retained; five configured actors, no provider or native mutation. Extended capacity is not accepted.
- **decision_memory.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. In-memory role/project library; not durable audit and not public API. Product audit remains Gateway SQLite.
- **dev_agent.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Local technical draft only; no shell/file/operator tools. Input package scope and size bounded by Supervisor.
- **e2e_demo.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Legacy cross-actor mock demonstration; excluded from runtime. Direct executor now denied. Replaced as acceptance by actual authenticated queue/native clone UAT.
- **intent_evals.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Golden evaluation harness; not runtime intent enforcement, not throughput proof; excluded from image.
- **knowledge_classifier.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Fixed project in source hash; positive numeric Native project IDs supported, but classification is never authorization. Product fetches native content itself.
- **knowledge_ingestion.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Fixed false success, scoped dedup/update, metadata revision and chunk bounds; persistent chunks transact with document.
- **knowledge_retrieval.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Role/project library context formatter; product does not expose it directly because it lacks fresh Native user ACL.
- **knowledge_search.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Real SQLite FTS5 MATCH prefilter with project/role; query normalization, limits. Product adds actor metadata and native checks before disclosure.
- **knowledge_storage.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. SQLite WAL runtime; pgvector unavailable; chunks/FTS/revisions transactional, fresh reads and empty isolated restore. No public PostgreSQL writes.
- **knowledge_ui_answer.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Local snippet formatter library, not authoritative semantic verification. Product uses scoped Native citation API/UI.
- **local_operator.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Fixed private stdin protocol, not MCP/HTTP; enrollment fresh Native role and maintenance checks. Not granted to specialists.
- **local_queries.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Exact read-only intents; mixed instructions stay bounded assistant path, receipts revalidate source/actor. Existing behavior retained.
- **n8n_indexing_hook.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Prototype raw-content webhook with wrong non-existent endpoint, excluded/not activated. Default key removed, buffer bounded/redacted, export inactive. Production uses signed fixed automation, no new public ingestion webhook.
- **planner.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Bounded sequential specialist/reviewer/aggregation DAG. Library model estimate was aspirational; actual local Supervisor budget is explicitly zero.
- **pm_agent.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Local risks/workload evidence; fixed Bangkok date and inject current config users instead of historical hardcoded5 IDs in product path.
- **proposal_aggregation.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Superseded duplicate proposal/executor prototype excluded. Executor closed because supplied PM string/ID and raw PATCH bypassed canonical confirmation, ownership and native gates.
- **proposal_ux.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Prototype formatter excluded. Removed false safe-to-execute/evidence flags; no authority from a role string or boolean.
- **qa_agent.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Local draft tests/triage only; NOT_RUN without runner evidence. Arbitrary attestation objects are not accepted from product request.
- **qa_change_workflow.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED_WITH_LIMITATIONS. Advisory in-process library, event fingerprint/cache not durable workflow receipt; not external event ingress. Notification objects do not send messages.
- **quota_panel.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Rewritten with validated provider project and reservation ledger, separate60s/day, unknown total tokens/billing/actor API count. No guessed model or20-user share.
- **reviewer_agent.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Checks references against bounded authorized native snapshot. Fixed FAILED propagation, ordinal reference confusion and explicit draft/semantic-review limits; scope checks actor/project/task/trace.
- **role_alerts.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED_WITH_LIMITATIONS. Advisory heuristics over authorized packages. In-memory dedup only; no sender/scheduler and no delivery acceptance claim.
- **scheduler_registry.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Declaration/simulation, not actual OpenProject cron or n8n inventory. Excluded; installed n8n ownership remains separate existing contracts.
- **service.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Fresh native identity before every command/CC/worker/poll. Wired local Supervisor and scoped knowledge actions, same canonical write preview/confirm. Fixed analyze query args accidentally passed to CC.
- **sprint_readiness.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED_WITH_LIMITATIONS. Advisory text heuristics (AC/test markers), not native transition gate; optional DecisionMemory remains library only. Existing native gates remain authoritative.
- **sprint_report.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Deterministic snapshot/advisory over freshly authorized Native packages; status-based heuristic and current workload, not actual Sprint velocity/performance rating.
- **store.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Existing WAL queue, leases/idempotency/actor scope retained; local-only claims bypass provider blocks, durable contract result and cooperative cancel, no schema migration added.
- **supervisor.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Source now used by real private worker. Scope/TTL/reference/version checks, bounded10-item context and output, ordered dependencies, aggregation and failed review, progress/audit. Local drafts, zero model calls.
- **supervisor_isolation.py** — DEVELOPMENT_ONLY_EXCLUDED; REVIEWED. Simulation harness, not a production dispatcher or20-user benchmark; excluded from image. Actual store isolation covered by application contract/UAT.
- **tasks_progress.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Historical checklist only; removed host-specificD path/raw parser exceptions. UI no longer treats oldDONE percentage as runtime acceptance.
- **weekly_report.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED_WITH_LIMITATIONS. Advisory CLOSED+updatedAt proxy is not historical closing timestamp; optional direct AI helper is not routed/qualified. Deterministic product report only; no LLM calls from analyze.
- **workflow_pause.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. In-memory advisory pause, not provider durable circuit. Exponent capped/raw details removed; actual durable circuit remains Store/Gemini.
- **workflow_timeline.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Fixed real workflow_id/observed_at/error_code mapping, bounded task timeline, no raw store errors or fabricated current timestamps.
- **workload_detector.py** — REQUIRED_RUNTIME_OR_INTERNAL_LIBRARY; REVIEWED. Authorized package-count advice, not capacity/productivity measure and no automatic reassignment. No write/sender exposed.

Historical diagnostic:511tests initially had7failures/15errors, resolved in later frozen regression. Failures from obsolete unsafe demo expectations are not acceptance proof. Actual Native clone/Playwright qualification is complete; see final reports. No serving deploy, accounts/TOTP change, Main or public tunnel restart.


## Final review and acceptance
520Windows/30Linux/64actualbrowser PASS;42source drift decisions and candidate parity verified. Native invalidstatus500→422,nullassignee/WAL close/FTS/metadata update/ACL,actor-bound Supervisor queue and operator fence fixed. Remaining limits and exact images are in FINAL_DEVELOPMENT_STATUS.md. Serving images unchanged. Legacy assertion changes cover retired unsafe helpers, policy-derived quota and truthful reviewer caveat; native no-write/role/ref/version assertions retained. SourceDiff/hashes and private before ZIP preserve the Gemini additions.

Baseline comparison:349recorded files;50baselined files differ,76current files were not captured in the original baseline and are not attributed as new edits.425current source/build/test files retained in private bundle.
