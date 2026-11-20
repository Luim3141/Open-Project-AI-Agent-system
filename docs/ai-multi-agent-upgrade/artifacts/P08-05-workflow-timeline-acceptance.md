# P08-05 ACCEPTANCE ARTIFACT: N8N WORKFLOW TIMELINE & UNIFIED TASK ID TRACE

> **Task ID:** P08-05  
> **Phase:** P08 — Control Center / quota / approval / local status  
> **Status:** DONE (100% Verified)  
> **Author:** Antigravity (Senior Full-Stack & DevOps Engineer)  
> **Date:** 2026-10-17  
> **Module:** [`openproject/ai/gateway/workflow_timeline.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/workflow_timeline.py)  
> **Tests:** [`openproject/ai/tests/test_control_center.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_control_center.py)

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC TRUY VẾT ONE TASK ID

Hệ thống thiết lập cơ chế liên kết dữ liệu truy vết duy nhất (One Task ID) xuyên suốt 4 tầng kiến trúc:
1. **n8n Community Workflow:** Trigger lịch trình (cron, webhook) với execution ID.
2. **Gateway Dispatcher:** Tiếp nhận yêu cầu, kiểm tra idempotency key và phân phối vào hàng đợi.
3. **Multi-Agent Runtime:** Thực thi tác vụ theo ExecutionPlan (Supervisor, PM, BA, DEV, QA, Reviewer).
4. **OpenProject Native Receipt:** Ghi nhận biên lai thay đổi nghiệp vụ hoặc phản hồi chỉ đọc.

Mọi sự kiện trong chuỗi đều mang cùng một `task_id`, `run_id` và `trace_id` trong bảng `audit` của `gateway.sqlite`.

---

## 2. TRUY XUẤT NGUỒN LỖI GẦN NHẤT (ERROR SOURCE DETECTION)

- Module tự động tổng hợp:
  - Cảnh báo workflow từ n8n (`store.workflow_alerts`).
  - Lỗi thực thi agent từ bảng `audit` (`outcome in ('error', 'denied', 'failed')`).
- Thời gian hiển thị được chuẩn hóa theo múi giờ địa phương **Asia/Bangkok (UTC+7)**.
- Phân loại rõ ràng trạng thái từng bước: `SUCCESS` hoặc `ERROR` kèm thông điệp lỗi cụ thể.

---

## 3. BẰNG CHỨNG KIỂM THỬ (TEST RESULTS)

- Test case: `ControlCenterTests.test_p08_05_workflow_timeline_and_errors`
- Kết quả: **PASS (100%)**
- 3 bước thực thi được liên kết chuẩn xác qua cùng một UUID `task_id`:
  - Bước 1: `task_dispatch` &rarr; `SUCCESS`
  - Bước 2: `agent_step_1` &rarr; `SUCCESS`
  - Bước 3: `agent_step_2` &rarr; `ERROR` (nhận diện chính xác `outcome: failed`)
