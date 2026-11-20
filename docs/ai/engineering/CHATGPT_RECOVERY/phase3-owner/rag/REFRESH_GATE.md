# Project6 Native cache refresh — operational clone gate

Predeclared before running the qualifier. This is an operational freshness test, **not** semantic model acceptance or a fresh semantic benchmark. No semantic candidate is selected: the historical chunk-monopolization hypothesis was contradicted by all 14 consumed Native misses having best relevant cosine below 0.65 at chunk ranks 1–8.

Input: new immutable, authenticated Native18/20 Project6 snapshot (10 existing WPs379/380/381/382/383/384/386/387/389/390) and scoped SQLite/Qdrant read copy. Baseline observation09:21UTC:9/10 actor20 documents stale after comments changed, despite matching lockVersions. Frozen Native payloads/activities stay private. Human semantic labels remain pending; Phase2 file-clause holdout stays unconsumed.

One bounded operational run, no score/threshold/model tuning, downloads, provider calls, Native writes, Main index/config mutation or browser automation. Disposable Qdrant uses existing immutable image, internal Docker network, loopback16335, CPU1 and memory256MiB. BGE-M3 uses existing local Ollama, batch1, num_thread1; no newly loaded model. Actual model/GPU RAM is reported separately from Qdrant cap.

Required gates:

- Seed current frozen old index and vectors, observe stale exact384/390 lookups empty.
- Scanner on cloned SQLite detects exactly9 changed WP sources; every refresh key is `native-event-6-...`, actor20, and Native business write count0.
- Drain at most12 Project6-only jobs; all9 reach `verified`; no Project5 row or business proposal exists.
- Actor20 snapshot hash/metadata matches all10 frozen current Native sources, with verified registered Qdrant payloads/chunks.
- Exact scoped384 `healthz` and390 `GET /tasks/{task_id}/title` return their correct current WP/citation to PM20 and Owner18.
- Actual Qdrant denies wrong project, wrong role, wrong actor and empty document scope; forged native aliases remain covered by44 targeted source tests.
- Warm exact-query p95<=5seconds, Qdrant OOM=false and RSS<=256MiB. This is a local sequential clone observation, not a production/concurrent SLA.

Stop on a failed gate; no acceptance relabeling or repeated calibration. If operational gates pass, root may review deployment plus a separate Project6-only scanner/drain. This does not fix the historical cosine/answerability gap or prove Owner UAT.
