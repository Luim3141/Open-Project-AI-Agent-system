<!-- AUTONOMOUS_FINAL_CURRENT_20261104 -->
# Semantic RAG —FAILED qualification

**Semantic RAG FAILED qualification; serving RAG không đổi.** B5 replay xác định SPAN_REFERENCE_MISMATCH (span10 thay vì5); offline unique same-source pointer repair vẫn không chứng minh answer. Typed FORMAT/SOURCE/SPAN/QUOTE/SUPPORT + bounded redacted captures giữ validator chặt.

Root corpus:11/15docs có JSON bị cắt, các business fields/boolean/path mất; whole-journal candidate giữ15docs/230073chars/117journals,906typedfacts, Unicode offsets/hash. Decode trước split, phân biệt Native fields, requirements và historical receipts. Research actual BGE/Qdrant906points + FTS/identity cho **DEV retrievalHit@5=13/13 (100%)**; đây là observed correlated DEV, không phải benchmark độc lập hay serving quality.

Final answer chưa đạt: six-case semantic-fact pilot strictsupport3/4positive, no-answer0/2negative emitted; một CRUD answer còn lẫn parent379/copied objective. Warm1.424–2.827s/cold16.406s. Expanded DEV dùng lại5cached pilot replies, chỉ3generation requests mới, dừng đúng gate ở warm5.944s>5s.4positive answers được quan sát, strictsupport2/4: hai câu “initial unit/create/list/SQLite” chỉ chọn unitname nên không đủ toàn bộ evidence.17candidate citations kiểm exacthash/offset/Nativeid/version không lỗi, nhưng quote identity không đồng nghĩa semantic support. RepresentativeFPR **NOT_ESTABLISHED**;0/2negative không chứng minh≤5%. Không mở oldholdout, không tạo/scoring lockedholdout khi DEV gate còn fail, không đổi gate để gọi PASS.

Current serving vẫn metadata retrieval/answer:null, NO_EVIDENCE hoặc UNVERIFIED_RETRIEVAL. Baseline observedDEV Hit2/13/FPR1/20 là lịch sử của serving baseline, không lấy candidate13/13 gán cho MAIN. Không có qualified RAG image hoặc postdeploy semantic E2E mới. Source-grade nghiên cứu không thay cho retrieval→evidence→answer→citation acceptance. Chỉ WP392 threeintents từng được Owner xác nhận; các nhãn khác là assistant source review, không gọi human ground truth. Lượt tiếp tục này11local4B requests,0Gemini mới, không tải/đổi model hoặc trả phí.

Essential FAILED: Semantic RAG complete-answer/evidence selection và worst-case latency/representativeFPR chưaqualified; candidate khôngdeploy, MAINsemanticE2E chưachạy. PUBLICATION_REDACTED_UAT: browser interactions/accessibility/loading/error/links; WAITING_FOR_SCHEDULE: current WF12 wallclock. Preserved partial:8WP385 unmatchedvectors/2historicalDEAD và persistedproviderREADINESS_STALE. Không tuyên bố FULL FUNCTIONAL DEMO READY.

Tiếp tục duy nhất có ích: sửa complete-evidence selection/parent-copy ambiguity và ổn định latency với gate5s giữ nguyên; đóng băng nguồn+code+broaderdevelopment/lockedholdout labels có source review trước khi score; chỉ sau tất cảqualitygates mới tích hợp serving/rollout/RAGMAINE2E. Không replay các private consumedintents (`main-setup-intent`, `main-delegated-acceptance-intent`, pilots/DEV) hoặc tự kích lại delegation/AUTO. Một root làm tuần tự; không spawn thêm subagent. Inventory hiện tại không chứng minh được tài khoảnCodexkhác đã hoàn tất; không gọi đó là verified.
<!-- END_AUTONOMOUS_FINAL_CURRENT_20261104 -->

<!-- FUNCTIONAL_CURRENT_20261104 -->
# RAG04/11 — chưa đạt

RAG chưa đạt. Serving baseline trên observed DEV: Hit@5=2/13 (15.38%), FPR1/20 (5%); chưa có benchmark mới được chứng nhận. Reader candidate DEV Hit@5=6/13 (46.15%), support3/13, FPR4/20 (20%) bị REJECTED và không deploy. Owner đã xác nhận3intents WP392;6cards VN/EN tương quan không phải benchmark đại diện hay phê duyệt candidate.
Hai pilot context ngắn cùng6câu đều `DIAGNOSTIC_COMPLETE`/`DIAGNOSTIC_COMPLETE` và không đạt:1.7B chọn supporting span1/4 positive, trả unsupported match1/2 negative;4B support2/4, negative output0/2. Warm model-only0.570–0.782s và2.601–4.862s; cold load, cached retrieval và whole-answer quality được báo riêng. Không chạy full DEV/holdout theo gate đã đóng băng. Chi tiết: `integration-final/rag/SHORT_CONTEXT_CAPACITY_RESULT.md`; không dùng các tỷ lệ pilot như benchmark acceptance. Grouped-source + answer/quote pilot `DIAGNOSTIC_STOPPED`:2responses hợp lệ, response thứ3 bị exact-quote validation từ chối (`INVALID_RESPONSE_ValueError`); valid selections support1/2 và answer còn mơ hồ. Dừng đúng gate, không mở full DEV/holdout hoặc deploy. Raw response bị từ chối chưa được lưu nên chưa kết luận cụ thể loại quote error.
`integration-final/rag/OWNER_REVIEW_PACKET_V2_REVIEWED.json` lưu đúng Owner reply; không mở/tune heldout queries/labels. JSON decoding chỉ đổi8/226spans, không phải lời giải answerability. Giữ source-span hashes/offsets, ACL/freshness và các failure receipts.
<!-- END_FUNCTIONAL_CURRENT_20261104 -->

<!-- FULL_INTEGRATION_20261103_CURRENT -->
# Semantic RAG — full integration 03/11/2026

**FAILED / NOT DEPLOYED.** Baseline DEV Hit@5 2/13, FPR1/20; Qwen candidate8/13, FPR2/20, p95 7.281s. DEV8 post-hoc document13/13, exact support span9/13; 20/20 negative còn candidate vì chưa có abstention, không thể gọi là FPR. Holdout queries/labels chưa mở; DEV đã đưa holdout-source documents vào context, không claim document-unseen, labels chưa independent/human review. BGE/Qdrant hiện phục vụ baseline. Xem `integration-final/SECOND_BRAIN_RAG_EVALUATION.md` và `integration-final/rag/span-dev8-relevance.json`.
<!-- END_FULL_INTEGRATION_20261103_CURRENT -->

# Second Brain / RAG — cập nhật Final Demo 03/11/2026

**M2 semantic FAILED, candidate REJECTED_NOT_DEPLOYED.** Bộ mới freeze dev/holdout trên corpus Project6/actor20, actual local BGE-M3 và Qdrant clone: baseline holdout Hit@5 3/20, negatives0/20; candidate Hit@5 13/20, negatives14/20. Chỉ số tốt trên dev24/24+0/20 không tổng quát sang holdout. Metadata citation errors0 ở phạm vi snapshot. Nhãn agent-grounded/correlated chưa human adjudication; không coi là benchmark độc lập hoặc ACL/end-to-end sign-off.

Giữ nguyên labels/hash/lock/results; không tune lại holdout. Candidate source lưu `demo-final/rag/rejected-candidate/`, serving retrieval được khôi phục từ image b184, không đổi threshold0.65. Container evaluation có ownershiplabel đã dọn, MAIN Qdrant không ghi bởi benchmark. Xem `demo-final/rag/RESULT.md`, `holdout-result.json`, `disposition.json`. Semantic quality là lỗi chức năng còn lại, không thuộc security defer.

## Lịch sử post-30218aff

**Chưa đạt acceptance semantic VN/EN.** Trong probe trên clone với title embeddings thực tế, sáu truy vấn dương tính và ba truy vấn âm khó có khoảng cosine chồng lấn: ngưỡng 0,52 thu hồi 6/6 nhưng nhận nhầm 2/3; 0,57 không nhận nhầm nhưng chỉ thu hồi 2/6; 0,65 không thu hồi truy vấn dương nào. BM25 thử nghiệm đạt hit@1 3/6, hit@5 5/6, MRR@5 0,617 và nhận nhầm 2/3 âm khó. Đây là tập nhỏ chẩn đoán, không phải benchmark đại diện hoặc cơ sở chứng minh chất lượng production.

Normalization của index và query được đối chiếu thống nhất; 21 test `test_rag_recovery.py` PASS. Không thay threshold production chỉ theo tập này. Cần bộ đánh giá có nhãn đủ rộng, xem đầy đủ chunks và citation/source authorization, sau đó thử reranker hoặc hybrid có calibration và đo cả abstention; kiểm tra index của WP mới bằng read-back thực tế. `READY` nhưng không có kết quả hiện chưa phân biệt rõ không đủ confidence với không có tài liệu phù hợp.

Chi tiết probe: `post30218-20261101T1540Z/rag-title-probe.json`. Các test pass không chứng minh semantic retrieval đã đạt.

## Stabilization — benchmark trên bản sao vector/chunk

`stabilization-rag/` có script và kết quả tái lập với 6 positive và 6 negative VN/EN. Trên fixture vector transport, ngưỡng hiện tại 0,65 đạt Hit@1 2/6, Hit@5 2/6, 0/6 negative trả kết quả; 0,57 đạt 3/6, 4/6, 0/6; 0,52 đạt Hit@1 3–4/6 qua hai lượt, Hit@5 6/6 nhưng 2/6 negative trả kết quả. Biến động thứ hạng giữa hai lượt chưa được điều tra. Sai role, sai actor và scope rỗng trả 0; 24 test recovery/scope PASS. Tập nhỏ, negative chưa được adjudicate độc lập, fixture không kiểm tra Qdrant filter thật và chưa đánh giá citation: không dùng để điều chỉnh threshold hoặc tuyên bố acceptance. Kết quả cũng cho thấy partial lexical match khi có dense hit có thể thêm ứng viên không liên quan. Tiêu chí holdout đề xuất tại `stabilization-rag/ACCEPTANCE_PLAN.md`; chưa có kết quả holdout.

Baseline tạm thời 24 positive / 20 candidate negative VN/EN, threshold 0.65: Hit@1/5 4/24, MRR 0.167, 0/20 negative; xem `stabilization-rag/PROVISIONAL_BASELINE_20261102.md`. Nhãn chưa được người độc lập adjudicate, chưa có holdout hoặc kiểm thử ACL/citation tổng quát; không coi đây là acceptance benchmark.

## Phase2-final — rejected semantic candidate, safe citation correction

`phase2-final/rag/RESULT.md` contains frozen dev/holdout gates, source/model/corpus hashes and actual Qdrant clone transport. Re-embedding13first chunks matched stored vectors (cosine≈1), repeated vectors identical; no observed model drift. JSON/audit text dilution and chunk representation were investigated. Candidate holdout Hit@5 increased8→15/24 but Hit@1 stayed8/24 and false positives rose1→2/20; EN top1 also decreased. Pre-fixed safety gate FAILED; representation source was restored and threshold0.65/chunk600/100 retained.

Only citation identity correction was deployed: use verified SQLite metadata Native ID rather than vector alias work_package_id.16actual Qdrant clone scope/freshness/prune/delete/restart/citation contracts passed; this is separate from semantic relevance. Labels were source-grounded agent judgments, no independent human adjudication. No installed reranker/runtime was found in scoped host/Gateway/Ollama inventories; no new download or paid service.

## Phase 2 final — candidates rejected, no semantic rollout

Citation identity fix đã deploy: Native ID lấy từ metadata SQLite đã xác minh, không tin vector alias. Exact child #387/#389/#390 lock version 2/citation được Gateway API read-back; đây không phải semantic acceptance.

- Chunk expansion: holdout Hit@5 tăng 8→15/24 nhưng negatives 1→2/20, REJECTED (`phase2-final/rag/RESULT.md`).
- Local multilingual MiniLM ONNX: fresh Native holdout Hit@5 10→19/24, MRR .417→.708, p95 4,12 giây, khoảng 548 MiB; negatives tăng 0→2/20. REJECTED (`RERANKER_RESULT.md`). Hai false positives liên quan title/version-history; không dùng title match làm bằng chứng answer.
- Literal evidence clauses trên 12 file thật, có revision/path/hash/offset: final dev strict evidence Hit@5 7/28, negatives 0/20, p95 0,95 giây, khoảng 549 MiB. Không đạt gate ≥2/3; STOP trước holdout mới 30 positive/20 negative. Supporting evidence có trong pool cho 22/28, nhưng score relevant/negative chồng lấn; framing normalization không cải thiện. `CLAUSE_RESULT.md`, `clause-evidence-manifest.json` giữ byte provenance và xác nhận holdout query artifacts rỗng.

Không có model/index/chunk/threshold candidate nào deploy MAIN; production chunk 600/100 và cosine 0.65 giữ nguyên. Stored/regenerated embedding cosine gần 1 và deterministic trong phép lặp; không có bằng chứng model drift ở 13 vector kiểm tra. Corpus audit/JSON dài gây dilution là một nguyên nhân quan sát được, nhưng chưa có giải pháp đạt quality+abstention. Labels do agent đọc nguồn, HUMAN_REVIEW_PENDING; strict snippet proxy có thể bỏ sót cách diễn đạt tương đương, không tự regrade để đạt gate. M2 **FAILED/PARTIAL**, không chứng nhận semantic RAG đã hồi phục. Final inventory 12 owned experiment containers: active 0/OOM 0; cache private không phục vụ request MAIN.

## Phase3 — freshness restored independently of semantic gate

Read `phase3-owner/rag/RESULT.md`.14historical semantic misses had relevant chunk ranks1–8 but cosine<0.65; rejected chunk-monopolization hypothesis before tuning. No new model/threshold/passages candidate. New actual failure was cross-project scan coupling: Project5WP175activity404 skippedProject6 indefinitely. Exception isolation per scope and independent reporting tick deployed.

MAIN read-only Native18/20 + SQLite/Qdrant after rollout:10/10actor20sources current,161points. Exact387/389/390signedRailsread-back returns Native version2/citation,denseREADY. Owner may legitimately receive current sharedcanonical source; not every valid result must be actor20 snapshot. Original strict operationalclone FAILED remains retained, root lexical-only diagnostic explains both overstrict assumptions; do not call it whole-gatePASS. Semantic answerability/quality still FAILED/PARTIAL; no human adjudication and no semantic candidate deployed.
