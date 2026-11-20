# CHANGE REQUEST: NÂNG NĂNG LỰC HỆ THỐNG TỪ 5 LÊN TỐI ĐA 20 NGƯỜI DÙNG (CR-USER-CAPACITY-20)

- **Mã Change Request:** `CR-USER-CAPACITY-20`
- **Ngày ban hành:** 2026-10-17
- **Người yêu cầu:** Chủ sở hữu hệ thống (Owner)
- **Kỹ sư phụ trách:** Gemini (Google Antigravity)
- **Trạng thái:** `IN_PROGRESS` (Đang triển khai & cập nhật kế hoạch)

---

## 1. Lý do thay đổi

Hệ thống QLDAPM Local Multi-Agent ban đầu được hoạch định cho một Scrum team cố định 5 người (mỗi vai trò PM, BA, FE, BE, QA đúng 1 người).
Trong thực tế triển khai dự án gia công phần mềm, đội ngũ phát triển cần mở rộng quy mô linh hoạt lên tới 20 thành viên với cơ cấu phân bổ nhiều người cho cùng một vai trò (ví dụ: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA). Do đó, hệ thống cần được nâng cấp để hỗ trợ từ 1 đến 20 tài khoản mà không làm xáo trộn kiến trúc local, bảo đảm an toàn dữ liệu và tuân thủ hạn mức Free Tier.

---

## 2. Phạm vi thay đổi

1. **Dung lượng người dùng:**
   - Hỗ trợ cấu hình linh hoạt từ 1 đến 20 tài khoản (`1 <= users <= 20`).
   - Tham số cấu hình chuẩn hóa: `MAX_ACTIVE_USERS = 20`.
2. **Cơ cấu vai trò (Multi-user per role):**
   - Hỗ trợ nhiều tài khoản cùng đảm nhiệm một vai trò (e.g., nhiều developer FE/BE hoặc QA).
   - Mỗi người dùng có định danh `actor_id`, session, project membership và quyền truy cập riêng.
3. **Phân tách các khái niệm tải đồng thời:**
   - *Registered Users:* 1–20 tài khoản trong hệ thống.
   - *Active Sessions:* 1–20 phiên đăng nhập LAN độc lập.
   - *Concurrent UI/API Requests:* Bounded bởi pool kết nối của Puma/OpenProject (pool=20) và Gateway Uvicorn.
   - *Concurrent AI Calls:* Bị giới hạn cứng ở mức 1 (hoặc tối đa 2) để tuân thủ 15 RPM của Gemini Free Tier.
   - *Queued AI Requests:* Xếp hàng điều phối công bằng trong SQLite durable queue.
4. **Loại bỏ các ràng buộc cứng:**
   - Xóa bỏ các điều kiện `len(users) == 5` trong mã nguồn Gateway và các kịch bản kiểm thử.

---

## 3. Các module bị ảnh hưởng

| Phân hệ / Module | Tệp nguồn bị ảnh hưởng | Nội dung điều chỉnh |
|---|---|---|
| Gateway Automation | `gateway/daily_brief.py` | Thay thế kiểm tra `len(targets) == 5` bằng `1 <= len(targets) <= MAX_ACTIVE_USERS`. |
| Gateway Store | `gateway/store.py` | Thay thế `EXACTLY_FIVE_ACTOR_REPORTS_REQUIRED` bằng điều phối động 1–20 báo cáo. |
| Gateway Operator | `gateway/local_operator.py` | Mở rộng kiểm tra danh sách `actors` từ `<= 5` lên `<= 20`. |
| Supervisor & Isolation | `gateway/supervisor_isolation.py` | Bổ sung hàm kiểm chứng cách ly và chia sẻ quota công bằng cho tối đa 20 actors. |
| n8n Workflow | `automation/workflows/*.json` | Nhận diện danh sách targets động theo dự án thay vì giả định 5 actors. |
| Kế hoạch & Tài liệu | `docs/ai-multi-agent-upgrade/*` | Cập nhật toàn bộ các task, acceptance criteria và runbook mạng LAN. |

---

## 4. Những yêu cầu BẮT BUỘC GIỮ NGUYÊN

1. **Mô hình bảo mật RBAC (PM-Only Write):**
   - Chỉ người dùng mang vai trò `PM` mới có quyền phê duyệt ghi nghiệp vụ (tạo/sửa Work Package, gán sprint, chuyển status).
   - Các vai trò khác (BA, FE, BE, QA) dù có bao nhiêu người cũng tuyệt đối chỉ có quyền đọc, phân tích, đề xuất (proposal draft) và bình luận (comment).
2. **Hạ tầng Local 0đ (Zero Incremental Spend):**
   - Chạy 100% trên máy Windows cục bộ qua Docker Desktop/WSL2.
   - Không Cloud VPS, không Kubernetes, không HA clustering, không Redis cluster.
   - Không tự ý bật billing, không dùng Gemini API trả phí. Toàn bộ 20 tài khoản dùng chung quota Gemini Free Tier của project đã xác minh.
3. **Nguồn sự thật nghiệp vụ:**
   - OpenProject và PostgreSQL tiếp tục là nguồn sự thật duy nhất cho dữ liệu dự án.
   - SQLite tiếp tục quản lý trạng thái Gateway, hàng đợi bền vững và audit log.

---

## 5. Đánh giá phần cứng máy chủ (Hardware Capacity Audit)

- **CPU:** 12th Gen Intel Core i5-12500H (12 Cores, 16 Threads) — Đủ khả năng xử lý mượt mà hàng trăm request HTTP/giây.
- **RAM:** Tổng 24.8 GB (Docker WSL2 cấp phát 11.54 GB, hiện chỉ dùng ~3.8 GB cho toàn bộ stack). Còn dư hơn 7.5 GB trong Docker engine, hoàn toàn đảm bảo cho 20 active sessions.
- **PostgreSQL Connection Pool:** Cấu hình trong `compose.yml` có `pool=20`, khớp hoàn toàn với 20 người dùng đồng thời.
- **Ổ đĩa:** Ổ D còn trống 280 GB; ổ C còn trống 29.8 GB.

---

## 6. Rủi ro & Giải pháp kiểm soát

| Rủi ro tiềm ẩn | Mức độ | Biện pháp kiểm soát |
|---|:---:|---|
| Cạnh tranh hạn mức Gemini Free giữa 20 người | Trung bình | Sử dụng thuật toán Fair-Queue / Round-Robin per-actor; ưu tiên interactive chat hơn background jobs; chuyển sang `WAITING_QUOTA` khi chạm trần. |
| Xung đột ghi đồng thời giữa 2 PM | Thấp | Kiểm tra `lock_version` bắt buộc (Optimistic Locking). Nếu xung đột, trả về HTTP 409 Conflict yêu cầu reload bản mới nhất. |
| Rò rỉ dữ liệu hoặc nhầm lẫn session giữa các user cùng role | Trung bình | Đánh khóa ngữ cảnh, cache và bộ nhớ theo bộ ba `(actor_id, project_id, conversation_id)` thay vì chỉ dựa vào role. |

---

## 7. Kế hoạch kiểm thử (Test Plan)

1. **Unit Tests:**
   - Tạo `tests/test_capacity_20_users.py`:
     - Kiểm chứng khởi tạo cấu hình 20 người dùng với nhiều user cùng vai trò (2 PM, 3 BA, 5 FE, 5 BE, 5 QA).
     - Kiểm chứng phân quyền RBAC: chỉ 2 tài khoản PM được phép duyệt proposal ghi, 18 tài khoản còn lại bị từ chối `PERMISSION_DENIED`.
     - Kiểm chứng tính cô lập của `ConversationMemory` và `DecisionMemory` giữa 20 actors (0 data leak).
     - Kiểm chứng hàng đợi công bằng `simulate_fair_quota_allocation` với 20 actors không ai bị bỏ đói (no starvation).
2. **Regression Tests:**
   - Toàn bộ 359 Gateway unit tests hiện có tiếp tục đạt 100% PASS.
   - Các bài test P04, P05, P06 duy trì tính toàn vẹn.

---

## 8. Kế hoạch Phục hồi (Rollback Plan)

- Nếu việc mở rộng gây ảnh hưởng đến tính ổn định của hệ thống:
  1. Khôi phục cấu hình Gateway `MAX_ACTIVE_USERS=5` trong `config.json`.
  2. Dữ liệu OpenProject hoàn toàn không bị ảnh hưởng vì không thay đổi schema DB nghiệp vụ.
  3. Rollback mã nguồn qua Git về commit HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`.

---

## 9. Trạng thái thực hiện

- [x] Đánh giá tài nguyên máy chủ local (CPU, RAM, Disk, Docker, DB Pool).
- [x] Ban hành ADR-0004 (`docs/adr/0004-user-capacity-scale-20.md`).
- [x] Soạn thảo Change Request chi tiết (`CHANGE_REQUEST_USER_CAPACITY_20.md`).
- [ ] Soạn thảo hướng dẫn cấu hình mạng LAN cho 20 người (`LAN_ACCESS_20_USERS.md`).
- [ ] Cập nhật mã nguồn Gateway (`daily_brief.py`, `store.py`, `local_operator.py`).
- [ ] Viết bộ test `test_capacity_20_users.py` và chạy kiểm thử 20 actors.
- [ ] Cập nhật kế hoạch tiến độ (`TASKS.json`, `IMPLEMENTATION_PLAN.md`, `PROGRESS_DASHBOARD.md`, `PROJECT_STATE.md`, `HANDOFF_CURRENT.md`).
