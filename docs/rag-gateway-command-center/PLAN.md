# Phase 4 — RAG, Gateway và Command Center

**Goal:** Hoàn thiện semantic retrieval và câu trả lời có nguồn kiểm chứng trên pipeline hiện có, sau đó nghiệm thu Gateway/UI theo đúng mức quyền.
**Architecture:** Giữ SQLite + BGE-M3/Ollama + Qdrant, Gateway/Native ACL và Rails bridge. Search vẫn search-only; explicit Web answer mode tái sử dụng Gemini.structured/Free-only policy/shared limiter hiện có để chọn trích đoạn trả lời, backend kiểm tra nguyên văn/citations. Search không generation; modeextract trả đoạn nguồn chưa tự chứng minh completeness. Telegram chuyển modeanswer thành Gatewayextract rồi giải thích bằng chính Commander/cap20, không thêm inference ẩn. Không thay keys/model/caps hoặc thêm orchestrator.
**Spec:** User attachment c390e450-fdb9-4c36-9cda-6a667d93e682/Pasted text.txt.
**Execution:** Một agent; thực thi tuần tự, self-review thay delegation theo yêu cầu trực tiếp. Dùng writing-plans, diagnosing-bugs và RED→GREEN ở seam thực tế.

## Bất biến

- gemini-3.5-flash-lite, keys/tokens/caps/pairing/outbox/gates giữ nguyên. Actual UTC bucket20769:18/20 calls; ngày hiển thị Asia/Bangkok13/11/2026 không có nghĩa budget đã reset.
- Catalog14, #398AwaitingOwner, PR15OPEN, modeOFF/idle; không Task/run/approval/merge mới trên MAIN.
- Không reset/clean/stash;8507 untracked files có sẵn. Không ghi DB business để điều khiển Agent.
- Không p95/stress/redesign/framework/dependency mới. Index chỉ sửa khi có bằng chứng, backup và scope/rollback cụ thể.

## Đã xác minh ban đầu

- HEADf3b713a, tracked tree sạch;4images đúng baseline; source/image parity Core/Gateway/Telegram PASS (7hostlegacy Gateway modules vẫn absent).
- Knowledge484documents/2485chunks, Qdrant2488points/1024Cosine, BGE-M3 đã cài. indexed_vectors_count0 không phải không có vectors: collection nhỏ hơn indexing_threshold10000.
- knowledge_answer.retrieval_response luôn answer=None; không có answer mode thực thi ở production read path.
- Generic knowledge_search chỉ chọn Native docs; registered files bị loại dù đã có search/read riêng và pin/ACL. Không được đưa legacy unregistered files vào search bằng cách bỏ scope.
- Repro dense-baseline: câu paraphrase resume có relevant chunk ở cosine0.5228; existing threshold0.65 loại nó. Negative sao Hỏa khoảng0.33. Đây mới là chẩn đoán, không tự giảm threshold để ép PASS; phải làm labeled calibration + held-out evaluation.

## Thực thi

- [x] A. Corpus/provenance/vector audit: actual payload/chunk consistency, empty/corrupt/duplicate/version; capture source pins và gold30–50cases từ nguồn thật. Tách calibration/held-out và retrieval/answer metrics; không bịa nguồn.
- [x] B. RAG core RED→GREEN: knowledge_search.py, knowledge_answer.py, service._knowledge và file_knowledge.py. Sửa ranking/evidence passage và unified authorized registered-source access; explicit search/answer mode, quote provenance, abstention và runtime-vs-history guard. Giữ Native pre/post ACL/version, source pin verification, hard limits và typed fallback/errors.
- [x] C. Callers/tests: Telegram tools.py/system instructions + strict optional mode, Rails controller/view/forms chỉ thêm choice vào Knowledge UI; không đổi controls đã đạt. Test injection, wrong-project/actor, stale metadata, missing/empty vectors, no-results vs outage, Unicode/paraphrase/multi-source/citations.
- [x] D. Gateway/Command Center inventory từ source + DOM; map29tools và mọi action, run direct reads/isolated command/auth/idempotency/concurrency contracts. MAIN business mutation giữ BLOCKED, không coi HTTP202 là executionPASS.
- [x] E. Relevant regression → candidate source parity → guarded image-only release cần thiết → MAIN read-back/real retrieval/answer/ACL → authenticated Web/Studio/Reports/error recovery. Actual Telegram Owner input chỉ khi cần chốt live transport, không giả inbound hoặc gửi proactive tự ý.
- [x] F. Before/after data/config/index pins,10deliverables, exact whitelist commits. Mọi gap ghi PARTIAL/NOT TESTED/BLOCKED/UNSUPPORTED riêng; không FULL PASS khi thiếu evidence.

## Validation / rollback

Targeted deterministic tests trước; semantic evaluation dùng BGE-M3/Qdrant thật, không Gemini judge. Mỗi answer fact phải là nguyên văn trong authorized passage và citation khớp source/version/chunk. Search không sinh answer; answer không là live runtime proof. Candidate dùng exact serving bases và không đổi env/mounts/networks/volumes. Rollback chỉ đổi image, giữ currentDB/history/catalog; không restore snapshot cũ để xóa records. Snapshot index private trước mọi sửa có chủ đích; không drop collection.

Cập nhật thiết kế sau repro: không nâng EXTRACTS_AVAILABLE thành SUPPORTED chỉ do có retrieval. Chỉ Web answer dùng structured selector (no tools), schema/source-span validation, post-generation ACL/version/activity/file-pin recheck. Dùng LiveBudget config nguyên trạng và deadline request tối đa60s (stricter than existing300); UI knowledge110s phù hợp Rails read100s +connect/render, controls vẫn15s. Existing Gateway policy model3.5lite/Free/billingOFF/rpd450/rpm13/tpm225000, analysis enabled; không đổi cấu hình. Model callbacks có thể bị provider/quota gate từ chối, khi đó trả ABSTAIN_PROVIDER thay vì giả answer.

Hoàn thành các hoạt động A–F trong scope được phép; đây không phải checklist FULL acceptance. RAG/Command Center/system vẫn PARTIAL; MAINwrites blocked. NaturalUTC20770 cho phép finalOwner41→42 freshRAG/checksumPASS; không còn block nghiệm thu footer.67Bot/Gateway466run22skip, finalCore file-read503/network giữ read-only/replay gates. Xem10reports và evidence levels.
