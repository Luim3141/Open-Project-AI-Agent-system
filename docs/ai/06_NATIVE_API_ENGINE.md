# BÁO CÁO TRIỂN KHAI VÀ KIỂM CHỨNG PHASE 6: NATIVE OPENPROJECT API WRITE ENGINE

> **Phiên bản:** 1.0.0 — QLDAPM MAIN PRODUCTION  
> **Ngày thực hiện:** 2026-10-22  
> **Trạng thái:** `VERIFIED` — 6/6 Tests Passed (T10 -> T14)  
> **Môi trường:** QLDAPM Main (OpenProject v14 Live port 8088, AI Gateway port 8090, Dự án ID 5 `qldapm-local`)

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC THIẾT KẾ (NATIVE-ONLY)

Hệ thống ghi dữ liệu của QLDAPM AI được xây dựng theo triết lý **Native API v3 Only**, tuân thủ nghiêm ngặt các nguyên tắc:
1. **Không ghi trực tiếp SQL vào PostgreSQL**: Tuyệt đối bảo vệ tính toàn vẹn của business logic, triggers, audit log và quyền hạn nội tại của OpenProject. Mọi thay đổi dữ liệu phải đi qua REST API v3 chính thống.
2. **Kiểm soát khóa lạc quan (Optimistic Concurrency Control)**: Mọi thao tác cập nhật (`update_work_package`, `transition`, `comment`) bắt buộc kiểm tra và đối chiếu `lockVersion` (hoặc `lock_version`). Nếu phiên bản bị trôi lệch, hệ thống từ chối ngay lập tức với lỗi `STALE_WORK_PACKAGE`, ngăn chặn ghi đè mất mát dữ liệu (lost updates).
3. **Chống trùng lặp tuyệt đối (Strict Idempotency Guard)**: Mọi mutation bắt buộc phải có `idempotency_key` hợp lệ ($1 \le \text{length} \le 100$). Sử dụng cơ chế 2 pha `store.begin(actor, key, payload)` và `store.finish(actor, key, result)`:
   - Request trùng lặp có cùng key và payload sẽ trả về kết quả đã cache mà không gọi OpenProject lần 2.
   - Request tái sử dụng key nhưng khác payload bị từ chối với lỗi `IDEMPOTENCY_KEY_REUSED`.
4. **Cơ chế phê duyệt 2 bước (Two-Step Proposal & Confirm)**: Mọi thao tác ghi trừ khi được gắn cờ `auto_execute` có kiểm soát đều trải qua bước sinh **Proposal**:
   - Bước 1: Sinh Proposal chứa preview chi tiết (trạng thái `before`, thay đổi `changes`, mã băm `hash`, thời hạn `expires`, và cờ `human_confirmation_required = True`).
   - Bước 2: Chỉ khi được xác nhận (`confirmed=True`), thao tác mới được gửi tới OpenProject.
5. **Xác minh sau khi ghi (Read-After-Write Verification)**: Sau khi gọi API ghi (POST/PATCH), hệ thống lập tức đọc lại (readback) đối tượng từ OpenProject để đối chiếu từng trường dữ liệu và marker mã băm yêu cầu `QLDAPM-request-<digest>`. Nếu dữ liệu không khớp hoặc không tìm thấy, hệ thống báo lỗi không coi thao tác là thành công.
6. **Phân quyền vai trò (Role-Based Access Control - RBAC)**:
   - Quyền Ghi/Thay đổi trạng thái (`create_work_package`, `update_work_package`, `transition`): **Duy nhất PM** (Role `PM` - Actor 19).
   - Các vai trò chuyên gia (`BA`, `BE`, `FE`, `QA`): Quyền Đọc, Phân tích, và Bình luận (`comment`). Mọi nỗ lực ghi vượt quyền đều bị chặn ngay tại Gateway với lỗi `PM_REQUIRED`.

---

## 2. KIẾN TRÚC VÀ CÁC THÀNH PHẦN CỐT LÕI

### 2.1. Native API Client (`openproject/ai/gateway/native.py`)
- Quản lý phiên làm việc HTTP với OpenProject API v3 qua Basic Auth API Token (từng Actor có token riêng biệt lưu trong `credentials.json`).
- Deadline 90s, cơ chế stream byte bounded tối đa 8MB tránh tràn bộ nhớ.
- Kiểm tra danh tính (`identity`) và thẩm tra quyền thành viên trong Dự án 5 (`qldapm-local`).
- Cô lập dự án: Mọi truy cập Work Package đều kiểm tra `_links.project.href == "/api/v3/projects/5"`.

### 2.2. Gateway Service Layer (`openproject/ai/gateway/service.py`)
- Định tuyến command:
  - Read: `get_work_package`, `list_work_packages`, `analyze`, `get_project_options`.
  - Mutations: `create_work_package`, `update_work_package`, `comment`, `transition`.
- Điều phối Idempotency qua `store.begin` / `store.finish`.
- Tự động chèn metadata request marker dạng `<!-- QLDAPM-request-<digest> -->` vào nội dung comment để truy vết và hòa giải (reconciliation) khi mạng gián đoạn.
- Ghi nhận `correlation_id` cho mọi thao tác vào bảng audit `history`.

---

## 3. MA TRẬN KIỂM CHỨNG LIVE RUNTIME (TEST MATRIX T10 - T14)

Bộ test tự động hóa toàn diện được xây dựng tại [`openproject/ai/tests/test_native_write_engine.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_native_write_engine.py) và chạy trực tiếp với Live OpenProject Main:

| Test ID | Tên Kiểm Thử | Mục Tiêu & Cơ Chế Kiểm Thử | Kết Quả |
| :--- | :--- | :--- | :---: |
| **T10** | `test_t10_read_live_work_package_via_native_api` | Đọc Live WP 38 ("Tài khoản & Role") qua Native API v3. Xác minh ID=38, Project=5, `lockVersion` hợp lệ ($\ge 1$). Kiểm tra cho cả PM (19) và BA (20). | **PASS** |
| **T11** | `test_t11_controlled_live_write_with_read_after_write` | Ghi comment có phép bởi PM (19) trên WP 38 có `lock_version` hiện thời. Kiểm tra Read-After-Write tìm thấy đúng comment và marker `QLDAPM-request-<digest>`. | **PASS** |
| **T12** | `test_t12_rbac_unauthorized_role_write_rejection` | Kiểm tra RBAC: User 20 (BA) cố tình gọi `transition` hoặc `create_work_package`. Hệ thống chặn đứng và raise `PermissionError: PM_REQUIRED`. | **PASS** |
| **T13** | `test_t13_optimistic_locking_stale_work_package` | Kiểm tra Optimistic Locking: Cố tình truyền `lock_version=999999` (stale). Hệ thống từ chối ngay với `ValueError("STALE_WORK_PACKAGE")` trước khi gửi request tới OpenProject. | **PASS** |
| **T14** | `test_t14_idempotency_deduplication_and_reuse_rejection` | 1. Gọi lần 1 ghi thành công.<br>2. Gọi lần 2 cùng `idempotency_key` và payload: trả kết quả cache, không tạo thêm activity.<br>3. Gọi lần 3 cùng key nhưng khác payload: raise `ValueError("IDEMPOTENCY_KEY_REUSED")`. | **PASS** |
| **Prop** | `test_proposal_and_preview_workflow` | Kiểm tra 2-step confirmation: Khi `confirmed=False`, sinh Proposal trạng thái `pending`, có `preview.before`, `preview.changes`, `human_confirmation_required=True`. | **PASS** |

---

## 4. BẰNG CHỨNG THỰC THI THỰC TẾ (TEST EXECUTION LOG)

```text
======================================================================
$env:PYTHONPATH=".;openproject/ai"; & "openproject\ai\.venv\Scripts\python.exe" -m unittest openproject/ai/tests/test_native_write_engine.py -v

test_proposal_and_preview_workflow (openproject.ai.tests.test_native_write_engine.NativeWriteEngineTests.test_proposal_and_preview_workflow)
Verifies 2-step proposal creation when confirmed=False. ... ok
test_t10_read_live_work_package_via_native_api (openproject.ai.tests.test_native_write_engine.NativeWriteEngineTests.test_t10_read_live_work_package_via_native_api)
T10: Read live Work Package 38 via Native API v3. ... ok
test_t11_controlled_live_write_with_read_after_write (openproject.ai.tests.test_native_write_engine.NativeWriteEngineTests.test_t11_controlled_live_write_with_read_after_write)
T11: Controlled live write with Read-After-Write verification. ... ok
test_t12_rbac_unauthorized_role_write_rejection (openproject.ai.tests.test_native_write_engine.NativeWriteEngineTests.test_t12_rbac_unauthorized_role_write_rejection)
T12: RBAC rejects write attempts from non-PM roles (e.g. BA actor 20). ... ok
test_t13_optimistic_locking_stale_work_package (openproject.ai.tests.test_native_write_engine.NativeWriteEngineTests.test_t13_optimistic_locking_stale_work_package)
T13: Optimistic locking rejects mutation when lock_version does not match. ... ok
test_t14_idempotency_deduplication_and_reuse_rejection (openproject.ai.tests.test_native_write_engine.NativeWriteEngineTests.test_t14_idempotency_deduplication_and_reuse_rejection)
T14: Idempotency deduplication caches result; key reuse with different payload is rejected. ... ok

----------------------------------------------------------------------
Ran 6 tests in 152.796s

OK
```

---

## 5. ĐÁNH GIÁ RỦI RO VÀ PHƯƠNG ÁN AN TOÀN

1. **Rủi ro lạm dụng quyền PM**: Token của PM (Actor 19) có quyền tạo và chuyển trạng thái công việc. Giải pháp: Mọi mutation đều có proposal preview và bắt buộc kiểm tra `lockVersion` + lưu vết audit log `correlation_id`.
2. **Rủi ro phân mảnh mạng OpenProject**: Khi mạng chập chờn, một request ghi có thể đã được OpenProject xử lý nhưng gateway chưa nhận được response. Phương án xử lý: Gateway lưu request ở trạng thái `pending`. Không bao giờ tự động gửi lại mutation; gateway hỗ trợ `reconcile_request` thông qua đối soát marker `QLDAPM-request-<digest>`.
3. **Rollback**: Toàn bộ cấu hình và cơ sở dữ liệu đã được backup an toàn tại `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway-backup-pre-master-phase0`. Nếu cần khôi phục trạng thái cũ, chỉ cần sao chép đè lại thư mục state.

---

## 6. KẾT LUẬN GIAI ĐOẠN 6

Native OpenProject API Write Engine đã hoàn thiện 100% các tiêu chí an toàn, bảo vệ dữ liệu, kiểm soát đồng thời và phân quyền. Hệ thống sẵn sàng cho việc kết nối với **n8n Automation Engine (Phase 7)**.
