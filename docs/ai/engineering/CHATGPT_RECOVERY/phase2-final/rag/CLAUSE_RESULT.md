# Repo-file evidence clauses — STOPPED AT DEV QUALITY GATE

**Kết quả: không có candidate đủ chất lượng để triển khai.** Final bounded dev pass vẫn chỉ tìm đúng literal supporting evidence7/28positive (25%), dưới gate2/3 đã chốt trước thử nghiệm. Không hạ gate. **Holdout30positive/20negative chưa được query retrieval, embed query hoặc rerank/scoring.** Không sửa source/config/index MAIN, không tạo Work Package, không tải model/package mới. Dừng experiment theo chỉ đạo root; không tiếp tục tuning.

## Scope và nguồn thực

`CLAUSE_PLAN.md` và `clause-source-manifest.json` khóa12file thực theo allowlist root phê duyệt. Manifest frozen `2026-11-02T07:38:30.244699Z`, SHA256 `3cd0fc63cbdb07f18d32f6c2f2f69ce0d74d118feefbc61dfee1a4be15ced8c5`. Raw source copies bất biến nằm private; mỗi file có path, raw/content SHA256, classification, project6/PM/actor20scope.10Markdown files trong workspace không Git-tracked và được ghi rõ **content-addressed revision, không giả là Git commit**. Demo README/API lấy trực tiếp bằng `git show` từ PR9commit `4a794e2b3d62247881fef4c0908eeeee9f043ba2`; không đọc nhầm demo worktree HEAD cũ.

Nguồn: local-file contract; ADR0001–0004; historical2026-10-22ingestion/retrieval reports; domain/issue-tracker/triage docs; PR9README và `task_manager/app.py`. Những khẳng định lịch sử/proposed/implemented-at-commit được phân loại riêng; không dùng chúng làm proof hiện trạng MAIN hoặc feature đã deploy. Bounded regex screen không phát hiện secret/email trong12file; không phải chứng nhận mọi dạng thông tin nhạy cảm. Không copy private config,credential,enrollment hoặc database.

Nhãn frozen `2026-11-02T07:42:48.161181Z`, SHA256 `c2f00a47f3e103ab9690f458f410b20b9298f93d849b67f801cc48728df4f542`: dev28positive/20hardnegative; holdout30positive/20hardnegative, balancedVI/EN. Split theo6dev/6holdout document groups, không reuse Native heldout intents/sources làm acceptance mới. Mỗi positive gắn literal supporting span/offset/hash trước scoring. Cùng agent tạo nhãn sau đọc source, `HUMAN_REVIEW_PENDING`; semantic equivalent alternatives chưa independent-adjudicate. Kết quả chỉ áp dụng **repo-file corpus**, không chứng minh đã sửa Native RAG.

## Pipeline thực đã thử

Baseline dùng production `KnowledgeSearchEngine` trên SQLite/vector fixture riêng với cosine0.65, chunk600/100. Candidate lọc scope/revision trước retrieval, recall tối đa6documents bằng dense+lexicalRRF, chọn2literal clauses/document, ONNX rerank tối đa12passages/query. Corpus có **165literal clauses +87original windows =252vectors**. Markdown spans/AST Python route function+decorator giữ original offsets/hashes; title chỉ nằm ở document retrieval, không prepend vào supporting evidence. Không viết lại/translate nguồn. Metadata/role/project/actor/source revision không do model quyết định.

Final gate ngoài relevance logit còn cần IDF-weighted query-content coverage và original query quoted/numeric/route constraints nằm trong evidence clause. Dev-only calibration tìm trong finite grid đã định nghĩa, negatives<=paired baseline và<=5%, không mất support do truncation; tối đa strict evidenceHit@5/MRR, rồi ít wrong spans và gate chặt hơn khi hòa. Đây là scorer thí nghiệm, không phải entailment verifier đã được chứng minh.

First dev model run07:47:47–07:48:18UTC đạt7/28,0/20negative. Root cho phép **một** final dev-only refinement: normalize question framing cho ONNX query; không đổi scoring architecture/model/gates/labels. Original query vẫn dùng cho document retrieval, lexical coverage, constraints và provenance/scope. Capability/condition/negation/date không được bỏ qua; TDD thêm conditional-prefix guard để không nhầm “In case tenant is NOT present...” hoặc “Trong trường hợp không...” với source framing.5offset/extraction/constraint/normalization/revision tests PASS, có RED logs trước từng sửa.

Final model run `2026-11-02T07:58:28.964370Z`–`07:58:57.363029Z`, evaluation `07:59:08.797492Z`:

| Dev metric | Baseline | Final candidate |
|---|---:|---:|
| Positive / negative |28 /20|28 /20|
| Strict evidenceHit@1 / Hit@5 |0/28 /0/28|7/28 /7/28|
| Broad documentHit@1 / Hit@5 |2/28 /2/28|7/28 /7/28|
| Strict evidenceMRR@5 / Recall@5 |0 /0|0.250 /0.250|
| VI evidenceHit@5 |0/14|3/14|
| EN evidenceHit@5 |0/14|4/14|
| Negative có kết quả / abstention đúng |0/20 /20/20|0/20 /20/20|
| Identity/offset/hash violations trong returned hits |0|0|
| Wrong frozen support spans trong accepted positive hits |0|0|
| Supporting literal mất do truncation |0|0|
| Warm p50 / p95 |0.134s /0.216s|0.658s /0.950s|

Baseline strict evidence0không có nghĩa corpus rỗng: baseline có2broad document hits, nhưng returned200character snippet không chứa literal evidence đã chốt. Đây là **strict snippet proxy**, không human-adjudicated semantic answer correctness. Candidate strict metric dùng source+offset+hash của full returned clause. Hai mức được báo riêng để không lấy broad document match làm citation support. Các proxy còn có thể undercount equivalent wording; gatequality25%vẫn rõ ràng không đủ, không tự regrade để PASS.

Final cutoff `2.347182273864746`, minimumcoverage0.3, khóa chỉ từ dev tại07:59:08UTC. Quality gate2/3FAIL; safety/runtime/source-identity/selfcheck gatesPASS. Exact lookup nonregression end-to-end và final holdout chưa được thực hiện vì dev exit gate không đạt; không gọi chúng PASS.

## Technical findings và blocker chính xác

22/28dev positives có original frozen supporting span trong12clausecandidate pool;6bị mất trước reranking. Trong22candidates có support, best relevant-clause raw logit trải từ-7.410đến8.400, median-1.913; negative best logits từ-6.354đến1.377, median-3.344. Các score distributions chồng lấn. Giữ0false positives/20requires conservative cutoff/coverage, chỉ giữ7positive. Không có đủ margin để ngưỡng relevance này đồng thời đạt quality đã chốt.

Title removal đã loại việc title tự trở thành supporting evidence; explicit spans bảo vệ source identity. Nhưng multilingual MiniLM relevance vẫn cho điểm thấp cho nhiều clause có thật và đúng, đặc biệt cross-language/natural framed questions và tài liệu kỹ thuật/Markdown/code. Final framing normalization không cải thiện7/28. Những kết quả này chứng minh **tested model + clause selection + lexical support gate chưa đủ domain/answerability discrimination**, không chứng minh mọi local model hoặc mọi representation đều không thể làm được. Đây không phải thiếu RAM, Python compatibility, hay lý do “chưa cài reranker”: runtime thực đã chạy thành công với memory/latency dưới giới hạn.

## Runtime, safety và evidence

Reused official Apache2ONNX model/revision/tokenizer/wheel lock của experiment trước; không download mới. Cả hai clause containers dùng immutable Python runtime image698db791…, `--network none --cpus1 --memory768m`,512tokens,batch1,ORT1thread. Final model load1.695s; peakRSS561,904KiB (~548.7MiB), peakcgroup570,687,488bytes (~544.3MiB), OOMfalse. Warm latency gồm measured local embedding/retrieval và inference; không gồm cold model load, external sidecarIPC hoặc concurrent users. Các nguồn chỉ gửi local Ollama/BGE-M3 thread1, không provider trả phí/generation.

Scope selfcheckswrongproject/wrongrole/wrongactor/emptyrevisionmap/stalerevisions đều deny. Source span/citation identity kiểm tra against exact private bytecopy. Đây không thay thế live file-registry/API/Native ACL acceptance. Native failure cases trước vẫn diagnostic, không reuse để đổi ngưỡng của corpus này.

`clause-evidence-manifest.json` ghi exact private artifact hashes/container IDs/images/caps/exit/runtime, supporting-span-pool diagnostic và **holdout_query_artifacts=[]**. Tại08:00:32UTC, cả2ownedclausecontainers đã exit0,active0,OOM0; không auto-start benchmark cũ. Private cache `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/phase2-evidence-clauses` giữ bytecopies/manifest/labels/252vectors/devpairs/rawscores/decodedtokenvisibletext/evaluation. Public artifacts: `clause-dev-summary.json`, `clause-dev-before-query-normalization-summary.json`, `clause-calibration-lock.json`, `clause-source-manifest.json`, `clause-evidence-manifest.json`, các `clause-*-red/green.log`.

Final code hashes trong `clause-calibration-lock.json`:

- `clause_experiment.py`: `b30bf21e04bf277de4e722e9c12a82e20105a88c1e00c97d76f652611d51fbfc`.
- `clause_candidates.py`: `2b2d0d3bd709bc33deee5fd58ed2df14f8ae7f4947e0a9570c13d98d7d7c0237`.
- `clause_evaluate.py`: `43042bd9e936e1462812fbd692b7abb3fdedcdbcf82083755f96111731937d8d`.
- Existing ONNX runner: `43857e7507eb88d8a2f86322ed36d72aacff8568efc1058171f8aa8150cf6c8d`.

Không thử architecture/model/gate khác sau lượt cuối. Trước một hướng nghiên cứu tương lai cần independent relevance/answer-support adjudication, đánh giá pool recall theo condition/clauses đầy đủ và một multilingual answerability/entailment strategy phù hợp technical corpus; không chỉ tiếp tục sửa cutoff trên data đã biết. Không đưa runtime này vào Gateway384MiB hoặc coi file-only partial gain là Native recovery. **M2 vẫn FAILED/PARTIAL, không có safe semantic deployment từ các thử nghiệm này.**
