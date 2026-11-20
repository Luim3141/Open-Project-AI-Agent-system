# ACCEPTANCE REPORT: TASK P06-07 — DECISION MEMORY WITH PROVENANCE HASHING

- **Task ID:** `P06-07`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Lưu decision memory: thay đổi yêu cầu, lý do status/gate, rủi ro Sprint có provenance
- **Tiêu chí chấp nhận:** Chỉ source nội bộ, version/hash, ACL; không dữ liệu GitHub Research hay Internet crawl.
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T12:02:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/decision_memory.py` thực hiện ghi nhớ các quyết định quản lý và kiến trúc trọng yếu của dự án:

1. **Phân loại 3 nhóm quyết định chính (`DecisionType`):**
   - `SCOPE_CHANGE`: Thay đổi yêu cầu, thêm bớt tính năng hoặc điều chỉnh User Story.
   - `STATUS_GATE`: Lý do chuyển đổi trạng thái Work Package hoặc kết quả nghiệm thu Gate.
   - `SPRINT_RISK`: Nhận diện rủi ro tiến độ, tắc nghẽn kỹ thuật hoặc suy giảm năng lực tải trong Sprint.

2. **Truy nguyên nguồn gốc xuất xứ (Cryptographic Provenance):**
   - Mỗi bản ghi `DecisionRecord` lưu trữ đầy đủ `project_id`, `actor_id`, `native_id`, `lock_version`, tóm tắt `summary`, nguyên nhân `reason` và timestamp.
   - Hàm `compute_hash()` tạo mã băm SHA256 bảo đảm tính bất biến và toàn vẹn của lịch sử quyết định.

3. **Chốt chặn an toàn triệt để (Zero-Crawler Policy):**
   - Kiểm tra nghiêm ngặt `FORBIDDEN_CRAWL_PATTERN`: Từ chối lưu trữ mọi nội dung chứa URL internet, tên miền GitHub hoặc dữ liệu thu thập ngoài luồng.

4. **Kiểm soát Truy cập Phân quyền (Role-based ACL):**
   - Lọc dữ liệu quyết định theo vai trò `allowed_roles`. Các quyết định nội bộ nhạy cảm của PM không bị tiết lộ cho các vai trò kỹ thuật khác khi truy vấn.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_decision_memory.py`
- **Số test case:** 5/5 PASS (0.001s):
  1. `test_record_scope_change`: Ghi nhận thay đổi phạm vi nghiệp vụ có băm SHA256.
  2. `test_record_status_gate_transition`: Ghi nhận lý do chuyển trạng thái kèm lock_version.
  3. `test_record_sprint_risk`: Ghi nhận rủi ro Sprint với phân quyền PM-only.
  4. `test_reject_external_crawl_and_github`: Chặn đứng nội dung chứa URL internet hoặc GitHub.
  5. `test_query_decision_history_with_acl`: Kiểm chứng lọc phân quyền theo role và dự án.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/decision_memory.py`
- Tạo mới: `openproject/ai/tests/test_decision_memory.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-07-decision-memory-acceptance.md`
