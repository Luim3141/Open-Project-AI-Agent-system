# BIÊN BẢN NGHIỆM THU TASK P09-10
## Hợp Đồng Cổng Phát Hành (Release Gate Contract) & Chặn Tự Động Promote Live

- **Mã task:** `P09-10`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (4/4 release gate tests PASS, zero auto-promote verified)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Định nghĩa và lập trình hóa cổng kiểm soát phát hành (Release Gate Contract) nghiêm ngặt nhằm bảo đảm hệ thống chỉ được xem xét phát hành khi thỏa mãn đầy đủ 4 tiêu chí cốt lõi: Diễn tập khôi phục (Restore drill), Tính tương đồng (Parity check), Đóng băng mã nguồn (Source freeze), và Phê duyệt tường minh từ Chủ dự án (Owner approval).
- **Tiêu chí chấp nhận:**
  - **Zero Auto-Promote Live:** Hệ thống TUYỆT ĐỐI KHÔNG tự động thăng cấp môi trường staging lên live/main (`can_auto_promote = False` trong mọi trường hợp đánh giá tự động).
  - **Restore Drill Evidence Gate:** Bắt buộc phải có bằng chứng diễn tập khôi phục thành công từ bản sao lưu gần nhất (`P09-05-backup-restore-drill-acceptance.md`) với xác nhận `PRAGMA integrity_check` = `ok`.
  - **Parity Check Gate:** Môi trường staging và release manifest phải khớp chính xác về chính sách `FREE_ONLY`, danh mục model miễn phí đã xác thực (`MODEL_ALLOWLIST.json`), và cấu hình `MAX_ACTIVE_USERS=20`.
  - **Source Freeze Gate:** Ghi nhận và cố định git commit SHA-1 tại HEAD và nhánh làm việc (`codex/local-multi-agent-upgrade`), bảo đảm không có thay đổi bất thường ngoài tầm kiểm soát.
  - **Human Owner Approval Boundary:** Trạng thái phát hành chỉ được chuyển sang `APPROVED` khi có Token phê duyệt rõ ràng từ người dùng (`OWNER_APPROVED_...`).

---

### 2. Thiết Kế & Thực Thi Cổng Phát Hành
Module trung tâm: [`openproject/ai/release_gate.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/release_gate.py)
Cung cấp các hàm kiểm tra tự động:
1. `check_restore_drill()`: Quét và xác thực biên bản diễn tập restore staging.
2. `check_parity()`: Xác thực chính sách Free-only và danh sách model miễn phí được ghim.
3. `check_source_freeze()`: Thu thập commit HEAD hiện tại và thông tin branch.
4. `check_owner_approval_gate()`: Ngăn chặn tự động promote, chỉ thông qua khi có token phê duyệt từ chủ sở hữu.
5. `evaluate_release_gates()`: Xuất cấu trúc `ReleaseGateAssessment` phục vụ việc ra quyết định trước Phase P10.

---

### 3. Bằng chứng kiểm thử tự động
File kiểm thử: [`openproject/ai/tests/test_release_gate.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_release_gate.py)
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.171s

OK
- test_restore_drill_gate_passes_with_existing_artifact: PASS
- test_parity_gate_verifies_free_models_allowlist: PASS
- test_source_freeze_records_git_commit: PASS
- test_auto_promotion_is_strictly_prohibited: PASS (can_auto_promote=False, human approval enforced)
```
