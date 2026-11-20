# BẢN ĐẶC TẢ VÀ ĐỐI SOÁT TÍNH NHẤT QUÁN CỦA CÁC CHỈ SỐ (KPI DATA CONSISTENCY)

> **Dự án:** QLDAPM MAIN — Phase 2.9.2  
> **Chủ đề:** Khắc phục triệt để mâu thuẫn số liệu, chuẩn hóa công thức tính toán và nguồn sự thật (Single Source of Truth - SSOT) cho toàn bộ KPIs trên AI Command Center.

---

## 1. NGUỒN SỰ THẬT VÀ ÁNH XẠ DỮ LIỆU (SSOT MAPPING)

| Chỉ số KPI | Vị trí hiển thị | Nguồn sự thật (Backend SSOT) | Công thức / Khóa truy xuất | Trạng thái trước sửa (Bug) | Trạng thái sau sửa (Đúng) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backlog Delivery Ratio** | Hero KPI Card 2 | Gateway `engineering_status` -> `backlog` list | `delivered_count / total_backlog` với điều kiện: `item['state'] == 'succeeded' \|\| item['status'] == 'DELIVERED'` | Hiển thị `0 / 5` do kiểm tra sai khóa `b['status'] == 'DELIVERED'` (trong khi backend trả `'state': 'succeeded'`). | Hiển thị chính xác **`5 / 5`** tương ứng 5 units đã hoàn thành. |
| **Backlog Subtitle** | Hero KPI Card 2 Sub | Gateway `engineering_status` -> `backlog` list | `"#{delivered_count} / #{total_backlog} Units đã phát triển hoàn tất"` | Dòng in cứng `5/5 Units đã phát triển hoàn tất`, mâu thuẫn với `0/5` ở trên. | Đồng bộ động: **`5 / 5 Units đã phát triển hoàn tất`**. |
| **Header Auto Delivery** | Header Meta Status Bar | Gateway `engineering_status` -> `backlog` list | `"Auto Delivery: #{delivered_count} / #{total_backlog} Units Delivered"` | Hiển thị `Auto Delivery: 0 / 5 Units Delivered`. | Hiển thị chính xác: **`Auto Delivery: 5 / 5 Units Delivered`**. |
| **Worker Status** | Header Meta Status Bar | Gateway `engineering_status` -> `worker` object | Nếu `worker['worker_id'].present?` thì `ALIVE (<id>)`, ngược lại `IDLE (Sẵn sàng)`. | Hiển thị `Worker: IDLE`. | Hiển thị chuẩn hóa: **`Worker: IDLE (Sẵn sàng)`**. |
| **Worker Telemetry** | Hero KPI Card 1 Sub | Gateway `engineering_status` -> `worker` object | Nếu `worker['worker_id'].present?` thì `Online & Đang chạy`, ngược lại `IDLE (Sẵn sàng)`. | Hiển thị `Worker: Chưa kết nối` (mâu thuẫn với Header). | Hiển thị đồng bộ: **`Worker: IDLE (Sẵn sàng)`**. |
| **Backlog Badges** | Tab Mission Control | Gateway `engineering_status` -> `backlog` | `(unit['state'] == 'succeeded' \|\| unit['status'] == 'DELIVERED') ? 'DELIVERED' : 'PLANNED'` | Hiển thị toàn bộ nhãn `PLANNED` màu xanh dương do `unit['status']` là nil. | Hiển thị toàn bộ nhãn **`DELIVERED`** màu xanh ngọc (emerald chip). |
| **Native Task Status** | Tab Native Backlog Table | Gateway `engineering_status` -> `tasks` | `(t['status'].is_a?(Hash) ? t['status']['name'] : t['status']).to_s` | Đoạn mã `t['status']['name']` bị rỗng khi status là chuỗi. | Hiển thị chuẩn xác: **`REVIEW`**, **`IN PROGRESS`** theo đúng trạng thái OpenProject. |
| **GitHub Stacked PRs** | Hero KPI Card 3 | GitHub Reconciliation API & SQLite cache | `github_prs.size` | Hiển thị `5 PRs` | Hiển thị **`5 PRs`** (1 Merged Feature, 4 Open Stacked). |

---

## 2. PHÂN ĐỊNH RÕ RÀNG CÁC NHÃN TRẠNG THÁI (STATUS CLARIFICATION)
Nhằm tránh gây hiểu lầm cho người vận hành:
1. **Trạng thái Kỹ thuật (Technical Delivery):** Cả 5 units (#380, #381, #382, #383, #384) đã được phát triển hoàn tất qua TDD, có 5 PRs trên GitHub. Nhãn hiển thị là **`DELIVERED`**.
2. **Trạng thái Nghiệp vụ OpenProject (Business Status):** Các Task đang ở trạng thái **`REVIEW`** trong OpenProject để chờ Tech Lead/Owner nghiệm thu thủ công trước khi chuyển sang Done.
3. **Trạng thái Work Package Cha (#379):** Đang ở trạng thái **`IN PROGRESS`** theo đúng cam kết an toàn, không tự động đóng trước khi có phê duyệt.
