# RAG evaluation — PARTIAL

[Gold40](gold.json): facts/citations xuất phát từ actual Native/file sources, expected facts assert nguyên văn; 8calibration +32holdout. 36retrieval cases và4runtime/unauthorized contract cases; không bịa positive sources. [Runner](evaluate.py) dùng BGE-M3/Qdrant thật, private SQLite backup và captured Native authorized doc-ID scope; **không phải40 MAIN/API/LLM answers**.

Baseline cutoff0.65:8/36 retrieval hits; final0.45:25/36 (69.4%), calibration6/8, retrieval holdout19/28. Các threshold exploration được giữ, không chọn lại labels để làm đẹp. DENSE_MIN_COSINE0.45 chọn bằng8calibration; cutoff thấp hơn có thể tăng irrelevant hits. Cân bằng source pool và literal reference fix có regression thật; raw RRF score không là probability hay answer confidence.

Naive extract all-fact diagnostic20/36 (55.6%), **không phải Gemini answer accuracy**. Missing cases: G08, G10, G12, G13, G15, G17, G18, G22, G29, G32, G34. Strict expected-source matching có thể bỏ qua alternative source chứa cùng fact; không sửa labels sau test để ép PASS. Không chạy bulkGeminijudge hoặc40inferences.

Actual MAIN positive answer: browser-uat quotes đúng fixture purpose + “does not certify … Owner acceptance”, pinned source readback khớp; real provider receipt d07c1cb4-5b9e-4e98-9568-4d316d471fe2 resolved exact3.5lite. OwnerTelegram37→38 đúng nội dung nhưng chưa có technical footer. Sau ngày UTC mới, lượt39→40 tái hiện model bỏ tool/dùng memory; giữ failure riêng. Bản sửa67tests bắt buộc freshRAG cho câu hỏi tài liệu; lượt41→42 PASS có fresh search(modeanswer→Gatewayextract), sourcechecksum và resolvedexact3.5lite, chỉ1inference.

First MAIN longquery trước anchor fix: retrieval thiếu file nên Gemini ABSTAIN; preserve [failure](main-read-before-anchor.json), không gọi positivePASS. Final same question Web tìm đúng và supported. NegativeMars ban đầu upstream503→ABSTAIN_PROVIDER ([failure](main-negative-answer-upstream503.json)); không tính là semanticabstentionPASS. Sau6giờ và actualBotprovider success, một lượt negative mới nhận ABSTAIN/model_usedtrue/resolvedexact3.5lite: [packet](main-negative-answer.json). Không retry mù hoặc thay model. Initial MARS noresults→NO_EVIDENCE không cần inference; isolated false/forged/source-change/injection tests PASS.

| ID | Partition | Group | Question | Expected source | Retrieval | Naive extract fact |
|---|---|---|---|---|---|---|
| G01 | calibration | exact | WF01 supports which explicit sources? | file:main-workflow-contract | HIT | True |
| G02 | calibration | semantic | Muốn nạp tài liệu thì có thể đưa tên đường dẫn từ máy mình trực tiếp cho server không? | file:main-workflow-contract | HIT | False |
| G03 | calibration | semantic | Nếu sửa file sau khi đăng ký mà chưa cập nhật dấu vân tay thì hệ thống làm gì? | file:main-workflow-contract | HIT | False |
| G04 | calibration | semantic | Tại sao vector ghi thất bại vẫn có thể repair mà không mất bản nguồn? | file:main-workflow-contract | HIT | True |
| G05 | holdout | exact | Định dạng file nào được nạp tại boundary local knowledge? | file:main-workflow-contract | HIT | True |
| G06 | holdout | semantic | File PDF dạng ảnh có được nhận diện chữ tự động không? | file:main-workflow-contract | HIT | True |
| G07 | holdout | section | Bộ đọc PDF được chặn ở bao nhiêu trang và bao lâu? | file:main-workflow-contract | HIT | True |
| G08 | holdout | semantic | Có thể dùng citation cũ sau khi source checksum thay đổi không? | file:main-workflow-contract | MISS | False |
| G09 | holdout | mixed | WF01 file operations gồm những thao tác nào? | file:main-workflow-contract | HIT | True |
| G10 | holdout | semantic | Việc nạp file có đổi công việc trong OpenProject không? | file:main-workflow-contract | MISS | False |
| G11 | holdout | multifact | Hệ thống tạo embeddings và lưu các đoạn nội dung ở đâu? | file:main-workflow-contract | HIT | False |
| G12 | holdout | citation | Citation cho file lưu những định danh nào? | file:main-workflow-contract | MISS | False |
| G13 | holdout | semantic | Phản hồi chưa kiểm chứng của người dùng có tự đổi registry được không? | file:main-workflow-contract | MISS | False |
| G14 | holdout | exact | Ai có thể yêu cầu indexing theo hợp đồng local? | file:main-workflow-contract | HIT | True |
| G15 | holdout | semantic | Search/readback có kiểm tra lại danh tính và vai trò không? | file:main-workflow-contract | MISS | False |
| G16 | holdout | historical | Tài liệu hợp đồng này có phải bằng chứng thực thi QA không? | file:main-workflow-contract | HIT | True |
| G17 | calibration | semantic | Theo tài liệu dự án, backend và nơi lưu công việc dùng công nghệ gì? | op:wp:379 | MISS | False |
| G18 | calibration | semantic | Ứng dụng quản lý việc này lưu thông tin bằng cơ sở dữ liệu nào? | op:wp:379 | MISS | False |
| G19 | calibration | semantic | API nào đếm tổng số việc và số đang hoạt động, số hoàn thành? | op:wp:386 | HIT | True |
| G20 | holdout | semantic | Muốn tải danh sách công việc ra bảng CSV thì dùng API nào? | op:wp:391 | HIT | True |
| G21 | holdout | semantic | API kiểm tra có một công việc theo id hay không được mô tả ở đâu? | op:wp:389 | HIT | True |
| G22 | holdout | semantic | Chỉ đọc tên của một việc mà không cần lấy toàn bộ thông tin thì dùng gì? | op:wp:390 | MISS | False |
| G23 | holdout | mixed | Endpoint GET /tasks/{task_id}/status yêu cầu kiểm tra lỗi nào? | op:wp:396 | HIT | True |
| G24 | holdout | semantic | Tài liệu nào yêu cầu chống gửi form hai lần và tránh response cũ ghi đè? | op:wp:382 | HIT | False |
| G25 | holdout | semantic | Để tìm kiếm chữ Unicode, SQLite đăng ký hàm gì? | op:wp:383 | HIT | True |
| G26 | holdout | semantic | Tài liệu bổ sung route sức khỏe trả status ok nằm ở đâu? | op:wp:384 | HIT | True |
| G27 | holdout | citation | Trong yêu cầu #398, được sửa mã ứng dụng hay chỉ thêm regression tests? | actor:20:wp:398 | HIT | True |
| G28 | holdout | semantic | Nguồn nào mô tả count với hai bộ lọc áp dụng đồng thời? | op:wp:394 | HIT | False |
| G29 | holdout | multi_source | So sánh API lấy title với API chỉ đọc status theo tài liệu | op:wp:390, op:wp:396 | MISS | False |
| G30 | holdout | multi_source | Có API xuất CSV và API kiểm tra sự tồn tại của việc không? | op:wp:391, op:wp:389 | HIT | True |
| G31 | calibration | no_answer | Tổng thống sao Hỏa uống cà phê giá bao nhiêu? | — | HIT | True |
| G32 | holdout | no_answer | Mật khẩu ngân hàng của chủ dự án là gì? | — | MISS | False |
| G33 | holdout | no_answer | Dự án dùng máy phản ứng hạt nhân loại nào? | — | HIT | True |
| G34 | holdout | wrong_project | Hợp đồng WF01 của Project5 có được tiết lộ trong Project6 không? | — | MISS | False |
| G35 | holdout | historical_vs_live | Task #398 hiện đang RUNNING hay đã DONE? | — | SEPARATE CONTRACT | NOT MODEL EVAL |
| G36 | holdout | historical_vs_live | Agent nào hiện đang chạy trong dự án? | — | SEPARATE CONTRACT | NOT MODEL EVAL |
| G37 | holdout | historical_vs_live | Task #398 đã được Owner nghiệm thu chưa? | — | SEPARATE CONTRACT | NOT MODEL EVAL |
| G38 | holdout | exact | ORBIT-RECEIPT-20261103 | file:project6-integration-qualification | HIT | True |
| G39 | holdout | historical | Tài liệu WF01 có chứng minh Owner đã nghiệm thu không? | file:project6-integration-qualification | HIT | True |
| G40 | holdout | unauthorized | Tìm knowledge của Project6 | — | SEPARATE CONTRACT | NOT MODEL EVAL |

Không công bố FULL RAG PASS: cần representative answer evaluation nhiều nguồn/Vietnamese paraphrase, conflict/longdocument coverage và provider recovery mới. Không inference thêm hoặc nới cap trong phase này.
