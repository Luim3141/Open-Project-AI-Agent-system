# End-to-end evidence by level

| Scenario | Observed | Verdict / boundary |
|---|---|---|
| Web→Rails→Gateway→RAG→Gemini→citations | Actual authenticated query, two correct quotes, source pin readback | PASS one positive; browser-uat.json + provider receipt |
| Telegram→Commander→tool→Gatewayextract→Commander | FinalOwner41→42, fresh RAG before model,1exact3.5litecall, full sourcepin footer | PASS content/tool/citation for this repeated document question |
| Negative no-answer model selection | Mars first503 preserved; after availability changed final actualmodelABSTAIN | PASS one semantic negative, not40answerqualityPASS |
| Search/extract/default/invalid/wrongscope | MAINread200 and semanticassertions; invalidmode/limit/nativeids422; P5nofile6 | PASS tested scope |
| Gateway read adapters/global/checkpoint | 22tools actual data,9semantic assertions; pending398 not397;27revision=11steps | PASS tested window, no assertion all projects unlimited |
| Local MCP/REST parity | initialize/list/identityactor18P6 + auth401 | PASS actual read, not JiraMCP |
| Command Center→Studio/report/inspector | 15UIgroups; real3nodes/artifacts/Back/reload/raw/export | PASS exercised; remaining controls PARTIAL |
| Modes/run/resume/approval/confirmation | Isolated auth/idempotency/fencing contracts | PASS CONTRACT; MAIN BLOCKED BY AUTHORIZATION |
| GitHub PR15 | Fresh read OPEN/unmerged/no checks | PASS read; no merge/sync/deploy mutation |
| Notifications/n8n | Existing17workflow fingerprints/outbox unchanged | PRESERVED; no fresh notification lifecycle E2E |
| Provider/network error recovery | Actual503→ABSTAIN_PROVIDER then later newqueryABSTAIN; UI429→200; offline typederror contracts | PASS bounded observed recovery; no outage campaign/model substitution |

MAIN browser: [network/correlation/UI results](browser-uat.json), [mobile](main-mobile.json). Backend [read packets](main-read.json), [adapter reads](main-integrations.json), [MCP](mcp-smoke.json), [Telegram full sanitized receipt](telegram-live-rag.json). Initial negative/assertion failure retained; do not replace503 with success label.

Telegram final answer correctly explains “This fixture does not certify semantic retrieval quality or Owner acceptance”, and includes file:project6-integration-qualification#sha256=c48bfa4826cdf746703c64aab06177146a7ed7ade1aa59d767554a3e40388901. BOT_REPLY_SENT42 replies input41, freshREAD_TOOL precedes one resolvedexact3.5lite generation. Current naturalUTC20770 budget2/20; historical20769 remains20. Prior37→38 and failing39→40 receipts retained separately. No proactive/fake inbound or task/control mutation sent.

Lượt41→42 chạy Botimage38b5579b821c. Finalimage828cfb8a73dc chỉ sửa nhãn empty/outage SEARCH_UNAVAILABLE ở nhánh không có source;67tests trên exactimage và source/runtimeparity đã kiểm. Positive retrieval/model/citation path không đổi, không inference lặp chỉ để thay timestamp image. FinalCorefileUI đã kiểm sau bản sửa read-only transport.
