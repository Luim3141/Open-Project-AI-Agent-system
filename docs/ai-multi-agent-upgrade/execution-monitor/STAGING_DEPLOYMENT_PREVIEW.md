# KẾ HOẠCH TRIỂN KHAI STAGING (STAGING DEPLOYMENT PREVIEW)
## EXECUTION MONITOR UI/UX REFINEMENT

- **Chủ dự án:** QLDAPM Project Owner
- **Kỹ sư phụ trách:** Gemini Principal Frontend Engineer & Visual QA Specialist
- **Trạng thái hiện tại:** `READY_FOR_STAGING_DEPLOYMENT` (Đang chờ Chủ dự án phê duyệt)
- **Mức độ rủi ro:** THẤP (Chỉ cập nhật Rails View partials trong Core, không thay đổi Database, Gateway, hoặc Gemini models)

---

### 1. Thông tin phiên bản & Định danh Image

| Thành phần | Hiện tại trên Staging (Baseline) | Candidate đề xuất triển khai | Trạng thái thay đổi |
|---|---|---|---|
| **Core (Web UI)** | `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20` | `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b` | **NÂNG CẤP UI/UX** |
| **Gateway** | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | **GIỮ NGUYÊN (100% Khớp)** |
| **PostgreSQL DB** | `qldapm-ai-stage-db-1` | Không đổi | **KHÔNG CÓ MIGRATION** |
| **SQLite Store** | `openproject/ai/state` | Không đổi | **BẢO TỒN NGUYÊN VẸN** |
| **Quick Tunnel** | `qldapm-ai-stage-quick-tunnel-1` | Không đổi | **KHÔNG RESTART** |

- **Overlay Manifest SHA-256:** `ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920`
- **Candidate Image Tag:** `qldapm-ui-candidate:final`

---

### 2. Các cải tiến chính mang lại

1. **Đồng bộ OpenProject Light Theme:** Loại bỏ hoàn toàn khối màu đen navy lệch chuẩn (`#172334`), đồng bộ theo Primer design system sáng sủa, thanh lịch.
2. **Trang Execution History tối ưu:** Cột bảng gọn gàng, trạng thái không bị gãy dòng, tìm kiếm & sắp xếp 38px chuẩn SaaS, nút điều hướng sơ đồ trực quan.
3. **Cấu trúc Tab cho Agent Detail:** Gom 18 thông số kỹ thuật thành các tab `Thông tin chính`, `Kết quả xử lý`, `Tất cả thông số`, loại bỏ cuộn dọc quá mức.
4. **Sơ đồ điều phối Multi-Agent cao cấp:** Node cards bo góc `rx="12"`, avatar role chuyên biệt theo màu sắc (`SV`, `BA`, `DEV`, `QA`, `RV`, `Σ`), phân biệt rõ nét đứt (Assignment) và nét liền (Dependency).
5. **Báo cáo tổng hợp đa phân mục:** Tự động tách nhỏ nội dung của BA, Developer, QA thành các khối thẻ rõ ràng, kèm nút xem lại "Nội dung nguyên bản".
6. **Chế độ Trình chiếu (Presentation Mode):** Mở rộng toàn màn hình, hỗ trợ phím tắt `Esc` và phím mũi tên bàn phím để trình bày đồ án trước hội đồng phản biện.

---

### 3. Kết quả kiểm thử trước khi triển khai (Isolated Qualification)

- **Đơn vị kiểm thử:** 39 test cases Playwright tự động trên 5 kích thước màn hình (1920×1080, 1440×900, 1366×768, 768×1024, 375×812).
- **Tỉ lệ đạt:** **39 / 39 (100% PASS)**.
- **Visual QA:** Đã đối chiếu ảnh chụp trước (BEFORE) và sau (AFTER), không ghi nhận bất kỳ lỗi tràn ngang màn hình hay xung đột style nào.
- **Tiêu thụ Gemini API:** **0 token / 0 calls** (Hoàn toàn chạy trên dữ liệu đã lưu và fixture).

---

### 4. Quy trình triển khai chính xác (Khi được Chủ dự án duyệt)

Lệnh thực thi duy nhất qua CLI tiêu chuẩn của dự án:

```powershell
Set-Location 'D:\AI project\QLDAPM chat'
& '.\openproject\ai\.venv\Scripts\python.exe' '.\openproject\ai\provision_local_stage.py' --application-only --gateway-image 'sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b' --core-image 'sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b'
```

- **Thời gian downtime dự kiến:** ~15-25 giây (chỉ khởi động lại Puma server của `staging-web`).
- **Thời gian khôi phục nếu cần rollback:** < 30 giây.

---

### 5. Yêu cầu phê duyệt (Approval Gate)

Theo đúng quy tắc vận hành tại Section VIII:
> "Chỉ sau khi được duyệt mới triển khai Staging."

Kính trình Chủ dự án QLDAPM xem xét và đưa ra quyết định phê duyệt để thực hiện việc áp dụng Candidate Image lên Staging.
