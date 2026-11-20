# Báo Cáo Nghiệm Thu Task P05-10: Proposal Aggregation

**Mã Task:** P05-10  
**Giai đoạn:** Phase P05 — Multi-agent Supervisor + PM/BA/QA/DEV/Reviewer  
**Tiêu đề:** Proposal aggregation: mọi thay đổi nghiệp vụ phải theo actor PM + native preview/gates/receipts  
**Tiêu chí chấp nhận:** Test non-PM deny; PM approval scoped; readback accurate  
**Thời gian hoàn thành:** 2026-10-17  
**Người thực hiện:** Gemini (kế thừa từ Codex)  
**Trạng thái:** PASS (4/4 unit tests, 48/48 multi-agent suite tests)

---

## 1. Mục Tiêu & Phạm Vi Triển Khai

Proposal Aggregation là cơ chế chốt chặn bảo mật và phân quyền nghiêm ngặt nhất trong hệ thống QLDAPM Local V2, bảo đảm rằng bất kỳ đề xuất thay đổi nào xuất phát từ các tác nhân AI hoặc các thành viên trong nhóm đều phải tuân thủ chính sách PM-only-write:
1. **Tổng hợp đề xuất có cấu trúc (Structured Aggregation):**
   - Đóng gói các đề xuất sửa đổi công việc thành cấu trúc `AggregatedProposal`.
   - Sinh bản xem trước thay đổi trực quan (human-readable preview diff) chỉ rõ trước và sau khi thay đổi.
   - Băm định danh SHA256 (`preview_hash`) cố định để chống giả mạo hoặc thay đổi ngầm sau khi tạo.
   - Thiết lập thời gian sống hữu hạn (TTL = 15 phút), quá hạn sẽ tự động hết hiệu lực.
2. **Từ chối tuyệt đối các vai trò Non-PM (Strict Non-PM Denial):**
   - Các tài khoản không giữ vai trò PM (Actor 6: BA, Actor 8: BE, Actor 9: FE, Actor 10: QA) khi gọi duyệt hoặc thực thi đề xuất đều bị từ chối thẳng thừng với `PermissionError: PROPOSAL_APPROVAL_PM_ONLY`.
3. **Phê duyệt theo phạm vi giới hạn của PM (Scoped PM Approval):**
   - Chỉ duy nhất người dùng giữ vai trò PM mới có quyền phê duyệt đề xuất.
   - Phê duyệt bắt buộc khớp 100% `proposal_id` và `preview_hash`. Nếu hash bị sai lệch hoặc bản ghi đã hết hạn, hệ thống lập tức từ chối.
4. **Kiểm tra đọc lại chính xác (Accurate Readback Verification):**
   - Sau khi gửi yêu cầu `PATCH` đến OpenProject native, hệ thống lập tức thực hiện truy vấn đọc lại `native.package(id)`.
   - Xác minh bắt buộc: `lockVersion` phải tăng đúng +1, và toàn bộ giá trị các trường sửa đổi phải khớp chính xác với dữ liệu đọc lại.
   - Phát hành biên bản áp dụng thành công (Audit Receipt) lưu vết vào database SQLite.

---

## 2. Thiết Kế & Mã Nguồn

- Module nghiệp vụ: `openproject/ai/gateway/proposal_aggregation.py`
  - Model `AggregatedProposal`: Pydantic model lưu trữ metadata đề xuất.
  - Hàm `aggregate_mutation_proposal()`: Tổng hợp thay đổi, sinh diff, tính hash SHA256 và lưu vào bảng `proposals`.
  - Hàm `approve_and_execute_proposal()`: Chặn non-PM, kiểm tra hash, gọi API native, xác minh readback và cập nhật biên bản thành công.
- Triết lý **Ponytail**: Tận dụng trực tiếp bảng `proposals` và `Store` hiện hữu, 0 dependency mới.

---

## 3. Bằng Chứng Kiểm Thử

File kiểm thử: `openproject/ai/tests/test_proposal_aggregation.py`

| STT | Test Case | Mô Tả & Điều Kiện Kiểm Chứng | Kết Quả | Thời Gian |
|---|---|---|---|---|
| 1 | `test_aggregate_mutation_proposal_creates_valid_structure` | Tổng hợp thay đổi từ BE (Actor 8) thành đề xuất hợp lệ, sinh preview diff và mã hash SHA256. | **PASS** | 0.001s |
| 2 | `test_non_pm_actors_strictly_denied_from_approving` | Xác minh 4 vai trò non-PM (BA: 6, BE: 8, FE: 9, QA: 10) đều bị từ chối khi duyệt đề xuất. | **PASS** | 0.001s |
| 3 | `test_pm_approval_scoped_and_readback_accurate` | PM (Actor 7) duyệt thành công, áp dụng thay đổi, kiểm tra lock_version tăng từ 4 lên 5 và các trường khớp 100%. | **PASS** | 0.370s |
| 4 | `test_stale_or_tampered_hash_fails_closed` | Đề xuất bị làm sai lệch hash hoặc stale lập tức bị từ chối với ValueError. | **PASS** | 0.001s |

**Tổng kiểm thử Proposal Aggregation:** 4/4 tests PASS (0.374s).  
**Hồi quy toàn bộ Multi-Agent Suite (9 modules):** 48/48 tests PASS (0.382s).
