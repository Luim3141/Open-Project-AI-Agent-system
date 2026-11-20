# BASELINE VÀ KIỂM KÊ DANH TÍNH TÀI KHOẢN TRÊN STAGING
## FINAL STAGING ACCESS RECOVERY, GANTT SCHEDULING & AGILE BOARDS STABILIZATION
**Thời điểm ghi nhận:** 2026-10-20T05:55:00+07:00  
**Môi trường:** Staging (`http://localhost:18091` / Quick Tunnel: `https://foo-bodies-albert-gabriel.trycloudflare.com`)  
**Database:** PostgreSQL `qldapm-ai-stage-db-1` (Project ID: 3, `qldapm-local`)  
**Core Container Image:** `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2`  
**Gateway Container Image:** `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`  
**Bản sao lưu trước can thiệp:** `$env:LOCALAPPDATA\QLDAPM\openproject-ai\operator\pre-stabilization-20261020-0555\staging_db_before_stabilization.sql` (6,322,247 bytes)

---

## 1. BẢNG KIỂM KÊ DANH TÍNH TÀI KHOẢN VÀ THIẾT BỊ 2FA (TOTP)

| User ID | Login | Email | Project Role (`qldapm-local`) | Admin Global | Phân loại Account | Trạng thái | Nguồn Auth | Active TOTP | Inactive TOTP | Khác 2FA | Recovery Code | Môi trường | Protected (Cấm sửa) | Thuộc Scope Reset được duyệt |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **4** | `admin` | `admin@example.net` | Không tham gia | Có (true) | Hệ thống gốc (Locked) | Khóa (3) | Internal | 0 | 0 | 0 | Không | Staging | Không | **KHÔNG** (Giữ nguyên) |
| **5** | `stage-owner` | `owner@qldapm.local` | Không tham gia | Có (true) | Người dùng quản trị | Hoạt động (1) | Internal | 1 | 0 | 0 | Không | Staging | Không | **CÓ** (Reset để enroll lại) |
| **6** | `ba-pm` | `ba-pm@stage.invalid` | `QLDAPM BA-PM` | Không (false) | Người dùng nghiệp vụ | Hoạt động (1) | Internal | 1 | 0 | 0 | Không | Staging | Không | **CÓ** (Reset để enroll lại) |
| **7** | `pm` | `pm@stage.invalid` | `QLDAPM PM` | Không (false) | Người dùng nghiệp vụ | Hoạt động (1) | Internal | 1 | 0 | 0 | Không | Staging | **BẢO VỆ ĐẶC BIỆT (PM)** | **KHÔNG — CẤM SỬA** |
| **8** | `be` | `be@stage.invalid` | `QLDAPM BE` | Không (false) | Người dùng nghiệp vụ | Hoạt động (1) | Internal | 1 | 22 | 0 | Không | Staging | **BẢO VỆ ĐẶC BIỆT (BE)** | **KHÔNG — CẤM SỬA** |
| **9** | `fe` | `fe@stage.invalid` | `QLDAPM FE` | Không (false) | Người dùng nghiệp vụ | Hoạt động (1) | Internal | 1 | 0 | 0 | Không | Staging | Không | **CÓ** (Reset để enroll lại) |
| **10** | `qa` | `qa@stage.invalid` | `QLDAPM QA` | Không (false) | Người dùng nghiệp vụ | Hoạt động (1) | Internal | 1 | 0 | 0 | Không | Staging | Không | **CÓ** (Reset để enroll lại) |
| **11** | `luim-admin` | `luim-admin@qldapm.local.invalid` | Không tham gia | Có (true) | Quản trị viên phụ | Hoạt động (1) | Internal | 0 | 0 | 0 | Không | Staging | Không | **KHÔNG** (Chưa có thiết bị) |
| **12** | `system-admin` | `system-admin@qldapm.local` | `QLDAPM PM` | Có (true) | Quản trị viên phụ | Hoạt động (1) | Internal | 0 | 0 | 0 | Không | Staging | Không | **KHÔNG** (Chưa có thiết bị) |

---

## 2. PHÂN LOẠI VÀ DANH SÁCH RESET ĐƯỢC CHỦ DỰ ÁN PHÊ DUYỆT

### Nhóm 1: BẢO VỆ TUYỆT ĐỐI — CẤM THAY ĐỔI
- **User 7 (`pm`)**: Giữ nguyên mật khẩu, giữ nguyên thiết bị TOTP (Device ID: 24).
- **User 8 (`be`)**: Giữ nguyên mật khẩu, giữ nguyên thiết bị TOTP (Device ID: 23 cùng 22 bản ghi lịch sử).

### Nhóm 2: THUỘC PHẠM VI RESET THIẾT BỊ TOTP ĐỂ CHỦ DỰ ÁN ENROLL LẠI QUA QR
- **User 5 (`stage-owner`)**: Device ID 28.
- **User 6 (`ba-pm`)**: Device ID 27.
- **User 9 (`fe`)**: Device ID 25.
- **User 10 (`qa`)**: Device ID 26.

### Nhóm 3: NGOẠI VI — GIỮ NGUYÊN
- **User 4 (`admin`)**, **User 11 (`luim-admin`)**, **User 12 (`system-admin`)**: Không có thiết bị TOTP hoạt động, không thuộc danh sách phê duyệt reset.

---

## 3. CẤU HÌNH BẢO MẬT 2FA TOÀN CỤC (GLOBAL SETTINGS)
- Setting: `Setting.plugin_openproject_two_factor_authentication`
  - `active_strategies: ["totp"]`
  - `enforced: true` (BẮT BUỘC toàn bộ người dùng phải có 2FA khi đăng nhập)
  - `allow_remember_for_days: 0`
- **Quy tắc bảo mật:** Không tắt 2FA toàn cục, không bypass qua tham số hay controller. Mọi tài khoản sau khi xóa thiết bị cũ sẽ tự động rơi vào luồng Native Forced Registration để người dùng quét QR Code mới.
