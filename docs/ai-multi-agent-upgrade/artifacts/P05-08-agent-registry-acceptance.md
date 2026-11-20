# Báo Cáo Nghiệm Thu Task P05-08: Agent Registry

**Mã Task:** P05-08  
**Giai đoạn:** Phase P05 — Multi-agent Supervisor + PM/BA/QA/DEV/Reviewer  
**Tiêu đề:** Agent registry gồm role/tool/model limits per agent, default Gemini shared  
**Tiêu chí chấp nhận:** Một Gemini project chạy nhiều agent nhưng tuân thủ quota chung  
**Thời gian hoàn thành:** 2026-10-17  
**Người thực hiện:** Gemini (kế thừa từ Codex)  
**Trạng thái:** PASS (5/5 unit tests, 39/39 multi-agent suite tests)

---

## 1. Mục Tiêu & Phạm Vi Triển Khai

Agent Registry đóng vai trò là danh bạ trung tâm quản lý toàn bộ 6 tác nhân chuyên biệt trong kiến trúc Multi-Agent của QLDAPM Local V2:
1. **Danh bạ 6 tác nhân định danh đầy đủ:**
   - `supervisor`: Điều phối tổng thể, lập kế hoạch tác vụ (Plan DAG) và tổng hợp proposal.
   - `pm`: Quản lý tiến độ dự án, rủi ro Sprint, công việc quá hạn và khối lượng tải (workload).
   - `ba`: Phân tích nghiệp vụ, chuẩn hóa User Stories, tiêu chí chấp nhận (AC) và phát hiện mơ hồ.
   - `dev`: Phân tích kỹ thuật, phân rã FE/BE, hợp đồng API và rủi ro kiến trúc/đồng thời.
   - `qa`: Bảo đảm chất lượng, thiết kế ca kiểm thử, phát hiện khoảng trống hồi quy và triage lỗi.
   - `reviewer`: Kiểm định độc lập, đối chiếu bằng chứng native, phát hiện xung đột và rà soát RBAC.
2. **Tuân thủ một quota chung (Single Shared Project Quota):**
   - Tất cả 6 tác nhân đều sử dụng cấu hình provider `gemini-shared`, cấm tạo pool quota riêng.
   - Mọi cuộc gọi mô hình đều đi qua Central Quota Limiter đã kiểm chứng (15 RPM, 500 RPD, 250,000 TPM) từ P02-05.
   - Giới hạn số lượt gọi (max_turns <= 2) và token tối đa (<= 2000 - 4000) được áp đặt chặt chẽ cho từng tác nhân.
3. **Phân quyền công cụ theo nguyên tắc đặc quyền tối thiểu (Least Privilege Tool Allowlists):**
   - Từng agent chỉ được phép gọi danh mục công cụ/hành vi được cấp phép.
   - DEV Agent bị cấm hoàn toàn lệnh shell, terminal, git clone và web research.
   - PM Agent bị cấm tự ý gọi API cập nhật công việc (`update_work_package`).
   - BA Agent bị cấm tự ý tạo công việc (`create_work_package`).
   - QA Agent bị cấm tự ý chuyển trạng thái (`transition`).
   - Reviewer Agent bị cấm tự động phê duyệt mù quáng (`auto_approve`).

---

## 2. Thiết Kế & Mã Nguồn

- Module nghiệp vụ: `openproject/ai/gateway/agent_registry.py`
  - Model `AgentDefinition`: Pydantic model kiểm định định dạng cấu hình chặt chẽ (extra="forbid").
  - `SupervisorHandler`: Điều phối kế hoạch qua `plan_request`.
  - Class `AgentRegistry`: Cung cấp `list_agents()`, `get_agent(name)`, và `get_handler(name)`.
  - Hàm `get_agent_registry()`: Singleton cung cấp quyền truy cập toàn cục.
- Triết lý **Ponytail**: Tận dụng 100% các class specialist agents đã triển khai ở P05-03, P05-04, P05-05, P05-06, P05-07, không bổ sung thư viện bên ngoài.

---

## 3. Bằng Chứng Kiểm Thử

File kiểm thử: `openproject/ai/tests/test_agent_registry.py`

| STT | Test Case | Mô Tả & Điều Kiện Kiểm Chứng | Kết Quả | Thời Gian |
|---|---|---|---|---|
| 1 | `test_all_six_agents_registered` | Đăng ký đầy đủ và chính xác 6 tác nhân (`supervisor`, `pm`, `ba`, `dev`, `qa`, `reviewer`). | **PASS** | 0.000s |
| 2 | `test_all_agents_share_single_central_gemini_quota` | Xác minh tất cả agent đều dùng `provider="gemini-shared"`, `shares_central_quota=True`, `max_turns <= 2`. | **PASS** | 0.000s |
| 3 | `test_strict_tool_allowlists_per_agent` | Xác minh danh mục công cụ cho phép của từng agent tuân thủ đặc quyền tối thiểu (chặn shell/clone, chặn direct writes). | **PASS** | 0.000s |
| 4 | `test_instantiate_agent_handler_returns_singleton_or_fresh_handler` | Xác minh `get_handler(name)` trả về instance xử lý hợp lệ có method `run`. | **PASS** | 0.000s |
| 5 | `test_unknown_agent_lookup_fails_closed` | Tìm kiếm tác nhân không tồn tại lập tức fail-closed với ValueError. | **PASS** | 0.000s |

**Tổng kiểm thử Agent Registry:** 5/5 tests PASS (0.000s).  
**Hồi quy toàn bộ Multi-Agent Suite (7 modules):** 39/39 tests PASS (0.014s).
