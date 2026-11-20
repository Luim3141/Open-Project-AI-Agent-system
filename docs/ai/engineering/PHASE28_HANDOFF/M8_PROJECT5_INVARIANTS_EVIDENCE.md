# BẰNG CHỨNG KIỂM CHỨNG MILESTONE 8: PROJECT 5 INVARIANT RE-VERIFICATION (FINDING E)

**Thời gian kiểm chứng:** 2026-10-30 23:09:47 (UTC+7)  
**Môi trường:** PostgreSQL Database `openproject` (`qldapm-openproject-db-1`)  
**Tệp baseline đối soát:** `docs/ai/engineering/project5_invariants_baseline.json`  
**Test script:** `tools/verify_project5_invariants.py`  

---

## 1. Mục tiêu kiểm chứng
Kiểm chứng tính bất biến tuyệt đối của Project 5 (`qldapm-local`):
- Trong toàn bộ quá trình thực thi Phase 2.8 (bao gồm khắc phục Scheduler, khôi phục Auto E2E trên Project 6, tạo WP #384, commit, PR #5, cập nhật n8n/Qdrant và kiểm thử trình duyệt), **Project 5 không bị tác động, không bị thay đổi bất kỳ bản ghi nào**.

---

## 2. Kết quả đối soát Deep Diff 7/7 Invariants

| Tiêu chí Invariant | Baseline (Milestone 0) | Trạng thái Live (Hiện tại) | Đánh giá | Ghi chú kỹ thuật |
| :--- | :--- | :--- | :---: | :--- |
| **Số lượng Work Package** | 341 | 341 | **PASS** | Không có WP nào bị tạo mới hay xóa |
| **Min Work Package ID** | 38 | 38 | **PASS** | ID khởi đầu bất biến |
| **Max Work Package ID** | 378 | 378 | **PASS** | WP mới (#379, #384) thuộc Project 6 |
| **Max Lock Version** | 4 | 4 | **PASS** | Không có bản ghi nào bị ghi đè hay sửa đổi |
| **Latest Updated At** | `2026-10-29T10:08:56Z` | `2026-10-29T10:08:56Z` | **PASS** | Đóng băng hoàn toàn về mặt thời gian |
| **Status Distribution** | `{'1': 340, '37': 1}` | `{'1': 340, '37': 1}` | **PASS** | Không chuyển trạng thái bất kỳ WP nào |
| **Members Count** | 5 (Users 19, 20, 21, 22, 23) | 5 (Users 19, 20, 21, 22, 23) | **PASS** | Không thay đổi phân quyền hay thành viên |

---

## 3. Log kiểm thử trực tiếp từ hệ thống

```text
=================================================================
VERIFYING PROJECT 5 INVARIANTS (FINDING E)
=================================================================

[PASS] Work Package Count: 341 == 341
[PASS] Min Work Package ID: 38 == 38
[PASS] Max Work Package ID: 378 == 378
[PASS] Max Lock Version (No modifications): 4 == 4
[PASS] Latest Updated At (Frozen in time): 2026-10-29T10:08:56Z == 2026-10-29T10:08:56Z
[PASS] Status Distribution: {'1': 340, '37': 1} == {'1': 340, '37': 1}
[PASS] Members Count: 5 == 5

-----------------------------------------------------------------
OVERALL INVARIANT VERIFICATION: >>> ALL 7 INVARIANTS HELD UNTOUCHED <<<
-----------------------------------------------------------------
```

**Kết luận Milestone 8: PASS 100%.**
