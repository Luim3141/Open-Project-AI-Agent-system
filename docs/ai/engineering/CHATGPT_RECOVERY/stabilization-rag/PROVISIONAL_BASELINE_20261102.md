# Provisional semantic baseline — 2026-11-02

**Diagnostic only; independent review pending.** No retrieval policy was changed. The candidate labels and detailed results remain in the private operator directory `semantic-review-20261102`. Do not treat these results as acceptance or an independently adjudicated holdout.

A copied Project 6 snapshot contains 135 vector points and 7 PM/actor-20 scoped documents. The frozen candidate set contains 24 positive and 20 presumed-negative queries, balanced VN/EN. Each positive includes a proposed native ID, source hash, chunk index and chunk hash for review. The referenced first chunks contain the corresponding source title; that alone does not establish full relevance or exhaust alternative documents. Negative labels remain unconfirmed pending full-corpus review. All labels were created by the same agent, not a human reviewer.

The earlier diagnostic intents/sources were assigned to calibration; the new candidate intents target separate source work items. Parent documents and overlapping functionality can still be relevant to both: document-level independence and complete relevance labels are not established. Reviewers must assess alternatives, leakage and negative claims before this set can serve as an acceptance holdout. Baseline was measured before any candidate tuning. Paired VN/EN paraphrases share an intent and are kept in the same split; these are not independent samples.

Using local BGE-M3 `bge-m3:latest` digest `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`, current cosine threshold 0.65, existing `KnowledgeSearchEngine.search` and a fixture computing cosine over the copied vectors:

| Language | Positive | Hit@1 | Hit@5 | MRR@5 | Candidate negatives returning results |
|---|---:|---:|---:|---:|---:|
| VN | 12 | 3 | 3 | 0.250 | 0/10 |
| EN | 12 | 1 | 1 | 0.083 | 0/10 |
| Total | 24 | 4 | 4 | 0.167 | 0/20 |

Hit counts require the proposed native ID, and may undercount alternative relevant documents. Results for candidate negatives are not a validated false-positive rate. No confidence interval is meaningful for independent intent sampling with this small, paired, unadjudicated dataset. Fixture transport filters only project and does not exercise real Qdrant filters; search engine performs its existing SQLite scope and chunk integrity checks. This run does not establish native authorization, citation correctness, exact-match nonregression, outage behavior or ACL acceptance. Existing recovery/storage unittest suite: 26 passed separately.

Private label file SHA-256: `3f41c0ff743dc4fb9d3f5729d4772a7127b78c9d8a94a8514e8ff90a091fd8c7`. Snapshot hashes and per-query outcomes are in the private manifest/results. The dataset is ready for independent label review, not for tuning or production acceptance; after corrections, freeze a fresh holdout and avoid reuse if its answers influence candidate design.
