# Frozen semantic candidate — REJECTED

Candidate không được triển khai. Development đạt Hit@5 24/24, negatives 0/20; locked holdout chỉ đạt 13/20 và nhận nhầm 14/20 negatives. Baseline serving trên cùng holdout đạt 3/20, negatives 0/20. Citation errors đo được bằng metadata/source snapshot: 0; không thay thế ACL/end-to-end acceptance.

Đánh giá dùng query embeddings BGE-M3 thực, SQLite snapshot và Qdrant clone thực, actor20/Project6. Nhãn do agent gán theo nguồn, cặp paraphrases có tương quan, chưa human adjudication. Vì vậy các tỷ lệ chỉ mô tả bộ này; không khẳng định chất lượng tổng quát.

Giữ nguyên `holdout-result.json`, `candidate-lock.json`, labels hash và source trong `rejected-candidate/`. Không sửa nhãn/ngưỡng theo holdout đã xem. `reject_candidate.py` đã khôi phục `knowledge_search.py` từ serving image, bỏ wiring candidate trong Service; baseline threshold0.65 giữ nguyên. Container Qdrant riêng của thử nghiệm đã được xóa sau khi xác minh ownership label; MAIN Qdrant không thay đổi.

M2 semantic acceptance vẫn **FAILED**. Exact lookup/citation và ingestion freshness là các khả năng riêng, không được dùng để đổi trạng thái này thành PASS. Một lần nghiên cứu tiếp cần dữ liệu/nhãn độc lập mới và thiết kế ranking/answerability khác; không tiếp tục tune trên holdout này.
