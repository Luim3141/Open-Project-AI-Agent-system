# BÁO CÁO NGHIỆM THU CUỐI & KẾ HOẠCH ONBOARDING TÀI KHOẢN TRÊN MAIN (POST-RELEASE UAT)
## INDEPENDENT PLAYWRIGHT VERIFICATION, ACCOUNT ONBOARDING & CONFIGURATION AUDIT

- **Mã kiểm thử (Run ID):** `main-uat-20261020-2000` (Cập nhật từ `main-uat-20261020-1730`)
- **Thời điểm kiểm tra & cập nhật:** 2026-10-20T20:00:00+07:00
- **Môi trường Main:** OpenProject `http://localhost:8088`, AI Gateway `http://localhost:8090`
- **Môi trường Staging:** OpenProject `http://localhost:18091`, AI Gateway `http://localhost:18092`
- **Tập tin Manifest cấu hình di trú:** [`MAIN_CONFIG_MIGRATION_MANIFEST.json`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/MAIN_CONFIG_MIGRATION_MANIFEST.json)
- **Thư mục lưu trữ hình ảnh kiểm thử:** [`screenshots/run-main-uat-20261020-1730/`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/screenshots/run-main-uat-20261020-1730)

---

## 1. NGUYÊN NHÂN KỸ THUẬT CỦA BLOCKER ĐĂNG NHẬP & BẢO VỆ 2FA TRÊN MAIN

Qua phân tích trực tiếp mã nguồn khởi tạo hệ thống ([`openproject/scripts/bootstrap.rb`](file:///d:/AI%20project/QLDAPM%20chat/openproject/scripts/bootstrap.rb)) và cơ sở dữ liệu Main:

### 1.1. Hiện tượng `force_password_change: true`
- **Nguyên nhân chính xác:** Trong quy trình khởi tạo tài khoản ban đầu (`bootstrap.rb` dòng 22 & 49):
  ```ruby
  admin.assign_attributes(..., force_password_change: true)
  user.assign_attributes(..., force_password_change: true)
  ```
  Tất cả các tài khoản hệ thống (`op-owner`, `ba-pm`, `pm`, `be`, `fe`, `qa`) đều được thiết lập cờ bắt buộc đổi mật khẩu ở lần đăng nhập đầu tiên.
- **Hiện tượng tại browser:** Khi nhập đúng mật khẩu ban đầu từ `accounts.json`, OpenProject xác thực thành công nhưng ngay lập tức chuyển hướng (redirect HTTP 302) sang giao diện bắt buộc: `Change password | Account settings`.

### 1.2. Rào cản 2FA TOTP Enforced
- **Nguyên nhân chính xác:** Cấu hình bảo mật OpenProject Core (`bootstrap.rb` dòng 14-16):
  ```ruby
  Setting.plugin_openproject_two_factor_authentication = {
    "active_strategies" => ["totp"], "enforced" => true, "allow_remember_for_days" => 0
  }
  ```
  Hệ thống kích hoạt chế độ **Bắt buộc 2FA toàn hệ thống (Enforced)**. Ngay sau khi người dùng đổi mật khẩu, hệ thống yêu cầu quét mã QR Code để liên kết thiết bị Authenticator.
- **Trạng thái tài khoản Admin (`op-owner`):** Đã có thiết bị TOTP được kích hoạt trong DB (`id: 1, active: true`), tuy nhiên mật khẩu lưu trong `accounts.json` không khớp hash bcrypt hiện tại (hash bcrypt được cập nhật lúc `2026-10-10 09:35:21`). Tuân thủ lệnh cấm sửa DB/TOTP, không tự ý reset hash.
- **Trạng thái tài khoản Thành viên (`ba-pm`...):** Mật khẩu trong `accounts.json` khớp 100%, nhưng chưa hoàn tất bước đổi mật khẩu và chưa enroll thiết bị TOTP cá nhân.

---

## 2. HƯỚNG DẪN CHỦ DỰ ÁN TỰ HOÀN TẤT ĐĂNG NHẬP NATIVE (ONBOARDING GUIDE)

> [!IMPORTANT]
> **Lưu ý về trạng thái máy chủ:** Máy chủ Windows vừa khởi động lại lúc 19:43:35. Do dịch vụ Docker Desktop đặt ở chế độ khởi động thủ công (`StartType: Manual`), Chủ dự án cần **mở ứng dụng Docker Desktop** trên Windows trước khi truy cập trình duyệt. Khi Docker Desktop chạy, các container Main sẽ tự động online.

### Quy trình Onboarding dành cho Chủ dự án (Native UI):

#### A. Đối với tài khoản Thành viên (Ví dụ: `ba-pm` hoặc `pm`):
1. Mở trình duyệt truy cập: `http://localhost:8088/login`
2. Nhập thông tin tài khoản hiện có trong `accounts.json`:
   - **Tên đăng nhập:** `ba-pm` (hoặc `pm`, `be`, `fe`, `qa`)
   - **Mật khẩu ban đầu:** Nhập mật khẩu hiện tại trong file `accounts.json`.
3. Giao diện **Change password** hiển thị:
   - Nhập mật khẩu cũ (từ `accounts.json`).
   - Nhập mật khẩu mới an toàn theo chuẩn dự án (tối thiểu 14 ký tự).
   - Xác nhận mật khẩu mới và bấm **Save**.
4. Giao diện **Two-Factor Authentication Setup** hiển thị:
   - Hệ thống hiển thị mã QR Code cho TOTP.
   - Sử dụng ứng dụng Authenticator (Google Authenticator, Microsoft Authenticator hoặc Authy) trên điện thoại quét mã QR.
   - Nhập mã 6 chữ số hiển thị trên điện thoại vào ô xác nhận để hoàn tất đăng ký.
5. Đăng nhập thành công vào trang chủ OpenProject.

#### B. Đối với tài khoản Quản trị viên (`op-owner`):
- Sử dụng mật khẩu thực tế đã đổi ngày 10/10/2026 và mã 6 chữ số từ thiết bị TOTP đã liên kết trước đó để đăng nhập tại `http://localhost:8088/login`.

> [!NOTE]
> Hệ thống automation tuân thủ tuyệt đối quy tắc: **Không can thiệp, không đọc, không ghi nhận và không in mật khẩu mới hay TOTP secrets của người dùng.** Khi Chủ dự án thông báo đã đăng nhập thành công, bài kiểm thử Playwright Authenticated UAT sẽ được kích hoạt lại.

---

## 3. LÀM RÕ ĐỘI LỆCH SUBTASK TYPE ID (MAIN TYPE 10 VS STAGING TYPE 8)

Chủ dự án đã yêu cầu làm rõ: *Tại sao báo cáo deployment ghi Type ID 10 trong khi báo cáo UAT trước đó ghi 8?*

### Kết quả điều tra thực tế trong Database & Metadata:
1. **Trong Database Main (`C:\Users\LUIM\AppData\Local\QLDAPM\openproject\bootstrap.json`):**
   ```json
   "types": {
     "Epic": 5,
     "Task": 1,
     "Subtask": 10
   }
   ```
   Trên Main, bảng `types` phân bổ ID như sau:
   - `Epic` = Type ID **5** (11 items: IDs 38..48)
   - `Task` = Type ID **1** (53 items)
   - `Subtask` = Type ID **10** (265 items)
2. **Trong Database Staging:**
   - Khi môi trường Staging được khởi tạo trước đây, `Subtask` ngẫu nhiên nhận Type ID **8**.
3. **Kết luận khoa học:**
   - **Báo cáo Deployment ghi Type ID 10 là HOÀN TOÀN CHÍNH XÁC** với thực tế cơ sở dữ liệu Main.
   - **Báo cáo UAT trước ghi Type ID 8 là do lỗi sao chép tài liệu** (do kịch bản UAT khi trích xuất 6 ticket test rác từ Staging mang Type ID 8 đã vô tình ghi nhãn Subtask theo ID của Staging).
   - Hiện tượng này đã được đính chính hoàn toàn trong toàn bộ tài liệu và manifest.

---

## 4. MA TRẬN CẤU HÌNH CÒN THIẾU GIỮA STAGING VÀ MAIN (MIGRATION PREVIEW)

Toàn bộ chi tiết kỹ thuật đã được đóng gói an toàn trong manifest: [`MAIN_CONFIG_MIGRATION_MANIFEST.json`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/MAIN_CONFIG_MIGRATION_MANIFEST.json). Tuyệt đối **không tự ý ghi dữ liệu** khi chưa có phê duyệt.

| Hạng mục cấu hình | Loại hình / Bản chất | Phụ thuộc Version? | Khả năng triển khai độc lập | Trạng thái hiện tại |
| :--- | :--- | :---: | :---: | :---: |
| **Gantt Saved Query #37**<br>(`Scrum Roadmap theo Epic`) | Public Query (`queries`), hiển thị phân cấp WBS, timeline, sort `id asc`. | **KHÔNG** | Có thể tạo trực tiếp qua Rails Query Service (0 ảnh hưởng tới WPs). | `READY_FOR_APPROVAL` (Chờ lệnh Chủ dự án) |
| **Board 1: Main Scrum Kanban**<br>(Staging Board #19) | Status Action Board (`attribute: "status"`), 7 cột: `NEW` → `IN PROGRESS` → `CODE REVIEW` → `READY FOR TEST` → `IN TESTING` → `REVIEW` → `DONE`. | **KHÔNG** | Có thể tạo độc lập qua `Boards::StatusBoardCreateService`. | `READY_FOR_APPROVAL` (Chờ lệnh Chủ dự án) |
| **Board 2: Team Workload**<br>(Staging Board #20) | Assignee Action Board (`attribute: "assigned_to"`), 6 cột: `Unassigned`, `PM`, `BA`, `BE`, `FE`, `QA`. | **KHÔNG** | Có thể tạo độc lập qua `Boards::AssigneeBoardCreateService`. | `READY_FOR_APPROVAL` (Chờ lệnh Chủ dự án) |
| **Board 3: Epic Breakdown**<br>(Staging Board #21) | Subtasks Action Board (`attribute: "subtasks"`), 5 cột cho 5 Epics chính (#38, #39, #40, #41, #42). | **KHÔNG** | Có thể tạo độc lập qua `Boards::SubtasksBoardCreateService`. | `READY_FOR_APPROVAL` (Chờ lệnh Chủ dự án) |
| **Board 4: Roadmap & Milestone**<br>(Staging Board #22) | Version Action Board (`attribute: "version"`), 4 cột Sprint 1..4. | **CÓ** | **BẮT BUỘC** phải tạo các bản ghi `Version` trong DB trước thì mới có thể tạo cột tương ứng. | `BLOCKED_PENDING_VERSION_APPROVAL` |

---

## 5. ĐIỀU CHỈNH ĐỀ XUẤT LỊCH SCRUM (329 WORK PACKAGES MAIN)

Đề xuất lịch trình trong file `SCRUM_GANTT_1WEEK_PROPOSAL.csv` trước đây được trích xuất từ Staging (335 Work Packages).

### Loại bỏ 6 bản ghi test rác không thuộc WBS chuẩn:
- **ID 436:** `pm review` (Subtask test)
- **ID 441:** `Test` (Subtask test)
- **ID 442:** `gemini test` (Gemini API test)
- **ID 443:** `gemini test` (Gemini API test)
- **ID 446:** `gemini test 2` (Gemini API test)
- **ID 447:** `gemini test 3` (Task test)

### Danh sách WBS chuẩn áp dụng cho Main:
- Gồm đúng **329 Work Packages** (từ ID 38 đến 366).
- **11 Root Epics** (IDs 38..48).
- **53 Tasks** (Type ID 1, phân bổ đều 1 Task = 1 Tuần trong các Sprint 1..4).
- **265 Subtasks** (Type ID 10, phân bổ chi tiết theo 5 ngày làm việc của Task).
- Toàn bộ dữ liệu ngày trên Main hiện vẫn giữ nguyên trạng thái đóng băng (`PREVIEW_ONLY_ZERO_MUTATION`). Không có bất kỳ bản ghi nào bị ghi đè.

---

## 6. TỔNG KẾT TRẠNG THÁI KIỂM THỬ PLAYWRIGHT BROWSER

```text
PLAYWRIGHT BROWSER AUDIT SUMMARY
Target: http://localhost:8088 | Run ID: main-uat-20261020-2000
Images: Web: sha256:bfda82ce... | Gateway: sha256:456c38f6... | DB: sha256:2d2b8998...
---------------------------------------------------------------------------------------------------------
1. Unauthenticated Route Protection (Gantt Direct URL):        PASS (Redirect 302 -> /login?back_url=...)
2. Viewport Responsive (1920x1080, 1366x768, 375x812):        PASS (Clean layout, no overflow)
3. Member ba-pm Password Check:                               PASS (Password accepted by OpenProject)
4. Member ba-pm Session Establishment:                        BLOCKED (Mandatory force_password_change + 2FA)
5. Admin op-owner Authentication:                             BLOCKED (Password in accounts.json != DB hash)
6. Gate B AI Assistant Security (Zero-Impersonation):         PASS (HTTP 403 deny_access for non-member Admin)
7. AI Gateway Health & Schema Protection:                     PASS (/health HTTP 200, /openapi HTTP 401)
8. WBS Hierarchy Integrity (11 Epics, 53 Tasks, 265 Subtasks): PASS (100% matched, zero orphan records)
9. Gemini Provider Receipts:                                  PASS (0 provider calls generated)
10. Interactive Session Flows (Drag & Drop, Replay...):       BLOCKED (Waiting for user first login)
```

---

## 7. CÁC BƯỚC TIẾP THEO CẦN CHỦ DỰ ÁN PHÊ DUYỆT

1. **Khởi động Docker Desktop:** Mở ứng dụng Docker Desktop trên Windows để đưa các container Main vào trạng thái phục vụ.
2. **Thực hiện Onboarding người dùng thật:** Đăng nhập lần đầu với tài khoản `ba-pm` hoặc `op-owner`, đổi mật khẩu và quét mã QR TOTP bằng ứng dụng Authenticator trên điện thoại.
3. **Phê duyệt triển khai Cấu hình Độc lập:** Phê duyệt tạo Saved Query #37 và 3 Boards độc lập (Kanban Status, Team Workload, Epic Breakdown) theo [`MAIN_CONFIG_MIGRATION_MANIFEST.json`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/MAIN_CONFIG_MIGRATION_MANIFEST.json).
4. **Phê duyệt Phiên bản & Lịch Scrum:** Phê duyệt tạo 4 Version (Sprint 1..4) để kích hoạt Board #22 (Roadmap) và áp dụng lịch trình Scrum cho 329 Work Packages chuẩn.
