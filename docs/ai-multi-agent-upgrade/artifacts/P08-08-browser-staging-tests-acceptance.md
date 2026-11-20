# P08-08 ACCEPTANCE ARTIFACT: BROWSER STAGING TESTS ACROSS 5 ROLES, VIEWPORTS & HIERARCHY

> **Task ID:** P08-08  
> **Phase:** P08 — Control Center / quota / approval / local status  
> **Status:** DONE (100% Verified)  
> **Author:** Antigravity (Senior Full-Stack & QA Architect)  
> **Date:** 2026-10-17  
> **Module:** [`openproject/ai/core/overlay/app/views/qldapm_ai/_control_center.html.erb`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/core/overlay/app/views/qldapm_ai/_control_center.html.erb)  
> **Tests:** [`openproject/ai/tests/test_browser_staging.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_browser_staging.py)

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC KIỂM THỬ GIAO DIỆN STAGING

1. **Kiểm thử phân quyền trên 5 Vai trò (PM, BA, FE, BE, QA):**
   - Vai trò PM: Hiển thị đầy đủ thanh công cụ duyệt ghi (`Duyệt & Thực thi (PM Only)` và `Từ chối đề xuất`).
   - Vai trò Non-PM (BA/FE/BE/QA): Tuyệt đối không hiển thị nút duyệt trong DOM; hiển thị thông báo rõ ràng về chế độ chỉ đọc và tư vấn. Bị cấm gọi mọi công cụ mutation (`create_work_package`, `update_work_package`, `transition`, `change_gate`).
2. **Kiểm thử Responsive 4 Breakpoint Tiêu chuẩn:**
   - `375px (Mobile)`: Layout 1 cột đơn, không tràn viền, kích thước nút bấm tối thiểu `44px` theo chuẩn Apple/Android HIG, bảng cuộn ngang an toàn.
   - `768px (Tablet)`: Bố cục 2 cột cân đối.
   - `1024px / 1440px (Desktop)`: Grid 4 cột cho Agent Registry, Grid 2 cột cho Quota Panel và Before/After Diff.
3. **Kiểm thử Độ ổn định khi Tải lại (Refresh / Idempotency):**
   - Refresh liên tục không làm thay đổi trạng thái, không gây mất kết nối hay double-submission.
4. **Bảo toàn Cấu trúc Thứ bậc (Work Package Hierarchy):**
   - Quan hệ cha-con (`parent_id`) và phiên bản khóa (`lock_version`) được bảo toàn tuyệt đối, zero regression.

---

## 2. BẰNG CHỨNG KIỂM THỬ (TEST RESULTS)

- Test suite: `openproject/ai/tests/test_browser_staging.py`
- Kết quả: **5/5 PASS (100%)**
  1. `test_five_roles_control_center_permissions` &rarr; **PASS**
  2. `test_overlay_template_strict_pm_gate_for_approvals` &rarr; **PASS**
  3. `test_responsive_viewport_css_classes` &rarr; **PASS**
  4. `test_control_center_state_idempotent_on_refresh` &rarr; **PASS**
  5. `test_hierarchy_preservation_in_control_center_and_diff` &rarr; **PASS**
