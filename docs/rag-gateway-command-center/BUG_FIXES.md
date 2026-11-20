# Proven bugs and changes

| Bug | Root fix / callers | Proof |
|---|---|---|
| Generic search excludes authorized registered files | service scoped file registry/pin/role pre/post, native_ids stays Native-only | integration-red→green; actual MAIN file search/answer/read |
| Answer always None | explicit search/answer/extract; Gemini structured quote selector+validation | answer-red/green; MAIN rendered supported quotes |
| Dense candidate starvation / file passage overwritten | bounded oversample, balanced file pool, dedup, preserve best chunk, batch exact chunk proofs | starvation-red/candidate-starvation; relevant regression |
| Dense cutoff too high | .65→.45 calibrated8cases; holdout separate | baseline8/36→final25/36, not perfect |
| Long exact source reference lost in common words | scoped generic literal reference priority and bypass lexical coverage filter | literal-anchor-red/green42tests; first MAINABSTAIN→same WebSUPPORTED |
| Old answer visible/new query late overwrites | abort + generation guard + clear at start/finally guard | actual inline JS RED→GREEN; no mutation replay change |
| Cold valid search exceeds20s UI timeout | knowledge110s aligns existingRails100s; controls15s unchanged | actual cold MAIN23.42s; JSdeadline regression |
| Search outage mislabelled no evidence/read unknownwrite | typed search status, read/write lock separation | outage-red; offline HTTP/JS contracts |
| Pinned-file read503/network also locks as unknown write | same bounded read-only transport, retains source citations and unrelated pending/unknown mutation locks | file-read-outage-red→green; actual final MAIN file-only extract/read |
| Knowledge mobile controls overflow | scoped wrap/min-width0/flexbasis | actualCSS red545>358→green358; MAINvisible284/284 |
| Retrieved instructions could request a write | pre-scan completebatch, schema+executor read-only RAG turn | injection RED writefirst→GREEN; no old MAIN bypass claim |
| Telegram model omits technical citation | append bounded validated server filechecksum / Nativeversion references | citation RED→67testsGREEN; final Owner41→42 fresh source/footer PASS |
| Repeated document question answered from memory without fresh tool | deterministic pre-model retrieval for explicit document/knowledge intent; empty fresh source abstains without model; same read-only gate/caps | actual39→40 failure; fresh-source RED2fail→67suiteGREEN; final41→42 livePASS |
| Empty-source outage mistaken for no evidence in Bot prefetch | retain SEARCH_UNAVAILABLE versus NO_EVIDENCE, never answer from memory or call model when source absent | telegram-empty-outage-red on prior image;67testsGREEN on finalimage; positive live path unchanged |

11product files changed across existing modules, no new dependency. Server citations distinguish retrieved sources from acceptance proof. Existing DONE guard, confirmation/idempotency and completion gates remain. No historicTask execution replay.

Harness failures retained/declared: initial unittest import aliases; missing hostPlaywright (used installed .venv); mobile new_page(viewport) wrong API corrected then inlineform clientWidth0 corrected to visible bar; MCP nested arguments/isError corrected. No product success inferred from these initial harness outputs. Existing release operator adds blank lines when rewriting .env; exact pre-release backup proves nonempty config lines unchanged except authorizedAI_IMAGE. No cosmetic rewrite of user config.
