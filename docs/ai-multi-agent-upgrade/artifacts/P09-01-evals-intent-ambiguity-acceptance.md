# BIÊN BẢN NGHIỆM THU TASK P09-01
## Evals Tiếng Việt/English cho Multi-Intent, Ambiguity, và Stale Chat References

- **Mã task:** `P09-01`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (32/32 benchmark scenarios, Accuracy: 100.0%, 5 unit tests PASS)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Xây dựng bộ công cụ Evaluation (Đánh giá) và Golden Benchmark cho việc phân loại ý định (Intent), phát hiện câu lệnh đa ý định (Multi-Intent), phát hiện mơ hồ (Ambiguity), và giải quyết các tham chiếu ngữ cảnh trò chuyện cũ hoặc hết hạn (Stale Chat References) bằng cả tiếng Việt và tiếng Anh.
- **Tiêu chí chấp nhận:**
  - Có Golden Set đa dạng bao quát các tình huống thực tế nghiệp vụ quản lý dự án (SCRUM).
  - Không hardcode 100% từ prompt (sử dụng regex heuristics theo từ điển chuẩn mực, word boundaries, ngữ cảnh đối tượng OpenProject).
  - Phân tích và tách nhỏ câu lệnh đa ý định (Compound Multi-Intent) thành các `SubIntent` với agent và operation type tương ứng.
  - Phát hiện câu lệnh mơ hồ (`AMBIGUOUS_TARGET`) khi thực hiện hành động ghi/sửa mà không cung cấp ID hoặc đại từ không thể giải quyết.
  - Phát hiện tham chiếu bị trôi/lỗi thời (`STALE_REFERENCE`) khi `lock_version` của bản ghi trong database đã thay đổi so với ngữ cảnh bộ nhớ đệm.

---

### 2. Triển khai kỹ thuật
1. **Module Đánh giá `openproject/ai/gateway/intent_evals.py`:**
   - Hàm `evaluate_instruction_intent()`:
     - Phân giải đại từ quan hệ (song ngữ Việt/Anh: "task đó", "cái vừa rồi", "that ticket", "this work package").
     - Kiểm tra tính hợp lệ của tham chiếu: nếu không có ngữ cảnh hoặc `lock_version` không khớp -> đánh dấu `is_stale_reference = True`.
     - Kiểm tra tính mơ hồ (`is_ambiguous`): bắt các hành động thay đổi trạng thái/sửa đổi ("cập nhật", "update", "assign", "close", "gán") mà không có ID cụ thể hoặc tham chiếu hợp lệ.
     - Tách nhỏ Multi-Intent: phân tích liên từ ngữ pháp ("và", "and", "sau đó", "then", ";") có chặn ranh giới từ `\b`, phân bổ thành danh sách `SubIntent` với `target_agent` (PM, BA, QA, DEV) và `operation_type` (`READ_ONLY` vs `PROPOSAL_WRITE`).
2. **Cập nhật `conversation_memory.py`:**
   - Mở rộng `PRONOUN_PATTERN` hỗ trợ song ngữ hoàn chỉnh cả tiếng Việt và tiếng Anh: `(?:that|this)\s+(?:task|ticket|work\s*package|item|bug|issue)`.
3. **Golden Evaluation Benchmark Set (`GOLDEN_EVALS_SET`):**
   - Bao gồm 32 kịch bản phân loại:
     - 6 trường hợp Deterministic Read (đếm, liệt kê, kiểm tra trạng thái).
     - 6 trường hợp Complex Analysis Read (phân tích rủi ro, đánh giá tiêu chí AC, xem xét kiến trúc).
     - 6 trường hợp Proposal Write (tạo task, cập nhật trạng thái, gán người thực hiện).
     - 6 trường hợp Multi-Intent Compound (ghép đọc + ghi, BA + QA, PM + DEV).
     - 4 trường hợp Mơ hồ (Ambiguity thiếu ID hoặc thiếu mục tiêu thao tác).
     - 4 trường hợp Tham chiếu ngữ cảnh (hợp lệ vs hết hạn vs lệch `lock_version`).
4. **Hàm Chạy Benchmark `run_intent_evaluations()`:**
   - Xuất báo cáo đo lường độ chính xác (Accuracy), thời gian phản hồi (Latency trung bình < 0.1ms), và kết quả match/mismatch từng kịch bản.

---

### 3. Bằng chứng kiểm thử tự động
```text
[EVALS BENCHMARK] Total: 32, Passed: 32, Failed: 0, Accuracy: 100.0%
.....
----------------------------------------------------------------------
Ran 5 tests in 0.002s

OK
```
- Toàn bộ 5 bài test trong `openproject/ai/tests/test_intent_evals.py` PASS 100%.
- Không gây hồi quy (Zero regression) đối với `test_conversation_memory.py` (4/4 tests PASS).
