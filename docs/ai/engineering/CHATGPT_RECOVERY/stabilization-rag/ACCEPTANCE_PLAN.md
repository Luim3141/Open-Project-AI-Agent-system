# Semantic retrieval — tiêu chí cho lần đánh giá tiếp theo

Trạng thái: **CHƯA ĐỦ BẰNG CHỨNG ĐỂ THAY POLICY**. Tài liệu này cố định tiêu chí trước khi chọn hoặc tuning giải pháp mới; không phải kết quả benchmark mới và không thay đổi runtime.

## Bộ dữ liệu

- Dùng snapshot riêng, bất biến, cùng corpus và model BGE-M3 local cho baseline và candidate; ghi hash snapshot, model/version và code. Không đọc hay ghi Project 5 để tạo bộ này.
- Thu thập tối thiểu 40 positive và 40 hard negative, mỗi nhóm gồm cả VN và EN; positive bao gồm paraphrase và exact match, negative gần nghĩa nhưng không được corpus trả lời. Một truy vấn có thể có nhiều tài liệu liên quan.
- Người am hiểu corpus xác nhận độc lập tất cả nhãn, bao gồm đọc đủ các chunk và kiểm tra nguồn; ghi nguồn, scope và lý do negative không có câu trả lời. Không đưa nội dung riêng tư vào báo cáo công khai. Nếu không thể xác nhận thì để `unjudged`, không tính là negative.
- Tách calibration và holdout theo nhóm ý định/tài liệu, giữ cả VN/EN và hai loại nhãn ở mỗi tập; tối thiểu 20 positive và 20 negative trong holdout. Không sử dụng holdout để chọn model, ngưỡng, fusion hoặc query rewrite. Chốt hash bộ dữ liệu và cấu hình trước lần đo holdout; nếu thay candidate sau khi xem holdout, cần holdout mới độc lập.

## Điều kiện chấp nhận đồng thời trên holdout

1. Hit@5 positive tăng ít nhất 10 điểm phần trăm so với baseline trên cùng truy vấn; Hit@1 và MRR@5 không giảm. Báo cáo cả số đếm và từng ngôn ngữ, không chỉ trung bình; mỗi ngôn ngữ không giảm Hit@5.
2. Tỷ lệ negative trả ít nhất một kết quả không tăng so với baseline và không vượt 5%; báo cáo từng ngôn ngữ. Mọi kết quả được tính, kể cả lexical được thêm bởi dense hit.
3. Exact match: không mất bất kỳ kết quả đúng ở top 1 so với baseline; kiểm tra cả VN/EN và khi dense unavailable.
4. Không có kết quả vượt project, role, actor hoặc document scope, kể cả empty scope và payload/chunk giả mạo; chạy test trên Qdrant filter thực trong môi trường disposable và kiểm tra lại authorization tại boundary native. Không được nới ACL hoặc bỏ kiểm tra hash/provenance.
5. Đánh giá citation: mọi kết quả được chấm đúng phải trỏ đúng tài liệu/chunk được phép và hỗ trợ câu trả lời; các lỗi attribution hay authorization đều chặn acceptance.
6. Báo cáo số lượng, confidence interval phù hợp cho các tỷ lệ, sai lệch giữa các lần chạy và các trường hợp chưa được adjudicate. Bộ nhỏ chỉ có thể hỗ trợ quyết định thử nghiệm; không chứng minh chất lượng production hoặc tỷ lệ lỗi bằng không.

Các ngưỡng trên là tiêu chí kỹ thuật đề xuất cho thử nghiệm tiếp theo, không phải cam kết thống kê hoặc chấp thuận triển khai. Nếu bất kỳ điều kiện nào không đạt hoặc không đo được, giữ policy hiện tại. Triển khai MAIN và thay đổi policy vận hành cần quy trình phê duyệt riêng.

## Bằng chứng hiện có

`README.md` và `results.json` trong thư mục này chỉ là diagnostic: 6 positive và 6 negative, nhãn negative chưa adjudicate, nhiều threshold đã thử trên cùng dữ liệu, thiếu holdout và citation/native authorization. Do đó không dùng chúng để chứng minh candidate vượt baseline. Ngày 2026-11-02 chạy `python -m unittest openproject.ai.tests.test_rag_recovery openproject.ai.tests.test_knowledge_storage -q` trong venv với `PYTHONPATH=.;openproject/ai`: 26 test PASS. Đây là test recovery/storage dùng fixture, không phải đo chất lượng semantic hay Qdrant/native ACL end-to-end.
