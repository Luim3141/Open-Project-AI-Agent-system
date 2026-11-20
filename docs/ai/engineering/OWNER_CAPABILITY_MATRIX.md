# OWNER FULL PROJECT CAPABILITY MATRIX & AUTHORITY SPECIFICATION
**Phiên bản:** Phase 2.6 (2026-10-30)  
**Phạm vi áp dụng:** OpenProject Owner (User 18 — `AI_SYSTEM_OWNER`), Project Manager (User 20 — `PM`), Cross-Project Isolation (Project 5 vs Project 6).

---

## 1. Nguyên Tắc Phân Quyền Kiến Trúc (Architectural RBAC Principles)

1. **Owner Authority trên Project được cấp phép (Project 6):**
   - Tài khoản Owner (`User 18`, login `op-owner`, role `AI_SYSTEM_OWNER`) có toàn quyền giám sát, quản lý và điều khiển toàn bộ tính năng của AI Engineering trên Project 6 (`ai-dev-demo`).
   - Quyền của Owner tương đương và bao trùm quyền của PM (`User 20`), bao gồm việc kích hoạt, tạm dừng, hủy, khôi phục, đổi chế độ Auto và đối soát GitHub.
2. **Quyền chia sẻ hàng đợi và chống phân mảnh (Shared Queue & Nonce Deduplication):**
   - Hàng đợi thực thi (`ai_queue`, `ai_runs`, `engineering_control`) là duy nhất cho Project 6.
   - Các hành động của Owner và PM thao tác trên cùng một trạng thái bền vững (SQLite SSOT), chia sẻ lịch sử và deduplicate theo idempotency key / unit definition.
   - Owner có thể hủy (`cancel`) hoặc khôi phục (`resume`) các tác vụ do PM khởi tạo mà không bị từ chối quyền sở hữu cục bộ.
3. **Cô lập tuyệt đối dự án nghiệp vụ (Project 5 Absolute Isolation):**
   - Project 5 (`qldapm-local`): Toàn bộ 341 Work Packages nghiệp vụ được bảo vệ nghiêm ngặt.
   - Các lệnh AI Engineering (`engineering_*`) bị từ chối tuyệt đối trên Project 5 (Raise `PermissionError('ENGINEERING_CAPABILITY_REQUIRED')`).
4. **Từ chối an toàn đối với tài khoản không thuộc Project (Unauthorized User Isolation):**
   - Người dùng không thuộc Project 6 (như `User 19`) bị chặn hoàn toàn ở tầng RBAC (`403 Forbidden` / `IDENTITY_MISMATCH_OR_ADMIN_TOKEN`), không thể xem trạng thái, không thể gửi lệnh.

---

## 2. Ma Trận Quyền Hạn Chi Tiết (Capability Matrix)

| Danh Mục Thao Tác | Action Name | Mô Tả Nghiệp Vụ | Quyền Owner (User 18) | Quyền PM (User 20) | Người Dùng Khác (User 19) | Bằng Chứng Kiểm Thử |
|---|---|---|:---:|:---:|:---:|---|
| **Giám sát trạng thái** | `engineering_status` | Đọc toàn bộ dashboard, runs, backlog, worker, quota, github PRs | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_owner_can_execute_all_engineering_actions`, `test_unauthorized_user19_denied_on_project6` |
| **Điều khiển chế độ** | `engineering_control` | Chuyển đổi mode: `OFF`, `PAUSED`, `AUTO` | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_owner_can_execute_all_engineering_actions`, `test_control_auto_mode_accepted_for_pm_and_owner` |
| **Thực thi đơn lẻ** | `engineering_run_once` / `admit` | Đưa 1 backlog unit vào hàng đợi thực thi thật | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_owner_admit_shares_queue_with_pm_without_divergence` |
| **Lập kế hoạch WBS** | `engineering_plan` | Lập kế hoạch phân rã nhiệm vụ và nhận feedback | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_plan_cannot_invent_units_or_cyclic_dependencies` |
| **Hủy tiến trình** | `engineering_cancel` | Hủy run đang trong hàng đợi hoặc yêu cầu worker dừng | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_owner_admit_shares_queue_with_pm_without_divergence` |
| **Khôi phục tiến trình** | `engineering_resume` | Khôi phục run bị lỗi hoặc tạm dừng từ checkpoint | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_resume_denies_unknown_checkpoint_changed_revision` |
| **Đồng bộ GitHub** | `engineering_github_sync` | Kích hoạt 2-way sync giữa GitHub PRs và OpenProject WPs | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_reconcile_github_with_openproject_success_and_idempotency` |
| **Đọc vết thực thi** | `get_execution_monitor` | Xem trực quan biểu đồ phân rã của các Agent (PM, BA, Dev, Reviewer, QA) | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | `test_engineering_projection_uses_actual_role_receipts_in_existing_monitor_schema` |
| **Xem chi tiết Work Package** | `get_work_package` | Đọc thông tin WP cha (#379) và con (#380–#383) | **CHO PHÉP** | **CHO PHÉP** | Theo OpenProject View WP | `qldapm_ai_controller.rb:render_engineering` |
| **Báo cáo tiến độ** | `engineering_report` | Tạo báo cáo tiến độ Daily/Weekly/On-demand (M7) | **CHO PHÉP** | **CHO PHÉP** | **CHẶN (403)** | Sẽ kiểm chứng tại Milestone 7 |

---

## 3. Xác Minh Khả Năng Vận Hành Thực Tế (Live Verification Evidence)

1. **Khởi tạo và đối soát Scoped Service:**
   - Khi Owner gọi API với `project_id: 6`, gateway tự động khởi tạo Scoped Service cho Project 6.
   - Cấu hình người dùng của Scoped Service Project 6 là:
     ```json
     {
       "18": "AI_SYSTEM_OWNER",
       "20": "PM"
     }
     ```
   - User 18 được cấp capability `AI_SYSTEM_OWNER` chính thức, kiểm tra hợp lệ tại `identity['role'] == AI_SYSTEM_OWNER && actor == 18 && project_id in (5, 6)`.
2. **Khắc phục triệt để lỗ hổng hủy/khôi phục chéo (Cross-Actor Lifecycle Fix):**
   - Trước khi sửa: Khi PM (20) tạo run, hàm `cancel` và `resume` kiểm tra `WHERE actor=?` khiến Owner (18) bị lỗi `AGENT_RUN_NOT_FOUND` / `ENGINEERING_RUN_REQUIRED`.
   - Sau khi sửa: Trong Project 6, hàm `agent_run`, `cancel` và `resume` nhận diện quyền hạn của `AI_SYSTEM_OWNER` và kiểm tra quyền theo project scope (`json_extract(payload, '$.project_id') = 6`). Cả Owner và PM đều có thể quản lý trọn vẹn toàn bộ vòng đời của các tác vụ kỹ thuật.
3. **Bộ test tự động:**
   - Toàn bộ 5 test case trong `test_owner_project_authority.py` đã vượt qua 100% (`5/5 PASS`).
   - Tổng cộng 56/56 unit tests trong toàn bộ hệ thống kiểm thử kỹ thuật QLDAPM đều `PASS`.
