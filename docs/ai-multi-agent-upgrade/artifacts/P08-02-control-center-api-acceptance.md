# P08-02 ACCEPTANCE ARTIFACT: READ-ONLY AGENT REGISTRY, TASK TREE & ACTOR-BOUND PROGRESS API

> **Task ID:** P08-02  
> **Phase:** P08 — Control Center / quota / approval / local status  
> **Status:** DONE (100% Verified)  
> **Author:** Antigravity (Senior Full-Stack & UI/UX Architect)  
> **Date:** 2026-10-17  
> **Module:** [`openproject/ai/gateway/control_center_state.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/control_center_state.py)  
> **Tests:** [`openproject/ai/tests/test_control_center.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_control_center.py)

---

## 1. YÊU CẦU & KẾT QUẢ ĐẠT ĐƯỢC

API Control Center State cung cấp dữ liệu read-only hợp nhất cho giao diện quản trị điều phối AI:
- **Agent Registry:** Danh mục đầy đủ 6 agents chuyên trách (`supervisor`, `pm`, `ba`, `dev`, `qa`, `reviewer`) kèm cấu hình định mức (`max_turns`, `max_tokens_per_call`), chia sẻ quota tập trung (`shares_central_quota: True`) và danh sách công cụ được phép (`allowed_tools`).
- **Progress:** Danh sách tiến độ các lượt chạy agent của actor hiện tại, phân trang đầy đủ (`limit`, `offset`, `next_offset`, `total`).
- **Task Tree:** Danh sách cây tác vụ của actor hiện tại (`get_agent_tasks_page`), hiển thị ID, agent thực hiện, trích đoạn chỉ thị, thời hạn và trạng thái hết hạn (`is_expired`).
- **Phân quyền vai trò (Role Permissions):** Báo cáo rõ quyền của người đang gọi (`is_pm: True` cho PM có quyền duyệt ghi, `is_pm: False` cho BA/FE/BE/QA chỉ đọc/tư vấn).

---

## 2. KIỂM CHỨNG CÁCH LY DỮ LIỆU TUYỆT ĐỐI (ZERO CROSS-USER LEAKAGE)

- **Actor 7 (PM):** Truy vấn trả về 3 tasks và 3 runs của chính Actor 7; hoàn toàn **không** chứa dữ liệu hoặc chỉ thị nhạy cảm của Actor 8 (`INSTRUCTION_FOR_ACTOR_8`).
- **Actor 8 (BE):** Truy vấn trả về 2 tasks và 2 runs của chính Actor 8; hoàn toàn **không** chứa dữ liệu hoặc chỉ thị nhạy cảm của Actor 7 (`INSTRUCTION_FOR_ACTOR_7`).
- **Phân trang an toàn:** `limit` giới hạn trong khoảng `1..50`, `offset >= 0`, fail-closed khi truyền tham số ngoài phạm vi.

---

## 3. BẰNG CHỨNG KIỂM THỬ (TEST RESULTS)

- Test case: `ControlCenterTests.test_p08_02_control_center_state_actor_bound_and_paginated`
- Kết quả: **PASS (100%)**
- HTTP status: `200 OK` tại `/api/v1/control-center/state`
- Contract JSON tuân thủ đầy đủ schema Pydantic/Starlette.
