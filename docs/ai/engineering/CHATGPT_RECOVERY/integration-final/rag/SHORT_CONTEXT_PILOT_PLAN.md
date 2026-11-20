# Short readable evidence contexts — static decision, 03/11/2026

**No model calls made; not a qualified candidate.** `readable_spans.py` is an offline research module. Frozen production code, serving retrieval, earlier failed metrics and the old holdout were not changed.

## What differs from the failed Qwen experiment

`quote_candidate_dev.py` fed up to two dense raw chunks per document for five documents to Qwen3 1.7B, context 4096 and output allowance350. It achieved 8/13 positive Hit@5, 2/20 negative outputs, p95 7.281s and was rejected. It did not record enough input-level evidence to prove that JSON escapes caused the misses.

The proposed comparison feeds exact source-derived sentence/allowed-JSON-field spans rather than long raw chunks. Repeated readable text is removed **within a source only**; source identity/version is kept. Every readable character maps back to its exact original Unicode interval. JSON escapes can be decoded for comprehension, while a quoted answer resolves to the original raw substring and hashes. No text is summarized, translated, aliased, case-folded, or HTML-decoded. Negation and scalar keys/values stay intact. Source text remains untrusted data; this is not a secret scrubber or authorization boundary.

This is a real input-representation and evidence-pool change, but its benefit must be measured. The static evidence argues against normalization alone being the fix:

| Static frozen-source observation | Result |
|---|---:|
| Extracted spans | 226 |
| Spans changed by JSON decoding/whitespace | 8 |
| Raw → readable characters | 13,486 → 13,472 |
| Same-source duplicate readable spans | 28 |
| Fixed top3 distinct spans/document, max5documents | ≤15 spans; ≤2,909 chars/query |
| Frozen positive supporting literal retained by compact context | 10/13 |

These are retrospective coverage diagnostics on already observed DEV, not correctness/abstention measurements. The compact top3 policy loses required evidence before generation and cannot reach the target supported-answer coverage on this DEV. **Do not spend inference on top3 as a final candidate or tune a relevance threshold to conceal the lost cases.** The previously observed DEV8 pool contained supporting literals for13/13, but no answerability proof; a future comparison must preserve that wider evidence pool or fix selection first.

## Smallest useful next experiment, waiting for resource window

One diagnostic ablation can test whether a sufficiently complete short-span context improves Qwen's answerability over raw chunks. Freeze a **single** candidate before running: preserve all nontruncated, same-source-distinct spans from the existing DEV8 pool, at most8/source and5sources; full sentences only, hard total context cap6,000 characters. If any prepared query loses its supporting evidence due to the cap, report that coverage loss and stop qualification; never insert the gold support manually.

Use at most six **already observed development** cases for an initial pilot: two natural positive VN/EN, two explicit-negation/yes-no VN/EN, and two no-answer cases. Choose identities and record their manifest before model calls, without selecting on new output success. This is a diagnostic sample with known-label bias, not a benchmark. WP392 Owner-reviewed labels remain only three correlated fixture intents and must not become representative quality evidence.

Use one Qwen3 1.7B request per question, no per-passage generation and no second verifier call. Keep temperature0, seed42, `think:false`, max output128 tokens, context2048; allow model to select only enumerated span IDs or return an empty list. A returned quote must be an exact unambiguous substring of a selected readable span and must resolve to the unchanged authorized/version-checked raw source. The generated answer still requires semantic correctness review: exact quote existence alone is insufficient. Explicit missing evidence means abstain, never an invented negative fact. Cross-source contradictions must cause abstention unless the question explicitly asks about historical differences and evidence distinguishes versions.

Resource budget: existing local Ollama only, CPU1, one request at a time, bounded isolated model runner with hard memory limit **2 GiB** if the existing model can fit. No new model download or paid provider. Do not restart/reconfigure MAIN Ollama to impose this limit. A separate isolated runner is needed if MAIN cannot enforce it. Abort if bounded startup cannot fit, any warm query exceeds5s, output is truncated, or total pilot exceeds60s excluding a separately reported cold load. Report true request wall times and token counts, not sums of disconnected measurements. Stop until root declares the fresh Engineering E2E resource window green.

Only run the complete observed DEV if this pilot has valid exact citations, correct reviewed answers, explicit abstention and meets its resource budget. Even a successful full DEV would require separately authored/adjudicated new dev and privately locked holdout, source/model/config/test freeze, ACL/freshness/deletion and local-file evaluation before any RAG deployment. Do not reuse or tune on consumed holdouts.

## Checks already run

Six focused normalization tests PASS: escaped Unicode/newlines/surrogates, preservation of negation and scalar false, exact raw quote mapping, stale/hash/ambiguous quote rejection, no HTML/combining-mark alteration and no restoration of filtered secret fields. `readable_span_diagnostic.py` verifies the unchanged dev/source-manifest hashes and source snapshot hashes and makes no network/model call. Its result is `readable-span-diagnostic.json`.

The next model experiment remains **NOT RUN / RESOURCE WINDOW PENDING**. The actual answerability blocker and rejected reader metrics remain unchanged.

## Root continuation04/11 — frozen diagnostic route

`short-context-pilot-manifest.json` freezes six previously observed DEV cases: create/list VN/EN, explicit no-restoration VN/EN, no-answer pagination VN/EN. All four positive support literals survive the fixed DEV8/top8 distinct readable-span contexts (2,470–3,606chars). No gold support is inserted into requests. No heldout questions/labels are opened.

No isolated Ollama image is installed. Root uses the existing local GPU Ollama only for a diagnostic, after Engineering is OFF/idle and RAM≥1.5GiB/freeVRAM≥2GiB. RTX3050 observation had3,020MiB free VRAM. This replaces the proposed hard2GiB isolation route for this pilot only; there is no hard process-memory limit and it is not deployment qualification. Exact spans are selected by enumerated ID (64output tokens), assembled without generated quote text; the full source span remains hash/offset-bound. Warm query>5s, incomplete/truncated output or total warm>60s stops the pilot. `run_short_context_pilot.py` freezes model digest and request hashes before at most6local calls; no downloads, config changes or paid provider. Extractive span correctness is separate from a complete bilingual answer or representative benchmark.
