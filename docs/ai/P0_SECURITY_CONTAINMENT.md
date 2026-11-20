# BÁO CÁO NGHIỆM THU PHASE P0-A: SECURITY CONTAINMENT & ZERO-BYPASS ENFORCEMENT

**Dự án:** QLDAPM MAIN  
**Thời gian hoàn thành:** 2026-10-23T00:43:00+07:00  
**Người thực hiện:** AI Engineering Lead  
**Trạng thái:** VERIFIED (PASS 12/12 NEGATIVE SECURITY TESTS)  
**Tài liệu tham chiếu:** `docs/ai/INDEPENDENT_RELEASE_GATE_AUDIT.md`

---

## 1. MỤC TIÊU VÀ PHẠM VI
Khắc phục ngay lập tức các lỗ hổng bảo mật nghiêm trọng đã được chỉ ra trong Báo cáo Kiểm toán Độc lập:
1. Nguy cơ webhook bypass xác thực, tự ý ghi mutation vào OpenProject.
2. Nguy cơ client spoofing danh tính PM qua body JSON (`actor`, `role`, `is_pm`).
3. Nguy cơ approval giả mạo, replay attack, tampered payload, hoặc bypass 2-step confirmation.
4. Rà soát phạm vi mạng (Network Exposure) của n8n Main.

---

## 2. KẾT QUẢ RÀ SOÁT MẠNG & INGRESS (A1)

| Hạng mục kiểm tra | Bằng chứng thực tế (Command / Config) | Kết quả |
| :--- | :--- | :--- |
| **Docker HostConfig.PortBindings** | `docker inspect qldapm-n8n-main --format '{{json .HostConfig.PortBindings}}'`<br>Output: `{"5678/tcp":[{"HostIp":"127.0.0.1","HostPort":"5679"}]}` | **AN TOÀN** (Chỉ bind Loopback `127.0.0.1`, không bind `0.0.0.0`) |
| **Docker Network Attachment** | Thuộc 2 mạng nội bộ: `qldapm-ai_ai` (`172.28.0.4`) và `qldapm-openproject_frontend` (`172.22.0.8`). | **AN TOÀN** (Mạng cầu cô lập) |
| **Reverse Proxy / Ingress** | Quét toàn bộ Caddyfile, Nginx, Ngrok, Cloudflare Tunnel trong repo. Không có reverse proxy nào map vào port 5679. | **AN TOÀN** (Không bị lộ ra WAN) |
| **Windows Firewall** | Port 5679 chỉ lắng nghe trên localhost. | **AN TOÀN** |

---

## 3. KHÓA ĐƯỜNG GHI NGUY HIỂM (A2)

- **Workflow WF06 (Native API Execution - ID: `Jq18aFSqfuUybEic`)**:
  - **Trạng thái trước:** Active (`active: true`), webhook đón request ghi trực tiếp không có token bảo vệ.
  - **Hành động xử lý:** Đã gọi API n8n deactivation: `POST http://localhost:5679/rest/workflows/Jq18aFSqfuUybEic/deactivate`.
  - **Bằng chứng xác minh:** Gọi webhook `POST http://localhost:5679/webhook/qldapm-execute-mutation` -> Trả về `HTTP 404 (Webhook not registered)`. Toàn bộ đường ghi unauthenticated qua webhook đã bị triệt tiêu 100%.

---

## 4. CHỐT MÔ HÌNH XÁC THỰC VÀ BẢO MẬT (A3, A4)

Hệ thống Gateway `/api/v1/commands` hoạt động theo nguyên tắc **Zero-Trust Client Identity & Two-Phase Cryptographic Approval**:

1. **Định danh bắt buộc qua Bearer Token:**
   - Gateway hoàn toàn bỏ qua các trường do client tự khai báo trong JSON body như `actor`, `actor_id`, `role`, `is_pm`.
   - Danh tính và vai trò được truy xuất độc quyền từ bảng `tokens` trong SQLite qua hàm `store.authenticate(bearer)`.
   - Token giả, token thiếu hoặc token không khớp -> Bị trả về `HTTP 401 Unauthorized` ngay tại ingress.

2. **Cơ chế Phê duyệt 2 pha (Proposal -> Cryptographic Hash Confirmation):**
   - Mọi lệnh ghi (mutations: `create_work_package`, `update_work_package`, `comment`, `transition`, `change_gate`, `write_code`) khi gọi qua `execute()` **không bao giờ ghi trực tiếp**.
   - Gateway tự động chuyển lệnh thành một `Proposal` ở trạng thái `pending`, sinh mã băm SHA-256 duy nhất:
     $$\text{fingerprint} = \text{SHA256}(\text{canonical}(\{"actor": \text{actor\_id}, "command": \text{payload}\}))$$
   - Chỉ duy nhất PM (Actor 19) mới có quyền xác nhận phê duyệt qua hàm `confirm(actor, identifier, fingerprint)`.
   - Bảng `proposals` sử dụng transaction atomic:
     ```sql
     UPDATE proposals SET state='executing' 
     WHERE id=? AND actor=? AND hash=? AND state='pending' AND expires>?
     ```
   - Nếu hash sai, hết hạn (>900s), đã thực thi trước đó (reused), hoặc payload trong DB bị sửa đổi -> Giao dịch bị hủy ngay lập tức với lỗi `STALE_EXPIRED_OR_CONSUMED_PROPOSAL`.
   - Kiểm tra `lockVersion` OpenProject: Nếu Work Package đã bị thay đổi đồng thời bởi người khác -> Bị chặn với lỗi `STALE_WORK_PACKAGE`.

---

## 5. KẾT QUẢ BỘ KIỂM THỬ TIÊU CỰC (12 NEGATIVE SECURITY TESTS)

File thực thi: `openproject/ai/tests/test_p0_security_containment.py`  
Lệnh chạy: `openproject/ai/.venv/Scripts/python.exe -m unittest tests.test_p0_security_containment -v`  
Thời gian thực thi: 57.785 giây  
Kết quả: **12/12 PASS (100% OK, 0 Errors, 0 Failures)**

| STT | Test Name | Mục đích kiểm tra | Kết quả thực tế |
| :---: | :--- | :--- | :---: |
| **01** | `test_01_negative_no_token_rejected` | Request không gửi Header Authorization bị chặn `401` | **PASS** |
| **02** | `test_02_negative_fake_token_rejected` | Request gửi Bearer token giả mạo bị chặn `401` | **PASS** |
| **03** | `test_03_negative_pm_spoofing_in_json_ignored` | Request dùng token BA (Actor 20) cố tình gán `actor=19` trong JSON bị Gateway bỏ qua và từ chối với lỗi `PM_REQUIRED` | **PASS** |
| **04** | `test_04_negative_wf06_direct_call_blocked` | Gọi trực tiếp vào webhook WF06 chưa xác thực bị trả về `404` | **PASS** |
| **05** | `test_05_negative_proposal_not_found` | Confirm proposal ID không tồn tại bị từ chối `PROPOSAL_NOT_FOUND` | **PASS** |
| **06** | `test_06_negative_approval_fake_hash` | Confirm với fingerprint SHA-256 không khớp bị từ chối `STALE_EXPIRED_OR_CONSUMED_PROPOSAL` | **PASS** |
| **07** | `test_07_negative_approval_expired` | Confirm proposal đã quá hạn 15 phút bị từ chối `STALE_EXPIRED_OR_CONSUMED_PROPOSAL` | **PASS** |
| **08** | `test_08_negative_approval_reused` | Confirm proposal đã được claim/execute trước đó (chống Replay) bị từ chối `STALE_EXPIRED_OR_CONSUMED_PROPOSAL` | **PASS** |
| **09** | `test_09_negative_approval_payload_tampered` | Dữ liệu proposal bị can thiệp trái phép trong cơ sở dữ liệu làm sai lệch băm bị từ chối `STALE_EXPIRED_OR_CONSUMED_PROPOSAL` | **PASS** |
| **10** | `test_10_negative_stale_lock_version` | Mutation với `lockVersion` cũ bị từ chối `STALE_WORK_PACKAGE` | **PASS** |
| **11** | `test_11_negative_requester_not_pm` | Non-PM (Actor 20) cố tình gọi mutation trực tiếp bị từ chối `PM_REQUIRED` | **PASS** |
| **12** | `test_12_negative_direct_command_always_yields_proposal` | Lệnh ghi gửi vào `execute()` luôn trả về proposal ở trạng thái `pending`, giá trị `lockVersion` trên OpenProject thực hoàn toàn không suy suyển (0 side effects) | **PASS** |

---

## 6. KẾT LUẬN PHASE P0-A

- Toàn bộ bề mặt tấn công unauthenticated write đã được cô lập triệt để.
- Mô hình xác thực Gateway & cơ chế phê duyệt mật mã học (Two-Phase Cryptographic Approval) đã được chứng minh hoạt động hoàn hảo bằng bằng chứng thực thi runtime 12/12 test PASS.
- Sẵn sàng tiến vào **Phase P0-B: Thay thế n8n Mocks bằng Real Workflows**.
