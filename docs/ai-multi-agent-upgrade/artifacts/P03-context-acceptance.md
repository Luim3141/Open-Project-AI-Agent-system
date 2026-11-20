# P03-04 — actor/project/conversation context

Accepted staging `sha256:3e2a64d575eb111a282fc5f76d2f5580b3cee92eb58a3812943cfaee52031d80`. Optional context_task_id+conversation_id in start_ai_run resolve exact “Đọc task đó”/“Xem công việc đó” against an own stored AgentTask reference. Fresh native ACL and lockVersion, conversation binding and expiry checked on every follow-up and cached poll. Multiple/no references, missing IDs, changed/expired/revoked references fail closed. Context rejects write consent/scope/mixed instructions; no prior write is replayed. No context is sent to Gemini. Existing explicit-ID requests retain behavior. Reuses agent_tasks, adds no schema/queue/service.

Actual validation:

-5targeted context tests PASS;224full Windows regression PASS109.772s and exit0+finalOK checked before deploy; logs P03-context-targeted.log/P03-context-regression.log and exit receipt. Full suite includes API/catalog export synchronization. Initial fixture model-copy serialization warning was removed by constructing validated reference models; no production workaround.
-58Linux candidate tests PASS1.648s, no network/readonly root/non-root, P03-context-linux.log.
-Private cold clone with actual native GETs/5roles: two follow-ups each target fresh referenced work package; each role rejects inherited write consent; cross-actor/conversation, stale and expired refs denied.0SDK calls, no Gemini key in clone,10new read receipts only in clone, original471usage untouched. P03-context-clone.json; executable tests/container_agent_context.py. This is actual authenticated REST/native acceptance, not five physical browsers.
-Actual staging source parity service/store/app/catalog/models; cachedREADY, metadata tables still empty,79done/11failed receipts and471usage unchanged; config/credentials/keys byte-identical to private predeploy snapshot. P03-context-live-check.json.
-Runtime inventory and qualified comparison PASS: only Gateway image changed, all schemas/roles/counts/ledger/ports/mounts/private metadata preserved, all7stagehealthy/all4HTTP200. P03-context-after.json/P03-context-preservation-check.json.

Previous2e117f87 image and operator/p03-context-before-20261016 exact source/static exports retained; private pre-provision backup local-runtime/before-provision-1792139484268411600. OpenAPI/catalog sources and static exports updated together. No core/UI fork edit/main promotion/Desktop/CSDLDPT/billing change or new Google request.

Limit: context is an implemented backend contract used with stored task metadata. Automatic context creation/selection in Supervisor/UI comes in later tasks; no claim that the current native chat automatically remembers every prior message or interprets arbitrary follow-up writes.
