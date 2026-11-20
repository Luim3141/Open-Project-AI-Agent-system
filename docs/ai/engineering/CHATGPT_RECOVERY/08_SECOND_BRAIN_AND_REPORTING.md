# Phase2 current — 01/11/2026

Phase2 current: actual ReaderJS parser/no-store/ID/staleresponse and controller403/404/503 contracts tested; hardcodedPASS/PR/lock fallback removed. NodeplainmockDOM is not GUI acceptance. Real privatecorpus+135vectorcopy/Qdrantclone/localBGE-M3 tested: healthz exact/ACL/fallback/index-deletePASS; VN/ENsemantic misses remain (rag-score-diagnostics.json). No thresholdchangeforfixture. Historicalforcedsuccess projection flaggedRECONCILIATION_REQUIRED; rawDBverdictuntouched. UI PENDING OWNER MANUAL UAT.

---

# Second Brain và Reporting — source repair, 2026-11-01

Phạm vi: chỉ đọc runtime; sửa source và chạy isolated tests bằng `openproject/ai/.venv/Scripts/python.exe`. Không Computer Use/GUI, không provider inference/embedding mới, không deploy/restart, không ghi/xóa dữ liệu Project 5 hoặc runtime DB. Bản gốc 5 file đã snapshot trước edit trong `backups/rag-reports/` (tên file được thay `/` bằng `__`). Các file source hiện hữu là untracked trước phiên này; không coi Git HEAD là bản gốc.

## Bằng chứng và nguyên nhân

- Báo cáo factual bị phụ thuộc provider: `generate_report(..., include_narrative=False)` vẫn gọi `service.gemini.settings()` để in tên model. Thiếu/expired proof làm `GEMINI_DISABLED_PENDING_LOCAL_CREDENTIAL_COST_AND_DATA_VERIFICATION` và không tạo được báo cáo local. Đây là lỗi đã tái hiện trong bộ test có sẵn.
- Báo cáo chứa các khẳng định cố định `$0.00`, `341 WPs nguyên vẹn`, hệ thống sẵn sàng nhận task, QA/reviewer đã kiểm tra mà collector không chứng minh. Đã thay bằng phạm vi snapshot và giới hạn bằng chứng; không gọi provider để lấy tên model cho báo cáo factual.
- RAG có thể trả kết quả dense sai chủ đề cho lookup một từ (`email`) dù lexical không có match, chỉ vì cosine vượt 0.65. Fixture có nội dung `/healthz` và cosine 0.99 tái hiện chính xác đường lỗi thuật toán. Sửa hẹp: truy vấn một token phải có token đó trong title/content của document đã qua ACL; truy vấn nhiều từ vẫn giữ semantic retrieval VN/EN. Không đổi model, threshold hay corpus, không reindex.
- Report card tự bịa mặc định `5` completed, `12` transitions và `5` PRs khi thiếu dữ liệu. Đã hiển thị `Chưa có dữ liệu`; PR đọc đúng `metrics.github.total_prs`. JSON narrative được `json_escape` trước nhúng vào `<script type="application/json">`, tránh report text đóng script element. Modal tiếp tục dùng `textContent` và endpoint fallback hiện hữu.

## Probe runtime chỉ đọc

`docker ps --format '{{.Names}} {{.Status}}'` và `docker inspect qldapm-ai-gateway-1 --format '{{json .Mounts}}'`: exit 0. Xác định runtime mount `/state` từ local gateway directory; không in environment hay credentials.

Python `sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)` trên `gateway.sqlite` và `knowledge.sqlite`: exit 0. Chỉ SELECT, không khởi tạo `KnowledgeStorage` vào live path.

- 5 báo cáo Project 6 mới nhất đều có `narrative`: lần lượt 3656, 3323, 316, 321, 316 ký tự tại snapshot. Không có `summary`. Báo cáo không rỗng trong DB.
- Corpus: Project 5 có 445 documents; Project 6 có 14 documents. Đây là count knowledge, không phải WorkPackage count.
- Copy logic SELECT Project 6 thành `KnowledgeStorage(is_mock=True)` trong memory để thử lexical, không kết nối Ollama/Qdrant: `email` trả `[]`; `email của tôi` và `Tìm email của tôi` sai chủ đề WP382 bởi common words; `route GET /healthz` có WP384 nhưng nhiều kết quả phụ. Lần đầu probe exit 1 vì constructor thiếu `source_hash`, sửa dùng `classify_document`, lần sau exit 0.
- `docker exec qldapm-ai-gateway-1 python -c ...sha256(engineering_reporting.py)...`: exit 0, serving hash `be61a3801f6ce7f8c1109abb6b93b939e984f054e8d6d789b0f10e8ee6c968e2`, khớp source trước repair. Không deploy source mới.

## Red / Green và lệnh thực tế

Working directory các lệnh dưới: `D:\AI project\QLDAPM chat\openproject\ai`.

1. `.\.venv\Scripts\python.exe -m unittest tests.test_engineering_reporting -v` trước edit: **exit 1, 7 tests, 4 errors**. Bốn lỗi đều do factual report gọi Gemini settings khi không có proof.
2. `.\.venv\Scripts\python.exe -m unittest tests.test_engineering_reporting.EngineeringReportingTests.test_factual_report_does_not_require_or_claim_provider_verification tests.test_rag_recovery.RAGRecoveryTests.test_single_keyword_email_does_not_accept_unrelated_high_dense_score tests.test_rag_recovery.RAGRecoveryTests.test_multiword_vietnamese_and_english_semantic_queries_keep_dense_recall -v` sau thêm test, trước sửa source: **exit 1, 3 tests, 2 failures**. Report gọi settings; email lấy nhầm healthz. Multiword semantic VN/EN đã PASS.
3. `.\.venv\Scripts\python.exe -m unittest tests.test_engineering_reporting_contract -v` trước sửa view: **exit 1, 3 tests, 2 failures** — metrics mặc định và JSON chưa `json_escape`; reader contract hiện hữu PASS.
4. `.\.venv\Scripts\python.exe -m unittest tests.test_engineering_reporting tests.test_engineering_reporting_contract tests.test_rag_recovery -v` sau sửa source: **exit 1, 29 tests, 28 PASS / 1 FAIL** trong 16.397 giây. 8 reporting tests và 3 template tests PASS; email no-match, exact healthz positive, VN/EN multiword semantic và ACL/version tests PASS. Failure còn lại: `test_weak_semantic_result_abstains_but_provider_outage_allows_lexical_fallback` — long VN query trùng nhiều từ phổ thông vượt lexical50%, nên FTS vẫn trả một document dù dense score0.42. Chưa tuyên bố whole RAG suite green.

## Giới hạn còn lại

- Reader trống theo user: **NOT_REPRODUCED / chưa xác định root cause**. DB có full narrative; list/get backend và modal/fetch contract có dữ liệu. Không được tuyên bố đã fix UI thực tế khi không chạy GUI theo giới hạn user.
- Không đo lại live `email` cosine hoặc gọi embedding/provider để xác nhận live ranking. Regression chứng minh và sửa đường lỗi với fixture, không phải nghiệm thu corpus thật.
- Single-token anchor giảm semantic recall cho truy vấn một từ không xuất hiện nguyên token trong document; multiword VN/EN vẫn giữ dense-only recall. Đây là tradeoff lookup bảo thủ, chưa phải calibrated relevance evaluation toàn corpus.
- Vietnamese generic-word queries còn có false positives ở partial lexical fallback khi provider unavailable; nhánh `READY` không có relevant dense hit đã được sửa tiếp và kiểm tra theo phần bên dưới. Không đổi threshold/model hoặc tuyên bố calibrated relevance toàn corpus.
- Không chạy các old live fixtures, `test_hybrid_retrieval`, `test_p0_real_rag_corpus` hoặc `tools/test_reporting_scheduler_live.py`: chúng trỏ vào live state hoặc có writes. Không chạy n8n workflow/query acceptance trong scope này; không nhận n8n status là RAG proof.
- Source repair chưa deploy. Billing, provider health, native data integrity, UAT, full regression, hiệu lực schedule live và zero-cost đều chưa xác minh trong phiên này.

## RAG continuation — phân biệt no-match với provider outage

Snapshot bổ sung trước sửa `knowledge_search.py` và `test_rag_recovery.py`: `backups/rag-reports/rag-policy-20261101_112044/`. SHA256 source trước sửa `0c4a253d80f3adee5af177f2fb935c5f68c63c3cdc7cdcf493f613e33d62e60e`; test trước sửa `7c5384e539a63d3adbb46f65426598570c8bb0ae7b4871bb22a0ca6d5656dc68`.

Nguyên nhân failure còn lại: `_dense_search` đã xác định `READY` nhưng loại toàn bộ hits có cosine thấp; `search` vẫn trả partial lexical trực tiếp. Truy vấn dài chứa chủ đề tàu vũ trụ trùng nhiều từ với câu “Cơ chế điều khiển không có trong dự án nội bộ.” nên vượt ngưỡng lexical 50%.

Sửa tối thiểu: dense chạy trước lexical để biết trạng thái; khi `READY` và không có qualified dense hit, `_lexical_search(require_all_terms=True)` chỉ nhận document chứa đủ toàn bộ query terms đã tokenize (trong title/content). Exact lexical vẫn cứu được dense false negative. Khi provider `FALLBACK` hoặc `DISABLED`, giữ partial lexical hiện hữu; khi có relevant dense hits, giữ semantic/RRF VN/EN hiện hữu. Public search interface, ACL/actor/document scope, BM25 và cosine threshold không thay đổi.

Tradeoff rõ ràng: khi dense hoạt động nhưng không có relevant hit, lexical-only truy vấn dài thiếu dù chỉ một token sẽ abstain; đây là policy bảo thủ, không phải calibration trên corpus thật. Partial lexical outage vẫn có thể false positive. Quy tắc đủ token cũng không chứng minh semantic entailment.

Lệnh đã chạy, log cùng thư mục báo cáo:

1. Từ `openproject/ai`: `.\.venv\Scripts\python.exe -m unittest tests.test_rag_recovery.RAGRecoveryTests.test_weak_semantic_result_abstains_but_provider_outage_allows_lexical_fallback -v` — **RED: exit 1, 1 test FAIL**, tái hiện nguyên failure; `rag_policy_red.log`.
2. Thêm hai test: exact lexical survives weak/empty dense; partial lexical chỉ fallback khi unavailable và reset trạng thái READY/FALLBACK/READY/DISABLED qua các search. Chạy ba tests chỉ định trước sửa source — **RED: exit 1, 3 tests, 2 FAIL / 1 PASS**; `rag_policy_added_tests_red.log`.
3. Từ `openproject/ai`: `.\.venv\Scripts\python.exe -m unittest tests.test_rag_recovery tests.test_owner_lexical_scope tests.test_second_brain_persistence -v` — **GREEN: exit 0, 25/25 PASS, 8.242 giây**; `rag_policy_green.log`. Bao gồm exact/weak/empty/no-provider/outage/reset, semantic VN/EN, single-word email, persistent BM25, six-role/native version0, cross-project, actor/scope, chunk/revision và recovery tests trong SQLite tạm.
4. Từ repository root: `openproject/ai/.venv/Scripts/python.exe -m unittest openproject.ai.tests.test_knowledge_search openproject.ai.tests.test_knowledge_retrieval openproject.ai.tests.test_knowledge_ui_answer -v` — **exit 0, 18/18 PASS, 0.005 giây**; `rag_policy_mock_callers.log`. Ba modules đã đọc trước khi chạy, dùng `is_mock=True` in-memory và không tạo vector client/provider calls.

Tổng hai lệnh GREEN này: **43 isolated tests PASS**. Không đồng nhất với full regression hoặc acceptance live. Không inference mới, không Computer Use, không deploy và không thao tác live DB/Project 5. Lệnh snapshot đầu dùng nhầm relative path từ `openproject/ai` nên copy không thành; đã sửa đường dẫn, snapshot thành công và kiểm tra hashes trước mọi source/test edit.

## Independent review follow-up

Review phát hiện dense response parse lỗi sau khi state đã READY không khôi phục FALLBACK, khiến lexical bị lọc như healthy no-match. Test mới `test_malformed_dense_response_preserves_partial_lexical_fallback` đã RED (exit1), sửa một dòng state trong except, rồi GREEN trong bộ36tests RAG/workforce (exit0). Logs `run-20261101T035551Z/rag-parse-red.log` và `review-fixes-green.log`. Reviewer kiểm tra lại regression/probe; final Gateway candidate Linux có130tests đạt, không skips, trong mạng cách ly. Không suy thành live corpus/Owner UI acceptance.
