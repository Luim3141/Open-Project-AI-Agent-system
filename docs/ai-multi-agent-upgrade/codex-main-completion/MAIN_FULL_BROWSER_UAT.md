# Main authenticated browser UAT — 21/10/2026

Status: **PARTIAL_PASS**, not final owner acceptance. This adds current evidence; earlier clone qualification remains distinct.

Owner completed Native login/TOTP in Edge and confirmed “đã đăng nhập”. Codex used that existing session through CUA/Playwright browser locators. No password, TOTP seed, cookie or session token was extracted or fabricated. Actual Main actor is PM19 (ba-pm), project5.

| Test | Result | Actual evidence |
|---|---|---|
| Assistant GET and dashboard | PASS | Gateway ok, OpenProject authenticated, native mode,329 readable Work Packages; legitimate empty Daily Brief; registry and saved quota policy visible |
| Native identity POST | PASS | `main-identity-post-verified.txt/png`; response received from OpenProject; dashboard and Control Center remain present after POST; original disappearing-context defect not reproduced |
| Supervisor local readonly | PASS | Exactly one submission; run `87803ca8-72a1-4643-b00f-8fda05a06266`, trace `45f86df7-745e-48dd-abc0-ea6fbee36681`; native actor19/project5; COMPLETED; PM then Reviewer; result visible in Assistant |
| Execution Detail | PASS |4graph nodes including synthesis;3agents;2plan steps;14events; native source references38–47; LOCAL_DETERMINISTIC;0calls/0observed tokens |
| Agent Detail | PASS keyboard and mouse | Enter and mouse on PM node selected PM and displayed its saved output. Mouse selection revalidates Native ACL asynchronously; initial immediate snapshot was too early. Follow-up `main-monitor-detail.txt/png` confirms PM selected |
| Presentation Mode | PASS | Button changed to “Thoát trình chiếu”, exit restored normal controls |
| Replay | PASS | Readonly replay changed14/14 to2/14 with “Tạm dừng phát lại”; returned to final result; no enqueue or generation |
| History, search, status, sort | PASS within one-record dataset | Search UAT Main2026-10-21 +COMPLETED +oldest:1actual execution; `main-execution-history-filtered.txt/png` |
| BA/BE/FE/QA native Main UI login | NOT_RUN | Native API identity all5roles passed deployment;24browser checks for other4roles were isolated clone evidence, not Main UI logins |
| Main graph drag/auto-layout | PASS | `main-monitor-interaction-uat.json`, `main-monitor-drag.png`, `main-monitor-auto-layout.png`; PM transform changed370,125→431.65,7.30 and AutoLayout restored370,125; browser layout only |
| Main four exact mobile/desktop viewports | NOT_RUN | Prior clone Monitor viewport checks remain separate; actual Main Owner browser viewport differs |
| Live Gemini fixed-text connectivity | PASS after separate approval | `main-minimal-smoke-result.json`; exactly1countTokens+1generateContent, QLDAPM_OK,18input+6outputtokens; Main local reservations2, fresh readinessREADY. Not a full Gemini multi-agent execution |
| Main business write/proposal approval | NOT_RUN | No existing Main WP modified for a test; clone tests only |

Read-only runtime evidence `runtime-20261021-023929.json`: Main now1ai_run/1agent_run/14execution_events;0proposals/0Gemini usage/0provider receipts. Staging remains113AIruns/23agentruns/44receipts. This Main record is a new actual local run, not an imported Stage record or Gemini output.

Known limit: local analysis explicitly samples10/329items; a low-risk summary over this sample is not full-project acceptance, capacity verification, or completion evidence. No schedule/status conclusion was applied to business data.

Subsequent approved smoke changed only Main local provider usage/readiness; `main-control-center-post-smoke.txt/png` showsREADY and2dailyreservations. The zero-usage readback above records the earlier local-only phase.

Additional Main Owner UI after reauthentication (the preceding session expired after60minutes): Ganttquery32 loads329rows/page500,11collapsedEpics and expands Epic38→Task49→Subtask102 correctly. Four Boards10..13 render7/6/5/4columns;329KanbanNEW cards, Workload53/117/53/53/53/0. Epicboard12 is five configured roots38..42; Roadmap is empty because no WPVersion was assigned. `main-gantt-and-boards-browser-uat.json`, `main-gantt-*.png/txt`, `main-board-10-ui.*` through13.

Main readonly Backlog, NativeSprintlist, Insights and WorkflowGates pages rendered. S1..S5 remainplanning/undated with60/66/54/90/48WP. Insights reports insufficient evidence rather than ratings. SecondBrain searchAUTH-01 returned0results (`main-second-brain-search-ui.*`): only empty-state searchPASS, not Mainingestion/citationPASS. No Maindata was indexed or altered. CloneSecondBrain subsequently16realUIchecksPASS, including5rolelogin/TOTP, per-actor indices and nativecitations; see `second-brain-clone-ui-uat.json`. Cloneevidence is not Mainbusiness UAT.

ActualMainserviceHMAC/Native25checks confirmed newrun actorisolation and viewaccess (`main-native-views-security-readback.json`). Native scheduling dry-run onclonePASS329dates/343follows (`schedule-native-fork-clone-dryrun.json`), but deadline/capacity and bulkSprint/Version remainunapproved/unqualified. FullGeminiSupervisor has separate preview and pendingOwnerapproval; no moreGooglecalls. Mainn8n has noautomation.key and0briefs; Stageautomation remainsuntouched. Keep Main/Staging independent.
