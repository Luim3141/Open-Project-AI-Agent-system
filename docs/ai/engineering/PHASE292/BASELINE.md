# BÁO CÁO THẨM ĐỊNH HIỆN TRẠNG TOÀN DIỆN (FORENSIC BASELINE) — PHASE 2.9.2

> **Dự án:** QLDAPM MAIN  
> **Giai đoạn:** Phase 2.9.2 — Zero-Silent-Failure Functional Audit & Integration Repair  
> **Thời điểm thẩm định:** 2026-10-31  
> **Phương pháp thẩm định:** Forensic Playwright Automation on Live Runtime, PostgreSQL Inspection, and Ruby/Rails Route Trace  
> **Trạng thái:** HOÀN THÀNH 100% (ĐÃ TÁI HIỆN VÀ XÁC MINH TOÀN BỘ LỖI BẰNG DỮ LIỆU THỰC CHỨNG)

---

## 1. MÔI TRƯỜNG VẬN HÀNH VÀ ĐỊNH DANH DỰ ÁN

Qua truy vấn trực tiếp cơ sở dữ liệu PostgreSQL `openproject` (`SELECT id, name, identifier, active FROM projects;`):

| Project ID | Tên hiển thị (Name) | Identifier (Slug) | Trạng thái | Vai trò trong hệ thống |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Demo project | `demo-project` | Active | OpenProject default demo project |
| **2** | Scrum project | `your-scrum-project` | Active | OpenProject default scrum template |
| **5** | QLDAPM — Local Community | `qldapm-local` | Active | **BẤT BIẾN:** Chứa 341 Work Packages bài tập, bảo vệ nghiêm ngặt |
| **6** | AI Software Development Demo | `ai-dev-demo` | Active | **DỰ ÁN KỸ THUẬT AI:** Nơi vận hành AI Engineering Command Center |

> **Phát hiện quan trọng:** Định danh chính xác của Project 6 trong OpenProject là **`ai-dev-demo`** (URL chuẩn: `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`).

---

## 2. KẾT QUẢ TÁI HIỆN BẰNG BROWSER PLAYWRIGHT THỰC TẾ

Script tự động hóa [`tools/reproduce_phase292_baseline.py`](file:///d:/AI%20project/QLDAPM%20chat/tools/reproduce_phase292_baseline.py) sử dụng phiên đăng nhập hợp lệ của User 18 (`AI_SYSTEM_OWNER`) trên Chromium headless:

```json
{
  "timestamp": "2026-10-30T19:00:29Z",
  "navigation_entry_in_sidebar": false,
  "kpi_backlog_value": "0 / 5",
  "kpi_backlog_sub": "5/5 Units đã phát triển hoàn tất",
  "worker_header_text": "Worker: IDLE · Múi giờ: Asia/Ho_Chi_Minh (UTC+7) · Auto Delivery: 0 / 5 Units Delivered",
  "worker_kpi_text": "Worker: Chưa kết nối",
  "backlog_unit_statuses": [
    "PLANNED",
    "PLANNED",
    "PLANNED",
    "PLANNED",
    "PLANNED"
  ],
  "visible_feedback_after_run_once": 0
}
```

### Đối soát thực tế với phản ánh của Chủ dự án:
1. **Thiếu đường dẫn navigation OpenProject:**
   - Khi đứng tại trang Work Packages của Project 6 (`/projects/ai-dev-demo/work_packages`), menu sidebar bên trái **hoàn toàn không có mục "AI Command Center"**. Người dùng bắt buộc phải tự nhớ và dán URL vào thanh địa chỉ.
2. **Mâu thuẫn chỉ số KPI Backlog Units:**
   - Card KPI hiển thị: `0 / 5`
   - Dòng phụ ngay dưới hiển thị: `5/5 Units đã phát triển hoàn tất`
   - Dòng Header meta hiển thị: `Auto Delivery: 0 / 5 Units Delivered`
3. **Mâu thuẫn trạng thái Worker:**
   - Header meta hiển thị: `Worker: IDLE`
   - Card KPI Telemetry hiển thị: `Worker: Chưa kết nối` (Disconnected)
4. **Trạng thái Backlog Items hiển thị sai:**
   - Toàn bộ 5 đơn vị công việc (đã hoàn thành và mở 5 PRs trên GitHub) đều bị gắn nhãn màu cyan: `PLANNED`.
5. **Nút bấm phản hồi im lặng (Zero Feedback):**
   - Khi nhấn nút `RUN ONCE`, browser gửi `POST /projects/ai-dev-demo/qldapm-ai/commands`, controller xử lý và render lại trang nhưng **hoàn toàn không có thông báo toast, alert hay banner nào** (`visible_feedback_after_run_once: 0`).
   - Nút bấm không có trạng thái loading, không bị disabled khi submit, tạo cảm giác như nút không hoạt động.
6. **Không có cơ chế tự động cập nhật (No Real-Time Polling):**
   - Mã nguồn view hoàn toàn không có `setInterval`, `fetch` hay bất kỳ polling loop nào. Giao diện là 100% static HTML render server-side một lần.

---

## 3. DANH MỤC ẢNH CHỤP MÀN HÌNH BẰNG CHỨNG HIỆN TRẠNG
Đã lưu trữ tại [`docs/ai/engineering/PHASE292/`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai/engineering/PHASE292/):
1. `01_work_packages_sidebar.png`: Minh chứng menu sidebar của Project 6 không có mục AI Command Center.
2. `02_command_center_initial.png`: Minh chứng mâu thuẫn KPI `0/5` vs `5/5`, `IDLE` vs `Chưa kết nối`, và 5 nhãn `PLANNED`.
3. `03_after_run_once_click.png`: Minh chứng sau khi bấm nút RUN ONCE, giao diện tải lại nhưng không có bất kỳ thông báo kết quả nào.
