# Extractive reader — diagnostic result, 03/11/2026

**REJECTED; not deployed.** A multilingual SQuAD2 reader with an explicit null answer does not meet the existing quality gates. No thresholds were calibrated to remove the observed errors, and no held-out question/label file was opened or scored.

The hypothesis was that a reader trained for unanswerable questions could distinguish answer-bearing spans from the relevance-only DEV8 candidates. Public weights were downloaded at a pinned revision with publisher SHA-256 verification. All inference used the existing offline runtime in a networkless container, CPU1, memory limit 1,280 MiB. MAIN Qdrant, source data and provider configuration were not modified by this experiment.

Model: [onnx-community/xlm-roberta-base-finetuned-squad2-ONNX](https://huggingface.co/onnx-community/xlm-roberta-base-finetuned-squad2-ONNX/tree/00e1042302c6444d04fea71f5785a539b599ad73), revision `00e1042302c6444d04fea71f5785a539b599ad73`. Its [base-model publisher](https://huggingface.co/IProject-10/xlm-roberta-base-finetuned-squad2) declares MIT and multilingual QA. Those declarations are not evidence of QLDAPM accuracy. Only ONNX/tokenizer data was loaded; no downloaded Python code was executed.

## Measurements

Synthetic English/Vietnamese pairs gave null answers for all four no-answer cases and correct condition spans for two positives. Two duration cases extracted only `14`, while the strict expected span included the unit `days`/`ngày`: **6/8 strict checks**, retained as failures. A bare extracted span can omit context needed for a complete answer.

The tokenizer asset pads every pair to 384 tokens by default. Disabling that unnecessary padding reduced these short-pair times from 0.51–1.16 s to 0.032–0.065 s. Both original and unpadded observations are preserved in `qa-reader-synthetic.json` and `qa-reader-synthetic-unpadded.json`. This is a latency correction; it is not evidence of production latency or answer quality.

DEV diagnosis used the already observed 13 positive / 20 negative cases and frozen BGE/Qdrant candidate pool, followed by the previously computed DEV8 relevance scores. Selection was fixed at two nontruncated spans per retrieved document, at most five documents, before the run. A context-only extractive span was returned only when its joint start/end logit exceeded the CLS/null logit; default margin **0**, max answer length 64 tokens. Exact Unicode offsets, source text hashes and span hashes were checked against the scoped frozen SQLite/source copies before inference.

| Observed DEV result | Value |
|---|---:|
| Positive document Hit@5 after reader | 6/13 = 46.15% |
| Positive selected quote contains frozen supporting literal | 3/13 = 23.08% |
| Negative queries with a returned answer-bearing candidate | 4/20 = 20% |
| Warm p95, summed separate measurements | 2.807 s, **lower bound** |
| Reader pairs / container wall | 330 / 23.883 s |
| Reader cold load | 4.201 s |
| Peak cgroup memory | 830,402,560 bytes |
| Span/source identity errors in prepared inputs | 0 |

`qa-reader-dev.json` records all case outcomes without copying project passages or extracted answers to the public report. Sensitive project input/output stays in the private operator directory. The negative count concerns candidates that the reader would actually return, unlike the historical unthresholded candidate-generation counts; this is an output-level FPR proxy for the experimental extractive pipeline, **not** a deployed-user-answer measurement. Complete answer correctness has not been independently adjudicated.

The latency figure adds cached embedding/retrieval, prior span selection/reranking and reader inference; it excludes a unified API request, IPC and concurrency. Citation checks here verify identity/offsets against a historical snapshot. They do not qualify live ACL revocation, source freshness, deleted documents or local-file citation behavior.

## Failure and production boundary

The experiment disproves the hypothesis on the observed technical receipts/yes-no questions. A generic extractive QA null decision retains both false positives and substantial recall loss. Quoting an actual source, reaching a relevant document, and returning an answer to the question remain separate properties. The current technical blocker is answerability and supporting-span selection, in addition to the independent-label gap. A new threshold or a synthetic-only success is insufficient to clear it.

`gateway/knowledge_answer.py::retrieval_response(items, dense_state)` adds honest response metadata for the existing ACL/version-filtered search. It returns `UNVERIFIED_RETRIEVAL` or `NO_EVIDENCE`, an explanatory reason and `answer: null`. It does not activate this reader, replace the serving retrieval algorithm, or claim a complete RAG answer. The service owner wires it only after the existing final source-visibility/version checks. Three focused boundary tests verify that related evidence and injected source text do not become a verified answer.

## Review packet and holdout

`OWNER_REVIEW_PACKET_V2.json` is a concrete six-card draft from the newly captured controlled Project6 WP392, Native version **0**, including exact description excerpts, offsets and SHA-256. Version 0 is valid and is not treated as missing. The packet contains four positive / two scoped no-answer wording cases across only three correlated intents. It has **not** been scored or used for tuning. Its author is the implementation assistant; human/independent review is pending. It is not a new accepted dev benchmark or locked holdout and cannot validate 80%/5% quality.

The packet includes a separate-evaluator protocol for new development/holdout sets, intent-level splitting, private holdout lock, source/model/config/test freeze and one qualification run. An independent evaluator must author/adjudicate and lock that set outside implementation context; Owner factual review must not be falsely relabeled as prior human ground truth or as deployment approval. Existing holdout content stays untouched. No claim of document-unseen performance is justified for the historical sources already seen during development.

## Validation performed

`python -m unittest discover -s docs/ai/engineering/CHATGPT_RECOVERY/integration-final/rag -p test_*.py -v`: 23 PASS, including four decoder tests.

`python -m unittest openproject.ai.tests.test_knowledge_answer -v`: 3 PASS. New scripts compile. `prepare_owner_review_packet.py` asserts source identity/version, exact offsets, hashes and preservation of an existing packet.

No production deployment, paid provider, Gemini call, MAIN database mutation or Qdrant mutation was performed by this work. B1–B7 and overall RAG acceptance remain **NOT PASSED**. Heavy experiments stopped after the failed DEV diagnosis; no held-out qualification was attempted.
