# End-to-end results

Evidence levels: SOURCE; ISOLATED CONTRACT; MAIN READ; HISTORICAL REAL EXECUTION; ACTUAL OWNER LIVE; NEW MAIN MUTATION (không thực hiện). Mỗi PASS giới hạn trong flow thực sự quan sát.

| Flow | Kết quả | Bằng chứng / ranh giới |
|---|---|---|
| A Telegram→Gemini SDK→functioncall→Gateway→Native/Observer→feedback→reply | PASS các lượt Owner thực tế; PARTIAL toàn bộ catalog NL | telegram-live-four-turns.json lưu lỗi ban đầu; postfix32/34 đúng acceptance/count; global35→36 READ_TOOL get_active_agents project6 correlationc9b94dff-c0e2-4009-92eb-98c0fbe5b010, actual resolved3.5lite, no loop. Final DTO-only change có adapter13checks/62contracts, chưa thêm model call |
| B Telegram authorized control/create/update/resume | BLOCKED BY AUTHORIZATION trên MAIN; isolated contracts PASS | 7write declarations strictschema/confirmation/auth/version/idempotency. Không autoapprove/runOnce/AUTO/createUnit để kiếm evidence; không suy live control PASS |
| C BA/PM→Dev→Reviewer→QA→READY | HISTORICAL REAL EXECUTION verified; không newrun | Nov6 plan76f13288→Task398runde391b2f, Dev12/Reviewer1/QA5provider calls,64JUnit/0fail, only tests/test_health_regression.py. Current Nativev10 READY FOR RELEASE/AWAITING_OWNER_APPROVAL. Existing18coding receipts requested3.5lite nhưng historical resolved version không lưu; BA/PM2actualresolved đúng. Demo evidence docs/agent-studio-v2-stabilization/demo-final.json + demo-tests.json |
| D CommandCenter→AgentStudio→Native/artifacts/GitHub | PASS observed MAIN terminal UI; PARTIAL all branches | browser-uat.json14groups/JSerrors0;6roles,3stage nodes, Devfile/PR15,393empty,Back/reload398. Actual RUNNING screenshots làNov6; không gán currentOFF thành running. RAG finalPASS nhưng một lượt trước không results/rootcauseunknown |
| E acceptance→outbox→n8n→Telegram→Reply context | HISTORICAL OWNER LIVE PASS; no fresh proactive send | 397approved→completedmsg16; Owner19Reply16 read397 despite conversation391→reply20 (../telegram-observer/live-reply-397.json). Durable current7SENT allattempt1;398PR21/await22, no398completed. Notification retry/offline/idempotency isolated, không mô phỏng bằng live send mới |

Additional actual integrations: GitHubPR15OPEN/head7cea +17/-0 inonefile; noCI/humanreviewcheckpassed claims. n8n17active workflow contracts/history; không phải17freshE2Epasses. RAG known398/384/390 + negative query/citations/currentNativeACL/version lexical retrieval; answerability gate chưa đạt, không generate answer để bỏ gate.

Controlled bot/Core+Gateway restarts: config hashes/volumes/data giữ nguyên; conversation/pairing/outbox persist, no new agent_runs/tasks/checkpoints, workerOFF/active0; integration-final/mainread evidence khác fixture.

Bổ sung MAIN: additional-reads.json ghi4read paths project options/report/agent run/trace; studio-recovery-probe.json ghi Explorer19Task với list+graphHTTP200. Screenshot Studio sau burst có Explorer429 và không được tính là ExplorerPASS; fresh probe không gặp lỗi nên không claim đã thử manualRetry live ở lượt này.
