# Second Brain — đánh giá trong đợt tích hợp 03/11/2026

Trạng thái: **CHƯA ĐẠT; candidate chưa triển khai MAIN**. Mục tiêu của Owner là Hit@5 ≥ 80%, false-positive rate ≤ 5%, citation/ACL/freshness chính xác và p95 truy vấn nóng ≤ 5 giây. Không được suy luận kết quả holdout từ kết quả dev dưới đây.

## Phạm vi và dữ liệu

Snapshot chỉ đọc gồm 12 tài liệu Native Project 6 có thể đọc bởi actor 20/PM; index và SQLite đánh giá được sao chép, Qdrant đánh giá chạy trong container riêng. `rag/eval/evaluation-plan.json` lưu manifest và hash cố định. Tập dev gồm 13 positive và 20 negative; tập holdout gồm 29 positive và 22 negative đã niêm phong, chưa chạy hay xem nội dung. Nhãn do một agent tạo và tự rà soát, chưa được reviewer độc lập hoặc con người xác nhận; các cặp VN/EN có tương quan, corpus Native nhỏ và trùng nguồn các đợt trước. Không coi đây là mẫu đại diện hay human ground truth.

Một sai sót trong lần thử dev: retrieval đưa cả 12 tài liệu vào context model, trong đó có các tài liệu thuộc document split của holdout. Câu hỏi và nhãn holdout vẫn chưa mở. Vì vậy holdout hiện tại chỉ có thể dùng như **câu hỏi mới trên nguồn đã xuất hiện khi phát triển**, không chứng minh khả năng với tài liệu chưa từng thấy. Muốn đánh giá document-unseen cần nguồn mới chưa dùng trong dev, được phân quyền, snapshot và gán nhãn độc lập trước khi chạy một lần với candidate đã khóa.

## Phép đo thực tế

| Phép đo trên dev | Hit@5 | False-positive rate | Citation identity errors | p95 | Kết luận |
|---|---:|---:|---:|---:|---|
| Gateway baseline, BGE-M3 + Qdrant clone | 2/13 = 15,4% | 1/20 = 5% | 0 | 0,396 s | Thiếu recall. |
| Qwen3 1.7B, top 5 nguồn và quote check | 8/13 = 61,5% | 2/20 = 10% | Chưa hoàn tất kiểm thử ACL/freshness | 7,281 s | Trượt cả ba ngưỡng; không deploy. |

Theo ngôn ngữ trên dev, baseline tìm đúng 1/6 câu positive tiếng Việt và 1/6 tiếng Anh; candidate thử nghiệm tìm đúng lần lượt 4/6 và 3/6, thêm 1/1 câu mixed. Các mẫu rất nhỏ và cùng ý định theo cặp nên không ngoại suy thành tỷ lệ tổng quát.

Thử nghiệm tách span và rerank mới trên cùng dev có document đúng trong top 5 cho 11/13 positive, nhưng chỉ 9/13 có đoạn chứa literal hỗ trợ; 19/20 negative vẫn có candidate vì pipeline này **chưa có abstention**. Đây là candidate retrieval, không phải FPR hay kết quả được phép trả cho người dùng. p95 0,4107 giây chỉ là lower bound cộng thời gian embedding/Qdrant và inference từng cặp, chưa gồm IPC/end-to-end hay tải đồng thời; bằng chứng `rag/span-dev-warm.json`. Candidate chưa đáp ứng gate và chưa deploy.

DEV8 post-hoc mở rộng passage pool: document đúng 13/13, selected supporting span vẫn 9/13; cả 20/20 negative đều có candidate vì chưa có abstention, **không phải FPR**. Warm p95 2,143 giây chỉ là lower bound, cold first query 13,48 giây; không gồm IPC và tải đồng thời. Labels vẫn tự rà soát, holdout queries/labels chưa mở. Bằng chứng `rag/span-dev8-relevance.json`; candidate không deploy.

Các file `rag/baseline-dev.json` và `rag/quote-candidate-dev.json` chứa số liệu từng case; mã chạy tương ứng nằm cùng thư mục. Quote nguyên văn chỉ chứng minh đoạn trích tồn tại, không tự chứng minh đoạn đó trả lời đầy đủ câu hỏi. Ứng viên chưa vượt các kiểm thử tiêm chỉ dẫn, source freshness, ACL hoặc local-file corpus; không dùng kết quả này làm acceptance.

Với implementation baseline đang phục vụ, 26 unit test local-file/ACL/search/retrieval PASS khi chạy trong image Gateway `3c065590` đã ghim dependency, network cách ly và source mount read-only. Lần chạy bằng Python Windows trước đó thất bại do môi trường dependency khác; kết quả container không chứng minh các case E2E hoặc chất lượng semantic của candidate.

Thử nghiệm theo từng passage bị dừng sớm vì latency vượt ngân sách: 1.7B có nhiều lượt 7–17 giây, 0.6B có sáu lượt đầu 9–19 giây. Qwen3 4B đạt 8/8 fixture synthetic nhưng benchmark dev chỉ hoàn tất 3/33 câu sau nhiều phút và được dừng để tránh tải kéo dài. Các phép thử bị dừng không phải kết quả benchmark đầy đủ. Model NLI lượng tử hóa và các probe synthetic trước đó được lưu dưới `rag/`; chưa chứng minh được tính answerability cho câu hỏi tự nhiên.

Một thí nghiệm **DEV post-hoc** khác dùng BGE/Qdrant snapshot và cross-encoder để xếp tối đa 8 span nguồn gốc/tài liệu (`rag/span-dev8-relevance.json`). Nó đưa đúng document vào top 5 cho 13/13 positive, nhưng span đứng đầu của document đúng chỉ chứa literal support ở 9/13 câu. Cả 20/20 negative đều có ứng viên vì pipeline không có bước abstain; đó **không phải FPR**, và document Hit@5 không chứng minh câu trả lời/citation được hỗ trợ. Warm p95 cộng các phép đo rời là 2,143 giây, chỉ là cận dưới vì chưa tính IPC/concurrency và chưa đo request end-to-end. Model chạy CPU1/network-none, peak 570.961.920 bytes. Các câu và nguồn đã được quan sát, nhãn chưa được thẩm định độc lập, holdout query vẫn niêm phong; không triển khai candidate này.

## Cần làm tiếp

Thiết kế lại bộ lọc answerability sao cho hiểu được phủ định, các constraint kỹ thuật và citation gốc mà vẫn giữ p95; kiểm thử dev và adversarial/ACL/freshness. Khi candidate và cấu hình đã cố định, reviewer độc lập rà lại nhãn holdout, rồi chạy đúng một lần; báo rõ số lượng, latency và mọi nhầm lẫn. Cần đánh giá local documents với ACL/citation riêng. Chỉ triển khai sau khi các gate thực sự đạt; không dùng dữ liệu holdout để tinh chỉnh.
