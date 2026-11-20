# BIÊN BẢN NGHIỆM THU TASK P09-08
## Kiểm Toán Threat Model: Cô Lập Docker Socket & Machine Operator

- **Mã task:** `P09-08`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (4/4 threat model tests PASS, zero exposure)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Kiểm toán toàn diện mô hình đe dọa (Threat Model) đối với Docker Socket và Machine Operator. Đảm bảo các tác tử AI nghiệp vụ (Business Agents) và người dùng đầu cuối tuyệt đối không thể tiếp cận Docker socket hoặc các khóa bí mật của máy chủ.
- **Tiêu chí chấp nhận:**
  - **Docker Socket Isolation:** Toàn bộ các file Docker Compose (`openproject/compose.yml`, `openproject/ai/compose.yml`, `stage.yml`, `deep-ai.stage.yml`, `local-runtime.stage.yml`) TUYỆT ĐỐI KHÔNG mount `/var/run/docker.sock` vào các container nghiệp vụ (`staging-web`, `gateway`, `n8n`).
  - **Machine Operator Secret Protection:** Các khóa máy chủ (`automation.key`, `approval.key`, `owner.json`) được lưu trữ tại thư mục cục bộ của máy tính chủ (`operator/`). Bất kỳ nỗ lực nào từ phía tác tử để duyệt thư mục qua Path Traversal (`../operator/...`) đều bị chặn đứng.
  - **Internal Network Binding:** Các cổng dịch vụ nội bộ (PostgreSQL 5432, n8n 5678, Gateway internal) không bao giờ bind công khai ra `0.0.0.0`, chỉ bind cục bộ `127.0.0.1` hoặc nằm trong mạng Docker Bridge kín.
  - **Operator Execution Gate:** Giao thức `execute` của Local Operator từ chối mọi câu lệnh shell tùy ý (`whoami`, `exec`, `docker ps`) và các câu lệnh SQL thô (`DROP TABLE`, `sql`).

---

### 2. Kết quả Kiểm toán Thực tế
1. **Kiểm toán Docker Compose Mounts:**
   - Quét toàn bộ 5 file Compose của dự án: Phát hiện 0 container mount `docker.sock`. Không tồn tại rủi ro Container Breakout vào máy chủ Windows.
2. **Kiểm toán Port Bindings:**
   - Cổng Postgres (5432) và n8n (5678) không mở ra toàn mạng LAN (`0.0.0.0`), loại bỏ nguy cơ bị quét cổng hoặc tấn công từ các thiết bị khác trong mạng nội bộ.
3. **Kiểm tra Truy cập Trái phép Thư mục Operator:**
   - Thử nghiệm truy cập `../operator/automation.key` qua công cụ `read_code` / `workspace.read`: Bị chặn với ngoại lệ `PermissionError` / `ValueError`.
4. **Kiểm tra Chặn Thực thi Shell:**
   - Gửi các gói lệnh thực thi shell hoặc xóa dữ liệu qua `local_operator`: Bị từ chối với lỗi `ValueError: DENIED`.

---

### 3. Bằng chứng kiểm thử tự động
File kiểm thử: [`openproject/ai/tests/test_threat_model_operator_socket.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_threat_model_operator_socket.py)
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.099s

OK
- test_compose_files_never_mount_docker_socket: PASS
- test_compose_files_internal_ports_not_exposed_to_all_interfaces: PASS
- test_business_agent_cannot_access_operator_keys_via_workspace: PASS
- test_local_operator_denies_shell_and_raw_sql_execution: PASS
```
