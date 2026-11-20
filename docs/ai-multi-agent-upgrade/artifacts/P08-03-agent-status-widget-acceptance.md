# P08-03 ACCEPTANCE ARTIFACT: REAL AGENT RUNTIME STATUS WIDGET (ZERO FAKE ONLINE)

> **Task ID:** P08-03  
> **Phase:** P08 — Control Center / quota / approval / local status  
> **Status:** DONE (100% Verified)  
> **Author:** Antigravity (Senior Full-Stack & UI/UX Architect)  
> **Date:** 2026-10-17  
> **Module:** [`openproject/ai/gateway/agent_status.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/agent_status.py)  
> **Tests:** [`openproject/ai/tests/test_control_center.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_control_center.py)

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC ĐO LƯỜNG THỰC TẾ

Widget trạng thái Agent đo lường trạng thái vận hành thực tế từ database `gateway.sqlite` và bộ ngắt mạch Google Gemini:
- **Tuyệt đối không fake trạng thái "Online":** Nếu Docker hoặc database store offline, trạng thái lập tức báo `RUNTIME_DOWN` (fail-closed).
- **Trạng thái thực tế:**
  1. `ACTIVE`: Agent đang có lượt chạy `RUNNING` được kết nối trong `agent_runs`.
  2. `WAITING_QUOTA`: Hàng đợi bị giữ do chạm ngưỡng 15 RPM hoặc 500 RPD.
  3. `BLOCKED_KEY_OR_MODEL`: Provider bị ngắt mạch (`store.gemini_block`).
  4. `ERROR`: Lượt chạy gần nhất (30 phút qua) kết thúc với trạng thái `FAILED`.
  5. `IDLE`: Không có tác vụ đang xử lý, sẵn sàng nhận yêu cầu mới.

---

## 2. DỮ LIỆU ĐO LƯỜNG & TỔNG HỢP

- Báo cáo tổng thể gồm 6 chuyên viên AI: `supervisor`, `pm`, `ba`, `dev`, `qa`, `reviewer`.
- Bảng tổng hợp số lượng: `total_agents`, `active`, `idle`, `waiting_quota`, `blocked`, `error`.
- Bằng chứng kiểm thử: Khi seed một tác vụ `RUNNING` cho `ba_agent`, trạng thái của BA chuyển ngay sang `ACTIVE` (`active_runs: 1`), các agent còn lại giữ `IDLE`. Khi kích hoạt ngắt mạch `store.block_gemini()`, toàn bộ 6 agents chuyển sang `BLOCKED_KEY_OR_MODEL` với lý do rõ ràng.

---

## 3. BẰNG CHỨNG KIỂM THỬ (TEST RESULTS)

- Test case: `ControlCenterTests.test_p08_03_agent_runtime_states`
- Kết quả: **PASS (100%)**
- Zero fake status; fail-closed khi môi trường gặp sự cố.
