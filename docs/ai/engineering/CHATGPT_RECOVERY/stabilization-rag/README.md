# Semantic RAG benchmark — bản sao cô lập

Benchmark chẩn đoán ngày 2026-11-01, không phải nghiệm thu production. `results.json` chỉ chứa query có nhãn, native ID, thứ hạng và match type; không chứa nội dung tài liệu, vector hay credentials.

## Phương pháp

- Corpus: snapshot Project 6 đã sao chép trước đó, 135 vector points; 7 tài liệu thuộc actor 20 và role PM. Sáu positive VN/EN gắn expected native ID 383, 384 hoặc 386; sáu negative VN/EN được giả định không có câu trả lời trong corpus. Các nhãn negative mới chưa được người độc lập xác nhận.
- Dùng BGE-M3 local để embed query; cosine được tính trên toàn bộ vector snapshot rồi lấy tối đa `limit * 2` chunk theo project. Fixture mô phỏng vector transport, cố ý không thực thi role/actor/document filter: search engine phải hậu kiểm với SQLite clone và chunk hash. SQLite được sao chép vào temporary directory trước khi mở.
- Chạy `KnowledgeSearchEngine.search` thực với limit 10, actor 20 và document scope; kiểm tra riêng wrong role, wrong actor và empty scope. Đây không kiểm tra Qdrant ACL filter thực, native authorization, lock-version readback hay citation end-to-end. `READY` không chứng minh relevance hay citation.
- Ngưỡng 0,65 (hiện tại), 0,57 và 0,52 được cố định trong script trước lượt chạy đã lưu. Hai ngưỡng thử nghiệm được chọn từ các probe đã có, do đó không phải pre-registration độc lập hay holdout; không dùng bảng này để khẳng định calibration hoặc chọn ngưỡng production.
- Hit@k: expected ID xuất hiện trong k kết quả đầu trên 6 positive; false positive: negative có ít nhất một kết quả trên 6 negative. Một kết quả sai khác trong top-k của positive không được tính trong metric này.

## Kết quả lượt lưu

| Ngưỡng | Hit@1 | Hit@5 | Negative có kết quả |
| --- | ---: | ---: | ---: |
| 0,65 | 2/6 | 2/6 | 0/6 |
| 0,57 | 3/6 | 4/6 | 0/6 |
| 0,52 | 4/6 | 6/6 | 2/6 |

Wrong role, wrong actor và empty scope: mỗi trường hợp trả 0 kết quả. Lượt chạy trước của cùng script cho hit@1 = 3/6 tại 0,52; thứ hạng có thể biến động và chưa được điều tra. Những con số còn lại giống nhau. Chồng lấn positive/negative khiến việc hạ ngưỡng không an toàn; chỉ một dense hit cũng có thể cho phép partial lexical matches. Không thay source hoặc threshold theo benchmark này.

## Chạy lại

Từ repository root, với bản sao riêng chứa `knowledge.sqlite` và `source-vectors.json`, model BGE-M3 local có sẵn và Python environment của dự án:

```powershell
.\openproject\ai\.venv\Scripts\python.exe .\docs\ai\engineering\CHATGPT_RECOVERY\stabilization-rag\benchmark.py '<private-corpus-copy-directory>'
```

Không cung cấp đường dẫn MAIN: script đọc corpus đầu vào và chỉ tạo bản sao SQLite trong temporary directory, nhưng đọc file snapshot trực tiếp; local embedding service phải hoạt động. Script không lưu corpus hoặc vector vào output; nội dung kết quả vẫn có query và ID nên cần xử lý theo chính sách dữ liệu của dự án. Do model/runtime và thứ hạng tie có thể thay đổi, chạy lại không bảo đảm cùng thứ tự. Với kết quả đại diện cần nhãn và citation được adjudicate, corpus lớn hơn, tập calibration/holdout riêng và kiểm thử native authorization thực.
