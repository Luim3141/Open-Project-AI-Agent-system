# Báo Cáo Nghiệm Thu Task P05-03: PM Agent

**Mã Task:** P05-03  
**Giai đoạn:** Phase P05 — Multi-agent Supervisor + PM/BA/QA/DEV/Reviewer  
**Tiêu đề:** PM Agent: Sprint risks, work packages overdue, blocker, workload có evidence  
**Tiêu chí chấp nhận:** 5 golden cases PASS, không tự cập nhật task  
**Thời gian hoàn thành:** 2026-10-17  
**Người thực hiện:** Gemini (kế thừa từ Codex)  
**Trạng thái:** PASS (5/5 golden test cases, 315/315 regression tests)

---

## 1. Mục Tiêu & Phạm Vi Triển Khai

PM Agent là tác nhân chuyên biệt phụ trách phân tích quản lý dự án (Scrum/Sprint) trong kiến trúc Multi-Agent của QLDAPM Local V2, bao gồm:
1. **Phân tích công việc quá hạn (Overdue Work Packages):** Tính toán độ trễ (days overdue) so với mốc ngày khảo sát, trích dẫn ID và lock_version của từng work package.
2. **Phát hiện điểm nghẽn & phụ thuộc (Blockers & Dependencies):** Nhận diện các work package mang trạng thái `BLOCKED` hoặc có mô tả/tiêu đề chỉ thị bị chặn bởi work package khác; trích dẫn đầy đủ ID của cả task bị chặn và task gây cản trở.
3. **Đánh giá tải công việc (Workload Distribution):** Thống kê số lượng task đang mở của 5 vai trò LAN (PM, BA, BE, FE, QA), cảnh báo mất cân đối phân bổ tải mà không đưa ra xếp hạng cá nhân.
4. **Tổng hợp rủi ro giao hàng Sprint (Sprint Delivery Risk Synthesis):** Kết hợp các chỉ số overdue, blocker, tiến độ và tỷ lệ hoàn thành để đưa ra đánh giá rủi ro (CAO / TRUNG BÌNH / THẤP) đi kèm bằng chứng dữ liệu native xác thực.
5. **Quy tắc nghiêm ngặt KHÔNG tự ý cập nhật task (Strict No Self-Update):** PM Agent là tác nhân phân tích & tham vấn (advisory / read-only). Khi nhận chỉ thị sửa đổi dữ liệu (write intent), agent từ chối thực hiện trực tiếp, chuyển trạng thái về `REVIEW` và xuất bản thảo đề xuất (Proposal Draft) yêu cầu phê duyệt thủ công của PM theo đúng chính sách PM-only-write.

---

## 2. Thiết Kế & Mã Nguồn

- Module nghiệp vụ: `openproject/ai/gateway/pm_agent.py`
  - `analyze_overdue(packages, as_of_date)` -> Trả về danh sách quá hạn + `NativeReference(work_package_id, lock_version)`.
  - `analyze_blockers(packages)` -> Trích xuất điểm nghẽn + `NativeReference` cho cả task bị chặn và task chặn.
  - `analyze_workload(packages, user_map)` -> Phân bổ workload cho 5 vai trò LAN + `NativeReference` cho các task mở.
  - `analyze_sprint_risks(packages, as_of_date, user_map)` -> Đánh giá rủi ro Sprint mức độ CAO/TRUNG BÌNH/THẤP với bằng chứng chi tiết.
  - `PMAgent.run(task, scope, packages, as_of_date)` -> Điều phối thực thi, chặn write intent chuyển thành Proposal Draft, trả về `AgentResult`.
- Triết lý **Ponytail**: Tận dụng 100% các model Pydantic đã định nghĩa (`AgentTask`, `AgentResult`, `NativeReference`, `RunScope`), 0 dependency mới, 0 cuộc gọi Gemini tốn phí nếu chạy deterministic.

---

## 3. Bằng Chứng Kiểm Thử (5 Golden Cases)

File kiểm thử: `openproject/ai/tests/test_pm_agent.py`

| STT | Golden Case | Mô Tả & Điều Kiện Kiểm Chứng | Kết Quả | Thời Gian |
|---|---|---|---|---|
| 1 | `test_golden_case_1_overdue_work_packages_with_evidence` | Phát hiện 3 task quá hạn (#101, #102, #104), tính chính xác số ngày trễ, trích dẫn đúng lock_version, loại trừ task #105 đã DONE. | **PASS** | 0.001s |
| 2 | `test_golden_case_2_blockers_and_dependencies_with_evidence` | Nhận diện task #102 bị BLOCKED bởi task #101, trích dẫn cả hai mã native reference trong kết quả. | **PASS** | 0.001s |
| 3 | `test_golden_case_3_workload_distribution_and_imbalance` | Thống kê chính xác số lượng task mở cho 5 vai trò (BE: 2, FE: 1, QA: 1, BA: 0, PM: 0), kèm danh sách ID. | **PASS** | 0.001s |
| 4 | `test_golden_case_4_sprint_delivery_risk_synthesis` | Đánh giá tổng hợp rủi ro Sprint mức độ "CAO" dựa trên sự tồn tại đồng thời của blocker và nhiều task trễ hạn. | **PASS** | 0.001s |
| 5 | `test_golden_case_5_strict_refusal_of_self_updating_tasks` | Nhận lệnh "Cập nhật hạn chót và đổi trạng thái sang DONE", từ chối mutation, trả trạng thái `REVIEW`, xuất Proposal Draft trích dẫn #101 lockVersion 3. | **PASS** | 0.001s |

**Tổng kiểm thử PM Agent:** 5/5 tests PASS (0.003s).  
**Hồi quy toàn bộ hệ thống Gateway:** 315/315 tests PASS (126.075s).
