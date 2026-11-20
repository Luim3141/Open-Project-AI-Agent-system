# BIÊN BẢN NGHIỆM THU TASK P09-02
## RBAC Cross-Role Matrix 5 Roles × 9+ Tools Native / n8n / RAG

- **Mã task:** `P09-02`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (4/4 test matrix PASS, test_rbac.py 5/5 regression PASS)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Thiết lập và chứng minh ma trận phân quyền RBAC (Role-Based Access Control) chặt chẽ xuyên suốt 5 vai trò (PM, BA, FE, BE, QA) trên 9+ công cụ nghiệp vụ bao gồm: Native mutation, Proposal generation, Comments, Permissions query, Assistant status, Action history, và RAG/Knowledge search.
- **Tiêu chí chấp nhận:**
  - Quy tắc bất biến **PM-only-write**: 100% hành vi thay đổi dữ liệu OpenProject (`create_work_package`, `update_work_package`, `transition`, `change_gate`, `propose_operation`, `write_code`, `request_test`) chỉ được cấp phép cho role `PM`. Bất kỳ yêu cầu nào từ role non-PM (`BA`, `FE`, `BE`, `QA`) đều bị từ chối triệt để (`PermissionError: PM_REQUIRED` / `403 Forbidden`).
  - Toàn bộ 5 vai trò được phép gửi bình luận (`comment`), nhưng bình luận bị kiểm soát chặt chẽ: không được phép chứa các trường thay đổi dữ liệu (`changes`, `status_id`, `operation`, `value`), nếu phát hiện sẽ chặn đứng với `ValueError`.
  - Các công cụ đọc (`get_permissions`, `get_assistant_status`, `get_action_history`) cho phép 5 roles truy cập an toàn, phản ánh đúng danh sách quyền mà không làm rò rỉ công cụ bị cấm.
  - Hỗ trợ mô hình 20 người dùng cùng mạng LAN (`MAX_ACTIVE_USERS=20`), cho phép nhiều người cùng một role (ví dụ: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA) với phiên làm việc và định danh actor độc lập, bảo đảm zero privilege escalation.

---

### 2. Ma trận Phân quyền Thực tế (Cross-Role Matrix)

| Công cụ / Thao tác | PM (Project Manager) | BA (Business Analyst) | FE (Frontend Dev) | BE (Backend Dev) | QA (Quality Assurance) |
|---|---|---|---|---|---|
| `create_work_package` | ✅ Cho phép (Proposal / Native) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) |
| `update_work_package` | ✅ Cho phép (Proposal / Native) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) |
| `transition` (Đổi Status) | ✅ Cho phép | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) |
| `change_gate` | ✅ Cho phép | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) | ❌ Chặn (`PM_REQUIRED`) |
| `delete_work_package` | ❌ Cấm hoàn toàn (Safe policy) | ❌ Cấm hoàn toàn | ❌ Cấm hoàn toàn | ❌ Cấm hoàn toàn | ❌ Cấm hoàn toàn |
| `comment` (Bình luận sạch) | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép |
| `comment` (Chứa mutation fields) | ❌ Từ chối (`ValueError`) | ❌ Từ chối (`ValueError`) | ❌ Từ chối (`ValueError`) | ❌ Từ chối (`ValueError`) | ❌ Từ chối (`ValueError`) |
| `get_permissions` | ✅ Cho phép (Đầy đủ) | ✅ Cho phép (Read-only) | ✅ Cho phép (Read-only) | ✅ Cho phép (Read-only) | ✅ Cho phép (Read-only) |
| `get_assistant_status` | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép | ✅ Cho phép |
| `get_action_history` | ✅ Xem lịch sử & project audit | ✅ Xem lịch sử bản thân | ✅ Xem lịch sử bản thân | ✅ Xem lịch sử bản thân | ✅ Xem lịch sử bản thân |

---

### 3. Bằng chứng kiểm thử tự động
1. **File test ma trận:** [`openproject/ai/tests/test_rbac_cross_role_matrix.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_rbac_cross_role_matrix.py)
```text
Ran 4 tests in 2.258s
OK
- test_cross_role_mutation_gate_matrix: PASS (100% mutation tools verified across 5 roles)
- test_comment_tool_allowed_for_all_roles_without_mutation_fields: PASS (Clean comments allowed, field injections rejected)
- test_read_tools_allowed_for_all_roles: PASS (Read tools accessible to all 5 roles)
- test_multi_user_per_role_isolation_up_to_20_users: PASS (20 distinct users across 5 roles maintain strict isolation)
```

2. **Kiểm thử hồi quy gốc:** [`openproject/ai/tests/test_rbac.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_rbac.py)
```text
Ran 5 tests in 12.743s
OK (All legacy native/mcp/broker RBAC assertions PASS 100%)
```
