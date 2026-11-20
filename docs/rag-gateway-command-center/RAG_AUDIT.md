# Second Brain / RAG audit

Architecture implemented: registered local sources / Native WP+activity ingestion → SQLite document/FTS/chunk store → local Ollama BGE-M3 (1024 dimensions, Cosine) → Qdrant → authorized hybrid RRF(k60) → source/chunk/Native proof validation → optional Gemini quote selection → citations/UI. Không model embedding mới, không dependency/provider/queue/orchestrator mới.

Baseline [metadata](baseline.json), [actual source examples/index audit](corpus-evidence.json), [Native-authorized snapshot](authorized-corpus.json). 484documents=445P5+39P6;2485chunks,2488points. 0emptychunks,0payload/chunk mismatch;3orphan/oldchunk points được validator loại, không xóa để làm sạch số liệu. indexed_vectors_count0 trên collection nhỏ không phải thiếu vectors. Whole point/payload SHA trước/sau c945eb2c94e435359a23f4ed0618b131fe639b96b690fd828938903984cfeba4.

Actor18 current Native visibility/version audit cho341P5/18P6 eligible docs. Không đưa toàn bộ484docs vào tool chỉ vì đã index. Chỉ2registered files hiện hành: P5 main-workflow-contract và P6 project6-integration-qualification; file cũ không có registry bị loại. Không nhận user filesystem paths/arbitrary URLs. Parser/size/DOCX archive/PDF bounded loader giữ nguyên; OCR không hỗ trợ.

Root causes/fixes: generic search bỏ registered files; cutoff0.65 quá cao với calibration; repeated chunks chiếm dense candidate window; lexical fusion ghi đè best file passage; snippet200cắt mất fact; answerNone vô điều kiện; query race/timeout20s/overflowUI. Dense poolmax200 + file poolmax50, dedup/RRF và exact literal reference priority chỉ sau ACL. Source batch proof không bỏ hash guards. No stopword/model/index change.

Default search không inference. Extract chỉ EXTRACTS_AVAILABLE. Web answer dùng existing Free-only Gemini.structured/limiter để chọn nguyên văn, không tools. Backend exact substring + source index + chunk hash + Native version/source pin; post-generation recheck role/ACL/version/activity/pin. Exact quotation không tự bảo đảm entailment/completeness: semantic/answer acceptance còn PARTIAL, không flip global quality gate.

Prompt injection source là untrusted data. Selector không write tools; Bot RAG batch hard-deny writes trước execution và các round sau. Unsafe URI/forged chunk/citation/Native binding fail closed. Runtime/DONE hỏi live cần Observer, không dùng lịch sử source để kết luận hoàn thành. Search outages/empty/denied/stale có reason riêng; provider errors ABSTAIN_PROVIDER. Không tự retry mutation/indexing.

Câu hỏi tài liệu/tri thức rõ ràng bằng tiếng Việt hoặc English được Bot đọc RAG trước model, kể cả hỏi lại câu cũ; không để model tự bỏ qua tool rồi dùng memory. Không có nguồn mới thì NO_EVIDENCE, không gọi model để suy diễn. Source references từ server được giữ ở footer và được gắn nhãn truy hồi, không phải xác nhận runtime. Những intent không rõ ràng vẫn phụ thuộc model routing; không tuyên bố mọi cách diễn đạt đều đã được nghiệm thu.

Public source [code](../../openproject/ai/gateway/knowledge_search.py), [answers](../../openproject/ai/gateway/knowledge_answer.py), [service](../../openproject/ai/gateway/service.py); details test/evaluation trong báo cáo riêng. Không reindex/cập nhật corpus hoặc đổi checksum allowlist trong phase này.
