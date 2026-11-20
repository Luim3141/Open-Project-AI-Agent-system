# Semantic RAG Phase 2 — frozen experimental gates

Recorded before candidate experiments: 2026-11-02T03:40Z. No Main mutation is authorized within this worker scope.

Baseline: exact current `KnowledgeSearchEngine`, cosine floor 0.65. Candidate must change representation/ranking rather than merely lower this floor. Dev documents: PM20/Project6 native 383,384,386. Holdout documents: 380,381,382; 379 may be partially relevant and will be labeled explicitly. Historic provisional holdout is diagnostic data, not an unseen acceptance set. Fresh intent groups/queries will be frozen before dev tuning; do not use holdout outcomes to revise candidate.

Paired evaluation on the same snapshot/model/scoped retrieval transport. Target at least 40 positive and 40 absent-feature negative queries overall, at least 20 each in holdout, VN/EN plus mixed language, exact lookup, paraphrase, long questions, ambiguity. Labels are source-grounded agent judgments; independent human adjudication remains pending. Relevant, partially relevant, irrelevant and absent are separate. Relevance must cite supporting chunks/content hashes. Results are experimental until human review.

Acceptance gates inherited from stabilization-rag/ACCEPTANCE_PLAN.md: holdout Hit@5 improves >=10 percentage points, Hit@1/MRR do not decrease; each language Hit@5 does not decrease; negative returned-result rate <=5% and no increase from paired baseline; exact top1 non-regression; citation mapping and ACL violations zero. Report Recall@5, abstention, p50/p95 latency, confidence limitations, stale/deleted/new index checks. Query p95 <=5s is a laptop operational target, excluding cold model startup/reindex. Do not change gates after viewing holdout.

Known gaps: only seven historical PM20 documents; document overlap/comments may confound scope; this cannot prove production-wide relevance. SQLite/Qdrant integrity tests and native boundary tests remain distinct from semantic accuracy. Exact snapshot hashes, source SHA256, Git HEAD, image identity, UTC time, command/environment and live/clone labels are required for evidence.
