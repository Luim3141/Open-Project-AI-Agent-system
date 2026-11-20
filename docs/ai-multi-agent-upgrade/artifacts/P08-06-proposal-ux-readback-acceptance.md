# P08-06 ACCEPTANCE ARTIFACT: PROPOSAL UX BEFORE/AFTER DIFF & NATIVE READBACK VERIFICATION

> **Task ID:** P08-06  
> **Phase:** P08 — Control Center / quota / approval / local status  
> **Status:** DONE (100% Verified)  
> **Author:** Antigravity (Senior Full-Stack & UI/UX Architect)  
> **Date:** 2026-10-17  
> **Module:** [`openproject/ai/gateway/proposal_ux.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/proposal_ux.py)  
> **Tests:** [`openproject/ai/tests/test_control_center.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_control_center.py)

---

## 1. MỤC TIÊU VÀ QUY TẮC BẢO VỆ DỮ LIỆU NGHIỆP VỤ

1. **Before/After Diff Trực quan:** So sánh chi tiết từng trường dữ liệu giữa trạng thái hiện tại (`current native work package`) và đề xuất mới (`proposed mutation`). Nhãn tiếng Việt rõ ràng (`Tiêu đề`, `Trạng thái`, `Người thực hiện`, `Hạn chót`).
2. **Tổng hợp đánh giá độc lập từ Reviewer Agent:** Tự động kiểm tra xung đột phiên bản (`lock_version`), kiểm tra quyền RBAC của người gửi yêu cầu. Cảnh báo và từ chối ngay (`REJECTED`) nếu vai trò không phải PM hoặc phiên bản bị cũ (`STALE_VERSION_CONFLICT`).
3. **Nguyên tắc bất biến: KHÔNG ĐÁNH DẤU THÀNH CÔNG TRƯỚC NATIVE READBACK:**
   - Hệ thống không bao giờ tin tưởng mã HTTP 200 đơn thuần từ API ghi mà bắt buộc phải đọc lại trực tiếp từ OpenProject (`native readback`).
   - Phân loại trạng thái biên lai (Receipts):
     - `SUCCEEDED`: 100% các trường thay đổi đã được xác nhận khớp trên OpenProject.
     - `PARTIAL_SUCCESS`: Chỉ một phần các trường cập nhật thành công (ví dụ đổi tiêu đề được nhưng đổi trạng thái bị chặn bởi workflow).
     - `PENDING_READBACK`: Chưa đọc lại được từ OpenProject; giữ trạng thái chờ xác minh.
     - `FAILED_READBACK`: Đọc lại cho thấy dữ liệu không hề thay đổi.

---

## 2. BẰNG CHỨNG KIỂM THỬ (TEST RESULTS)

- Test case: `ControlCenterTests.test_p08_06_proposal_diff_reviewer_summary_and_readback`
- Kết quả: **PASS (100%)**
- Kiểm chứng 3 kịch bản:
  - Khớp 100% &rarr; `SUCCEEDED` (verified: True)
  - Khớp 2/3 trường &rarr; `PARTIAL_SUCCESS` (verified: False, báo rõ trường `status` chưa khớp)
  - Chưa có dữ liệu native &rarr; `PENDING_READBACK` (verified: False)
  - Non-PM duyệt đề xuất &rarr; Bị từ chối ngay với mã lỗi `RBAC_VIOLATION`.
