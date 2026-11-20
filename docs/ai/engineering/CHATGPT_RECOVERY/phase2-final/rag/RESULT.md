# Semantic RAG Phase 2 — FAILED ACCEPTANCE, safe citation fix retained

Continuation: local cross-encoder feasibility, pinned install and a fresh locked holdout were completed later. See `RERANKER_RESULT.md`: relevance improved but no-answer false positives still failed acceptance; no semantic candidate was deployed. This file preserves the earlier passage experiment and source state at its timestamps.

Snapshot experiment: 2026-11-02 03:36–03:48 UTC. Production source restored after rejecting semantic candidate. No Main deployment, native business write, paid provider call or Computer Use was performed by this worker.

## Delivered source change

`openproject/ai/gateway/knowledge_search.py`: dense citations now take `native_id` from the SQLite-authorized document metadata, rather than the unchecked Qdrant `work_package_id` alias. The old code accepted a payload alias of 999 despite verified metadata identifying WP12. `test_rag_recovery.py::test_dense_citation_uses_verified_native_identity_instead_of_unverified_alias` reproduced this failure before the one-line fix (`citation-red.log`); the focused suite then passed (`focused-green.log`). Real isolated Qdrant reproduced the boundary and verified the fix too.

Final search SHA256: `6dce36043c90d8ccdb55bd21b8ce0f92f46f0a48d16c3eaebad2a0d30cfcf69c`.

`knowledge_ingestion.py` was restored exactly: SHA256 `c4283da4f9db19f9b32c020113e825ad9586ced44f06a6a9b9d093bb4fab05f3`, equal to the directly inspected serving Gateway file at restoration time. The rejected supplement is preserved only as `rejected_candidate_knowledge_ingestion.py` (hash `68c0dbdada0b5a09fbab684585e60b9c857b7241878dcf9205b5a869a0c07c33`) and a separate experiment test; it is outside the build source. Cosine floor remains 0.65.

## Root-cause evidence

The complete read path was inspected: classifier/provenance → ingestion/chunks → BGE-M3 embed → Qdrant filters → SQLite FTS/BM25 → dense validation → RRF → service native visibility/version recheck. Ingestion embeds raw 600-character windows with 100-character overlap; comment JSON, artifact paths, hashes, receipts and unrelated PM/BA plans share windows with requirements. This dilutes semantic signals and creates competing, partly relevant sources. Several native documents contain generic or copied cross-topic plans, so document relevance cannot be established by title alone.

Stored versus regenerated first-chunk embeddings: 13 probes, cosine approximately 1.0; repeated calls were bit-identical in these probes. Model `bge-m3:latest`, digest `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`, F16, dimensions1024; vector norms approximately1. No observed model drift or normalization mismatch explains these cases. Private probe output: `semantic-review-20261102/phase2-consistency.json`; reproducible command: `.\openproject\ai\.venv\Scripts\python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/rag/diagnose.py`.

Dev example: English Unicode query cosine rose from0.637 with audit-mixed windows to0.680 for a complete source passage, without changing model or floor. However isolated short generic requirements such as “Update task status” also produced false positives for absent push/SMS capabilities. Passage extraction alone cannot establish answerability.

Historical benchmark fixture filtered only project before its chunk top-k; actual Qdrant filters role/actor/document scope before retrieval. The historical4/24 is a different provisional query set and transport, so it is not the paired baseline below. Real Qdrant was used for both arms below. No claim is made that the historical ranking instability was fully eliminated: three repeated clone queries ranked identically, and embeddings were stable, but broad tie/ANN/corpus drift investigation is still incomplete.

## Frozen evaluation and rejected candidate

`PLAN.md` fixed gates before candidate selection. Private labels were frozen at03:41:54UTC: SHA256 `c18c247c0a359efcea4b8d5115196aba1793ef4174539f0f803bdef5add588a3`. There are88 queries: dev24positive/20negative and holdout24positive/20negative; balanced VN/EN, including paraphrase, exact route/keyword, domain terms and long questions. Dev primary source IDs383/384/386; holdout primary sources380/381/382. WP379 and overlapping plans were labeled partial rather than relevant. All labels are agent judgments after reading source contents, with source/content hashes, and remain `HUMAN_REVIEW_PENDING`. Fresh wording uses previously known intent families; this is not an independently sampled/human-adjudicated holdout. Coverage of ambiguity and mixed-language is limited, and wrong-project/stale/deleted/new-source cases belong to the separate integration contract, not the accuracy denominator.

Input snapshot: seven PM/actor20 Project6 documents;135 historical total project points, with allowed point scope selected before indexing. SQLite SHA256 `f4837ce3db6ce3542acbac8b6b40195f78cf2df2879e32e4b747e28da45f5d8d`; vector snapshot SHA256 `867e7fe2ca2691617d25514047fedc4f4109efed0d674d8d92c8dd4c3b31f6cd`. Private raw labels/query vectors/results stay at `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/phase2-final-rag`.

Candidate retained original windows and appended literal lines/JSON string passages. Initial minimum20character variant was rejected on dev (7/20 negatives returned). A single development revision required minimum60characters to retain more context; its dev result was15/24 Hit@1 and Hit@5 versus11/24 baseline, negatives0/20 both. The candidate/source lock was written before holdout. Holdout was run once; candidate was not revised after its results were seen.

| Holdout metric | Paired baseline | Candidate |
|---|---:|---:|
| Hit@1 |8/24|8/24|
| Hit@5 / Recall@5 |8/24 (33.3%)|15/24 (62.5%)|
| MRR@5 |0.333|0.460|
| VN Hit@1 / Hit@5 |5/12 /5/12|6/12 /8/12|
| EN Hit@1 / Hit@5 |3/12 /3/12|2/12 /7/12|
| Absent-feature negatives returning anything |1/20 (5%)|2/20 (10%)|
| Correct abstentions |19/20|18/20|
| Returned source/native identity violations |0|0|
| Warm p95 query latency |0.340s|0.301s|

Hit@5 improved29.2percentage points, but negative return rate increased and exceeded the pre-fixed5% cap. Therefore **semantic acceptance FAILED**; EN top1 also regressed. No post-holdout threshold adjustment or candidate deployment was performed. These counts are small and paired by intent/language: they do not support an independent-sample statistical claim. Identity correctness is narrower than answer-support correctness: no generated answers or complete human citation adjudication were measured. Positive queries can return partially relevant/irrelevant results; Hit@K is not precision.

Commands (Windows host Python, real local Ollama, dedicated Qdrant port16334):

```powershell
.\openproject\ai\.venv\Scripts\python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/rag/benchmark_phase2.py prepare
.\openproject\ai\.venv\Scripts\python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/rag/benchmark_phase2.py dev
.\openproject\ai\.venv\Scripts\python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/rag/benchmark_phase2.py holdout
```

Exact timestamps/source hashes/model/command/environment are in `dev-summary.json` (03:44:02–03:44:30UTC) and `holdout-summary.json` (03:45:07–03:45:23UTC). Dev search source predates the independent citation one-line fix; holdout uses that fix, applied identically to both arms. Git HEAD was `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`, source uncommitted. Runtime Gateway image during experiment was698db791…; the benchmark did not test a new Gateway image. Benchmark code now explicitly loads the preserved rejected module for reproducibility, rather than the restored production ingestion.

## Actual Qdrant contracts

`integration-results.json`:16assertions PASS at03:48:07–03:48:09UTC, after restoration. Dedicated disposable Qdrant image `sha256:9bfc89f9914fc14876a88c05270685921a55b8877b254a98bcc1cc2f0a424cd2`, host-bound port16334; it never used the Main Qdrant URL. Synthetic Project6 contract corpus: new index/read, wrong project/role/actor/empty document scope, actual Qdrant prefilters for each scope, revision pruning in SQLite and Qdrant, forged alias/metadata/chunk rejection, restart readback, deletion propagation, three identical repeated query rankings. This is not live Native authorization/end-user citation rendering. Fixture service tests separately cover native visibility and lock-version refresh.

Provenance record/log: `../checks/rag-actual-qdrant-contracts-20261102T034804692372Z.json` and `.log`; `source_changed_during_check=false`. Exact command:

```powershell
$env:PYTHONPATH='openproject/ai'
.\openproject\ai\.venv\Scripts\python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/record_check.py --name rag-actual-qdrant-contracts --environment 'Isolated Qdrant 16334; host Python3.14; real local Ollama; synthetic contracts; no Main mutation' --image sha256:9bfc89f9914fc14876a88c05270685921a55b8877b254a98bcc1cc2f0a424cd2 -- .\openproject\ai\.venv\Scripts\python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/rag/integration_checks.py
```

## Installed reranker feasibility

Read-only inventory on host project venv and serving Gateway: `torch`, `transformers`, `sentence_transformers`, `FlagEmbedding`, `onnxruntime` all absent. Host HuggingFace hub has no cached model directories. Ollama manifest inventory and `/api/tags` contain only BGE-M3 embedding model; no installed cross-encoder/reranker was discovered in these scoped locations. A local cross-encoder could be a separate future experiment, but cannot be tested from the installed assets without new runtime/model installation. No download, dependency install, paid service, provider generation or holdout retuning was attempted.

## Required shared documentation updates / remaining work

Root should record: citation source fix only is eligible for build/release; semantic representation change rejected and restored; M2 remains FAILED/PARTIAL. `architecture.md` must state authoritative SQLite-native citation identity and retain current600/100 chunking/0.65 policy. Do not claim safe semantic recovery or Owner acceptance.

Next useful independent investigation needs a new source-grounded development/holdout corpus with adjudicated relevance and answerability, and a verifier/reranker that can distinguish task CRUD from absent related capabilities. The consumed holdout must not be reused to select a replacement candidate. No Main reindex was performed, so production semantic recall remains unresolved.
