# Readable span capacity comparison — 04/11/2026

Both diagnostics are rejected for qualification. Same six observed DEV questions, exact same authorized frozen spans, eight/source maximum and no gold quote inserted. The model is the only changed inference setting; no heldout query/label access, production retrieval change or new model download.

| Model | Positive support selected | Negative outputs | Warm request range | Total diagnostic |
|---|---:|---:|---|---|
| Qwen3 1.7B | 1/4 | 1/2 | 0.570–0.782s | 8.805s |
| Qwen3 4B | 2/4 | 0/2 | 2.601–4.862s | 36.968s |

These are correlated pilot counts, not representative Hit@5/FPR, not full bilingual answer scores, and not end-to-end latency: cached embedding/retrieval/span ranking is excluded. Cold first request1.7B=5.409s and4B=19.129s includes model loading; actual timings/load metadata remain in result JSON. Hardware headroom was checked, but no hard memory limit was imposed, so neither run is resource/deployment qualification.

Root inspected two selected evidence sets after execution: 1.7B pagination-VI returned CSV/filter text from WP391 with no page_size evidence; that is an unsupported match. 4B create/list-EN selected only unit-name spans, lacking explicit SQLite/create/list support despite the correct document. For create/list-VI, 4B additionally selected four unrelated documents alongside WP380. Exact quote/hash existence is insufficient answerability. Root review is not independent human adjudication.

The frozen plan permits a full observed-DEV run only after the pilot has correct supported selections and abstention. Both pilots failed, so no full-DEV/holdout/model tuning or deployment follows from these results. RAG remains OPEN; the shorter representation and bigger existing local model did not solve bilingual support/negation selection. Future work must improve evidence grouping/answerability before another independent evaluation. Preserve the three Owner-approved WP392 intents as fixture labels, not a replacement benchmark.
