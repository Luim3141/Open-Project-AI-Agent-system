# Dependency impact — C2a Native open counts

Exact count intent → `local_queries.match_query` → shared `execute_query` → own Native project endpoint with `status:o` and actual type filter → authoritative `total` → redacted durable read receipt. `Service.start_run` and `Service.perform(get_ai_run)` both use the helper; fresh authorization/readback precedes receipt reuse. The private route is not a new public Command/catalog contract.

Old unfinished-count receipts remain in SQLite but public readback returns stale. Task/Epic/Subtask scopes are distinct; Bug uses the existing exact approved Task[Bug] mapping. No Core, n8n, role, Native mutation, provider, schema or quota change. Two deployed Gateway modules changed; test fixtures now model Native type/project/closure fields. Existing Task-query assertion is strengthened to require Task scope and a Task label; count semantics are proved separately with mixed types and nonstandard closed/open status names.

C1 documentation corrections:17 referenced source/test paths in the Gemini dependency map are missing. Actual Native client is `gateway/native.py`, source phases are `gateway/native_phase.py`, vectors use `gateway/vector_client.py`, and current collection is `qldapm_knowledge_dense`. Seven host-only helper modules are absent from the production image and are not promoted by this patch.

Remaining dependencies: live Supervisor context selection must align RAG citations with at most10 selected fresh Native items; local summary must distinguish selected versus project totals. WF03 exposes start/plan plus durable polling; a final callback is not currently implemented by that workflow. Full application-QA producer and Native lifecycle are separate unfinished work.


C4a deployed impact: CoreGatePolicy + server qldapm_snapshot only. GatesAPI/UI/native mutation guards consume the server marker; caller gate-data cannot select it. Legacy logical policy remains unchanged. No Gateway/QA375producer bytes, DBschema, model/quota or workflowdefinitions changed.20Corefixtures and actualNativeclone qualified; Main73/48/13and preservation passed. RollbackCore46bf retains DB/history andGatewaye9. Next application QA proof needs explicit producer/import, currentsource/build binding and existing independent review; it is not provided by Native4compatibility alone.
