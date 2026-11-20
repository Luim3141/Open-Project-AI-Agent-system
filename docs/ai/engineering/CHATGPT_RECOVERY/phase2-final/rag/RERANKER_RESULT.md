# Local cross-encoder experiment — REJECTED ON HOLDOUT

Later continuation: root authorized one separate12-file evidence-clause experiment. It stopped on the fixed DEV quality gate after its final permitted query-normalization pass, leaving its fresh holdout unconsumed. See `CLAUSE_RESULT.md`; neither experiment produced a semantic deployment.

**Không triển khai model/source/cấu hình lên MAIN.** Cross-encoder chạy được trong giới hạn laptop và cải thiện tìm đúng tài liệu; nhưng chưa đạt answerability/abstention gate. Giữ production retrieval policy hiện hữu. Các kết quả dưới đây là nhãn do agent đọc source, `HUMAN_REVIEW_PENDING`, không phải Owner acceptance.

## Kết quả cuối

| Metric holdout | Production baseline trên snapshot | Cross-encoder candidate |
|---|---:|---:|
| Positive / negative queries |24 /20|24 /20|
| Hit@1 theo native document |10/24|15/24|
| Hit@5 / Recall@5 theo native document |10/24 (41.7%)|19/24 (79.2%)|
| MRR@5 |0.417|0.708|
| VN Hit@1 / Hit@5 |6/12 /6/12|9/12 /11/12|
| EN Hit@1 / Hit@5 |4/12 /4/12|6/12 /8/12|
| Exact top1 |4/4|4/4|
| Negative trả kết quả |0/20|2/20 (10%)|
| Abstention đúng trên negative |20/20|18/20|
| Citation source/native identity violations |0|0|
| Candidate relevant-document hits khớp frozen support-literal/chunk proxy |Không đo bằng proxy này|12/19|
| Candidate bị mất frozen supporting literal do truncation512 |Không áp dụng|0|
| Warm p50 / p95 |0.140s /0.232s|2.260s /4.124s|

Candidate tăng Hit@5 thêm37.5điểm phần trăm và giữ exact lookup. Tuy nhiên negative rate tăng từ0 lên10%, vượt5% và vi phạm điều kiện không tăng so với baseline. Đây là lý do độc lập đủ để **REJECT**. `source_chunk_support` proxy cũng không đạt; phân biệt proxy với semantic judgment bên dưới. Không sửa threshold, model, passage construction hoặc nhãn sau khi xem holdout.

Thời gian model holdout: `2026-11-02T07:23:31.947919Z`–`07:25:20.542226Z`; evaluation `07:25:28.527509Z`. Model load4.060s; peak RSS561,664KiB (~548.5MiB), peak cgroup569,905,152bytes (~543.5MiB), CPU1, hard cap768MiB,512tokens, batch1. Warm query latency cộng thời gian embedding/retrieval đã đo và tổng thời gian từng `session.run`; không gồm model cold load, IPC của sidecar chưa xây dựng, hay contention nhiều người dùng. Không có OOM. Vì vậy chưa coi4.124s là SLA production.

## Corpus, split và khóa trước holdout

Scoped read-only snapshot lúc chuẩn bị:10Project6/PM/actor20 documents,109chunks, SHA256 `f0186c27f40ad554c8648fcb6c31178487a58d23ac783e722c9d6a279081c18e`. Nhãn mới khóa05:01:20UTC, SHA256 `5a9f62e98197db3b34dec331496951fea92394f1239a400e9ad2b8bdba0b7d43`: dev24positive/20negative; initial holdout36positive/20negative. Primary dev sources383/384/386; primary holdout mới387/389/390. Không dùng passage-candidate holdout đã tiêu thụ trước đó để chọn cross-encoder.

Root xác minh Native visibility/lock versions bằng `OS_OPERATOR_NATIVE_READ` khoảng05:04UTC: `Service.engineering.scoped(project6)`, `Native.identity20 PM`, `Native.package` từng ID, project links đều `/api/v3/projects/6`. Đây không phải signed browser bridge. Snapshot390lock1 khác Native2 nên12positive của390 bị loại **trước scoring**, giữ làm stale-source exclusion; snapshot379revision không còn trong scoped Qdrant copy cũng bị loại, không tái tạo từ text cũ. Hai arm dùng cùng8authorized current revisions/81chunks, cùng vectors, scope và query embeddings. Final holdout24positive/20negative thuộc387/389. Corpus nhỏ, paired languages/intents và source overlap có tương quan; không đưa confidence interval giả định independent samples.

Baseline: `KnowledgeSearchEngine` thực, cosine floor0.65, exact cosine trên bản sao vector đã lọc/kiểm tra payload, deterministic tie ordering. Candidate: rawdense top40 + lexical top10documents mở rộng sang chunk/cap60; giữ tối đa2representative chunks/document theo dense/lexical insertion order; rerank query với `source title + original chunk`, dùng ONNX raw relevance logit. Native ID/source/chunk hashes không được model tạo lại. Actual ANN search/transport latency không được dùng trong paired scoring; real Qdrant prefilters được kiểm tra riêng.

Dev-only experiments được giữ nguyên bằng chứng: full broad pool2040pairs quá chậm(p95=8.44s);2representatives/256tokens691pairs p95=2.45s nhưng1supporting invariant bị truncation;2representatives/512tokens691pairs đạt tất cả fixed dev gates: Hit@1=16/24,Hit@5=17/24,MRR0.681,negatives0/20,p95=3.761s,17/17support-literal matches. Không bỏ qua truncation guard để PASS.

Khóa cuối tại `2026-11-02T07:22:39.337364Z`, **trước** holdout retrieval/scoring:

- Cutoff: raw logit `1.3410100936889648`, được chọn chỉ trên dev theo quy tắc đã ghi: negatives<=baseline và<=5%, tối đa Hit@5 rồi MRR, rồi cutoff cao hơn khi hòa.
- Candidate generator SHA256 `29df9ce6e72d5517e50247b4749889c9a9b19f841dc9475d363fac7c147e8bef`.
- Offline ONNX runner SHA256 `43857e7507eb88d8a2f86322ed36d72aacff8568efc1058171f8aa8150cf6c8d`.
- Evaluator SHA256 `78df666bb3b3c0152dd13b5e01b54f1f5f63fd36d6b160d87c730dfd7891e273`.

Evaluator assert những hash này trước khi dùng holdout. Holdout chỉ chạy một lần,684pairs. `reranker-calibration-lock.json` và `reranker-holdout-summary.json` giữ exact code/runtime/gates.

## Phân tích failure, không sửa nhãn hậu nghiệm

**Hai false positives là một intent pair VN/EN về API trả mọi phiên bản title cũ.** Tài liệu được trả là WP389, mô tả task existence. Không tài liệu được phép nào trong snapshot mô tả title version history. Query VN có logit1.5159, EN1.4672, đều vượt cutoff1.3410. Đây là **answerability failure trên topic overlap**, không phải ACL leak hay sai native identity. Cross-encoder học relevance/ranking, không tự chứng minh nội dung có câu trả lời. Các từ API/task/identifier cùng ngữ cảnh giúp source liên quan chung nhận điểm cao dù thiếu capability được hỏi. Không thể kết luận chỉ nâng cutoff sẽ sửa an toàn: việc đó phải được đánh giá trên tập mới, không tập holdout đã thấy.

**12/19 là strict frozen literal-support proxy, không phải “chỉ12citation đúng về nghĩa”.** Ground truth positive chỉ định relevant native document và các supporting chunks chứa một literal đã chọn trước scoring. Evaluator kiểm tra returned relevant-document chunk theo đúng frozen chunk hashes/literal; đây hẹp hơn semantic equivalence. Inspection sau holdout cho thấy:

-4cases VN/EN `exists=true`/`exists=false`: selected chunk1 của389 chứa acceptance clauses `với task_id tồn tại/không tồn tại...`, trong khi frozen evidence chọn phrasing `nếu task tồn tại/không tồn tại...` ở chunk khác. Đây là equivalent wording bị literal proxy bỏ sót; không được báo là4confirmed false citations.
-1case “giữ nguyên endpoints/schema”: selected chunk4 ghi summary giữ nguyên API cũ và schema, nhưng frozen support literal là `Không thay đổi schema` ở chunk khác. Cũng có semantic support khả dĩ; nhãn/hit không được sửa để cải thiện metric sau holdout.
-2cases VN/EN về empty SQLite database: selected chunk4/summary và title mô tả existence/true-false nói chung; explicit empty-database edge case nằm ở chunk khác, không trong selected representative. Đây là thiếu explicit passage support cho condition được hỏi; inference từ “missing task→false” cần người đọc adjudicate, không tự chứng nhận đúng bằng document-level hit.

Tất cả19hits vẫn giữ đúng source/native identity; không có cross-project/actor leak. Broad document hit không đồng nghĩa retrieved passage hỗ trợ đủ answer condition. Model đã thấy512token và không mất frozen supporting literal do truncation ở những passage có literal; vấn đề còn lại là chọn passage và answerability. Không đo generated answer correctness hoặc rendered UI citation; không có provider generation.

Title được prepend giống nhau vào mọi chunk của một tài liệu. **Suy luận cần thử riêng:** điều này có thể làm chunk thiếu clause trông liên quan nhờ title chứa toàn bộ tên feature. Không có title-ablation experiment nên chưa tuyên bố causal proof. Tương tự,2representative chunks giảm latency nhưng có thể bỏ qua explicit edge-case clause. Chuyển sang chấm cả document dài cũng không tự giải quyết no-answer và có thể làm mất clause vì context limit.

## Feasibility và safety thực sự đã kiểm tra

Official Apache2model `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, revision `1427fd652930e4ba29e8149678df786c240d8825`; AVX2UINT8ONNX118,620,016bytes + tokenizer17,082,660bytes đã khớp published LFS SHA256.20binary wheels được pin version+hash, offline install `--no-index --require-hashes`, ONNXRuntime1.31.1/Tokenizers0.23.3/NumPy2.5.4 trên Python3.14.8; `pip check` PASS. Không Torch, không `trust_remote_code`, không trả phí; CPUExecutionProvider, threads1, spinning off. Tất cả model runs dùng `--network none --cpus 1 --memory 768m`; corpus không gửi ra ngoài. Metadata/download phase chỉ gọi official public artifact endpoints, không mang corpus. Primary sources/license/compatibility citations ở `RERANKER_FEASIBILITY.md`; installed assets không còn là blocker giả định.

At07:24:34UTC, actual MAIN Qdrant **READ ONLY** search bằng copied authorized vector: allowed40hits đều trong8allowed hashes; wrongproject,wrongrole,wrongactor,emptydocument scope đều0. `reranker-main-readonly-acl.json` chứa route và limitations. Candidate generator cũng assert các scope trên fixture trước scoring, gồm stale390source. Index add/revision/delete/restart/forged payload contracts16PASS từ experiment cô lập trước đó vẫn ở `integration-results.json`; không thay source/indexing code cho reranker và không gộp chúng thành live semantic acceptance.

Docker LinuxEngine không khả dụng ở lượt07:18; root khởi động lại Docker, runner bắt đầu khi API ready07:20. Không replay MAIN. Các container thí nghiệm đã exit, dữ liệu/cache giữ lại; inventory `reranker-evidence-manifest.json` ghi IDs/images/caps/network/exit/OOM. Model container base là immutable Gateway image698db791… dùng làm Python runtime, không phải việc triển khai lại MAIN.

## Một hướng tiếp theo, chưa được phép thực nghiệm

**Đề xuất nhỏ nhất: tách document retrieval khỏi evidence-passage acceptance.** Giữ scoped candidate document recall rộng; thay2opaque windows bằng các nguyên văn semantic clauses/acceptance sentences có offset/hash về source, rồi rerank/query-match đúng clause và trả chính clause được chọn. Title chỉ dùng cho document retrieval/context metadata, không được coi là supporting evidence cho mọi clause. Final gate cần kiểm tra requested capability/condition xuất hiện trong evidence passage, bên cạnh relevance score; no-answer title-history phải không được đáp bằng existence. Một generic cross-encoder cutoff vẫn cần dev calibration và hard negatives; không cam kết tự có entailment chỉ nhờ thay passage.

Để tránh cạn holdout nhóm WP6, chuẩn bị corpus mới từ **các tài liệu thực trong repo đã được owner cấp scope local ingestion**, không tạo WP: chọn các architecture/runbook/API docs có chủ đề khác nhau, ghi rõ implemented/proposed/historical và date/version, loại secret/private config, chỉ project/actor/role được phép. Allowlist đường dẫn/source revision trước ingest trên clone; không tự coi toàn bộ repo được truy cập cho mọi actor. Chọn10–15documents với intent groups không trùng, lập literal+semantic equivalent supporting clauses đầy đủ trước evaluation; agent đọc source và owner reviewPENDING được ghi riêng. Dev và holdout chia theo document/intent, tối thiểu20positive+20hardnegative holdout, include wrongcondition/missingcapability/time/version queries. Đóng băng budget/gates như hiện tại, test source offsets/hash/native-or-file provenance và exact lookup; chỉ sau đó mới hiệu chỉnh clause model/threshold trên dev rồi dùng holdout mới một lần.

Không chạy ablation, không nâng cutoff theo title-history failures, không tiếp tục tune holdout đã dùng. Root phải phê duyệt scope và hướng tiếp theo trước experiment mới. Runtime/model hiện nằm private cache dành cho nghiên cứu; **không có safe deployable semantic recovery** từ lượt này.

## Evidence và cách chạy lại nghiên cứu

Private cache: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/phase2-reranker`; full labels, source snapshot, vector snapshot, query/passages, raw logits/decoded token text, evaluation từng case, package wheelhouse/venv/model. Public repo evidence: `reranker-{dev,holdout}-summary.json`, `reranker-calibration-lock.json`, `reranker-{asset,wheel,evidence}-manifest.json`, `reranker-package-check.json`, `reranker-main-readonly-acl.json`; code `prepare_reranker.py`, `prepare_reranker_labels.py`, `reranker_candidates.py`, `reranker_offline.py`, `reranker_evaluate.py`.

Exact model command được giữ trong container inventory; chuẩn là:

```powershell
docker run --name qldapm-phase2-reranker-holdout512 --network none --cpus 1 --memory 768m --env TOKENIZERS_PARALLELISM=false --env OMP_NUM_THREADS=1 --entrypoint /experiment/venv/bin/python --mount "type=bind,source=<private-cache>,target=/experiment" --mount "type=bind,source=<this-rag-directory>,target=/scripts,readonly" sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb /scripts/reranker_offline.py score --input holdout-pairs.json --output holdout-scores.json
```

Đây là provenance, không chỉ dẫn dùng lại consumed holdout để tuning/acceptance mới. Không tự start các container cũ. No new production source edits in this reranker investigation; root's independent fencing work changed production ingestion SHA after its earlier restoration, which is recorded separately in evidence manifest rather than overwritten.
