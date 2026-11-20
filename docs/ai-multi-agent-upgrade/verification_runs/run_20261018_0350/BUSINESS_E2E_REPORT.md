# BÁO CÁO KIỂM THỬ E2E NGHIỆP VỤ & PHÂN QUYỀN (BUSINESS E2E & RBAC SUITE)
**Verification Run:** `run_20261018_0350`  
**Timestamp:** 2026-10-18T03:56:00+07:00  
**Test Suite:** `scripts/test_business_e2e_suite.py`  
**Trạng thái:** 6/6 PASS (100%)

---

## 1. Mục tiêu Kiểm thử
Xác minh toàn diện các luồng nghiệp vụ trên hệ thống QLDAPM Multi-Agent:
1. **CSP Integrity:** Loại bỏ triệt để cảnh báo CSP `connect-src '://'` trên giao diện OpenProject Staging.
2. **RBAC & Proposal Gating:** Ràng buộc quyền hạn theo vai trò (PM, BA-PM, BE, FE, QA) — chỉ PM mới có quyền phê duyệt thay đổi (mutation), các vai trò khác bị chặn (read-only/analyze-only).
3. **Supervisor Dispatch & Context Isolation:** Supervisor điều phối các agent chuyên trách (BA, QA, PM, Reviewer) thực thi tuần tự/song song mà không để rò rỉ ngữ cảnh (context bleed).
4. **Control Center State Serialization:** Trạng thái Control Center của AI Gateway serialize đầy đủ các khối `agent_registry`, `progress`, `task_tree`, `role_permissions`.
5. **Tool Isolation:** Công cụ nội bộ của nhà phát triển (`write_code`, `shell`) bị cách ly hoàn toàn khỏi business chat của người dùng.
6. **Security Boundaries:** Kiểm tra cơ chế fail-closed của CSRF protection và từ chối truy cập không xác thực (401).

---

## 2. Kết quả Thực thi Kiểm thử

```text
Ran 6 tests in 4.641s

OK
[PASS] CSP connect-src verified: zero invalid '://' tokens found.
[PASS] Role permissions contract verified: PM-only write strictly enforced, non-PM blocked.
[PASS] Supervisor dispatched cleanly to BA, QA, PM, Reviewer agents with zero context bleed.
[PASS] Control Center state serialization verified (agent_registry, progress, task_tree, role_permissions).
[PASS] Business chat tool isolation verified: zero operator/shell/write_code exposure.
[PASS] CSRF fail-closed rejection and unauthenticated 401 verified.
```

---

## 3. Chi tiết Từng Hạng mục & Khắc phục Lỗi

### A. Khắc phục Triệt để Cảnh báo CSP `connect-src '://'`
- **Nguyên nhân gốc rễ:** OpenProject Rails concern `dynamic_content_security_policy.rb` đọc thiết lập `Setting.collaborative_editing_hocuspocus_url` (mặc định là `"auto"`). Khi gọi `URI.parse("auto")`, phương thức trả về scheme nil và host nil, khiến chuỗi nội suy `#{uri.scheme}://#{host_with_port(uri)}` trở thành `"://"`. Trình duyệt khi tải trang phát hiện scheme không hợp lệ và phát cảnh báo trong DevTools console.
- **Giải pháp:** Cấu hình biến môi trường `OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL: ""` trong `openproject/ai/stage.yml` và `openproject/ai/automation/quick_tunnel_web.rb`.
- **Kết quả xác minh:** Lấy header `Content-Security-Policy` từ Staging Gateway/Web (`http://127.0.0.1:8080/login`), phân tích directive `connect-src`: chuỗi `://` đã hoàn toàn biến mất, không còn bất kỳ token scheme rỗng nào.

### B. Kiểm thử Ma trận Quyền hạn 5 Vai trò (RBAC Contract)
- **Cơ chế:** AI Gateway áp dụng bộ quy tắc kiểm tra vai trò người dùng trước khi thực thi bất kỳ đề xuất thay đổi nào (`can_mutate_business`).
- **Ma trận xác minh:**
  | Vai trò (Role) | Actor ID | Quyền Xem/Phân tích | Quyền Phê duyệt Thay đổi (Mutation) | Kết quả Kiểm thử |
  | :--- | :---: | :---: | :---: | :---: |
  | **PM** | 7 | Có | **ĐƯỢC PHÉP** (`is_pm: true, can_mutate: true`) | PASS |
  | **BA-PM** | 8 | Có | **BỊ CHẶN** (`is_pm: false, can_mutate: false`) | PASS |
  | **BE** | 9 | Có | **BỊ CHẶN** (`is_pm: false, can_mutate: false`) | PASS |
  | **FE** | 10 | Có | **BỊ CHẶN** (`is_pm: false, can_mutate: false`) | PASS |
  | **QA** | 11 | Có | **BỊ CHẶN** (`is_pm: false, can_mutate: false`) | PASS |
- Non-PM khi gửi lệnh thay đổi nhận được thông báo giải thích rõ ràng và bị từ chối ở tầng Gateway trước khi chạm vào OpenProject API.

### C. Điều phối Supervisor & Chống Tràn Ngữ cảnh (Zero Context Bleed)
- Supervisor tiếp nhận yêu cầu từ người dùng, lập kế hoạch DAG và ủy quyền cho 4 role agents:
  1. `ba`: Phân tích User Story và nghiệm thu tiêu chí (AC).
  2. `qa`: Xây dựng kịch bản kiểm thử biên và hồi quy.
  3. `pm`: Đánh giá tác động tiến độ và rủi ro.
  4. `reviewer`: Rà soát đối chiếu bằng chứng độc lập.
- Kết quả kiểm thử: Mỗi agent nhận một bounded context riêng biệt, không có hiện tượng chéo biến hoặc ghi đè kết quả của nhau (`COMPLETED` trạng thái độc lập).

### D. Serialization Trạng thái AI Control Center
- Endpoint và module `get_control_center_state` trả về cấu trúc dữ liệu chuẩn hóa:
  - `agent_registry`: Danh sách 6 agents chuẩn với giới hạn turn, toolset và provider.
  - `progress`: Tiến độ công việc theo phân trang an toàn (`limit`, `offset`, `total`).
  - `task_tree`: Cây tác vụ phân rã từ WBS.
  - `role_permissions`: Quyền hạn của actor hiện tại theo đúng context project.

### E. Cách ly Công cụ Nhà phát triển khỏi Business Chat
- Các công cụ nhạy cảm mức hạ tầng/code (`write_code`, `shell`, `docker exec`) hoàn toàn bị loại bỏ khỏi danh mục công cụ của Business Assistant.
- Business Assistant chỉ có quyền truy cập vào các công cụ nghiệp vụ: `analyze`, `list_work_packages`, `get_work_package`, `comment`, `propose_operation`.

### F. Kiểm tra Phòng vệ CSRF & Xác thực
- Gửi mutation request không kèm CSRF token hoặc token sai: Hệ thống kích hoạt fail-closed, trả về `403 Forbidden` / `ActionController::InvalidAuthenticityToken`.
- Truy cập tài nguyên bảo vệ mà không có session cookie hợp lệ: Trả về `401 Unauthorized`.
