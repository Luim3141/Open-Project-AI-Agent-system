# BÁO CÁO DIỄN TẬP SAO LƯU & PHỤC HỒI ĐỘC LẬP (RELIABILITY & BACKUP DRILL REPORT)
## Kiểm Định Khả Năng Phục Hồi Thảm Họa Thực Tế Toàn Diện (Full-Stack Disaster Recovery)

**Thời điểm thực hiện:** 2026-10-28T06:54:58.005679+00:00  
**Môi trường:** QLDAPM MAIN (Project ID 5: `qldapm-local`, OpenProject Self-Hosted)  
**Kết luận Diễn tập:** **`READY_FOR_OPERATOR_UAT`**  
**Chính sách chất lượng:** Zero False-PASS (Báo cáo trung thực, ghi nhận rành mạch cơ chế sao lưu khả dụng).

---

## 1. Đánh giá Dung lượng & An toàn Đĩa (Storage Health)
- **Ổ đĩa D (Workspace & Data):** Tổng 1514.27 GB, Còn trống **582.54 GB** (38.47%).
- **Ổ đĩa C (AppData & System):** Tổng 348.73 GB, Còn trống **81.79 GB** (23.45%).
- **Ngưỡng an toàn:** Đạt chuẩn an toàn vận hành dài hạn (> 10 GB khả dụng).

---

## 2. Kết quả Sao lưu Toàn Diện (Full-Stack Consistent Snapshots)

| Thành phần Dữ liệu | Kích thước | Thời gian | Cơ chế Sao lưu | SHA-256 Fingerprint | Trạng thái |
|---|---|---|---|---|---|
| **OpenProject PostgreSQL** | 2,076,872 bytes | 1.002s | `pg_dump -Fc` (Compressed custom archive) | `0bb697a8181bb12051cfb9c4...` | **SUCCESS** |
| **AI Gateway SQLite** | 9,707,520 bytes | 0.063s | `VACUUM INTO` (Consistent point-in-time snapshot) | `c8c1a85497f79372485cc99a...` | **SUCCESS** |
| **Knowledge DB SQLite** | 5,107,712 bytes | 0.054s | `VACUUM INTO` (Consistent point-in-time snapshot) | `107b7ac0c8197b52ff9d7584...` | **SUCCESS** |
| **n8n SQLite & Encryption Key** | 12,587,008 bytes | 0.999s | Container `VACUUM INTO` + Copy `/home/node/.n8n/config` | DB: `4f4c384acf5de18cf51c...`<br>Key: `daa27645048a0d777dd3...` | **SUCCESS** |
| **Qdrant Vector DB** | 16,126,826 bytes | 2.818s | Volume Directory Gzip Archive (Cold Volume Backup) | `8dd911f022efa1e3edff47c2...` | **SUCCESS** |

---

## 3. Kiểm định Phục hồi trong Môi trường Cô lập (Isolated Restore Verification)
Tất cả các bản sao lưu đã được kiểm định phục hồi thực tế trong môi trường cô lập tạm thời:

1. **OpenProject PostgreSQL (`openproject_backup_*.dump`):**
   - **Thao tác diễn tập:** Phục hồi vào cơ sở dữ liệu tạm thời cô lập `op_drill_temp` qua lệnh `pg_restore`.
   - **Xác thực số liệu:**
     - Tổng số Work Packages phục hồi: **376 / 376** (Khớp 100% dữ liệu gốc).
     - Số Work Packages thuộc Project 5 (`qldapm-local`): **339 / 339**.
   - **Dọn dẹp:** Đã xóa cơ sở dữ liệu tạm `op_drill_temp` ngay sau khi kiểm tra.

2. **AI Gateway SQLite (`gateway_backup_*.sqlite`):**
   - `PRAGMA integrity_check`: **`ok`**
   - Số bản ghi audit: **19591**
   - Số phiên AI runs: **191**
   - Số đề xuất mutation: **57**
   - Số token hợp lệ: **196**
   - Số QA evidences: **2**

3. **Knowledge SQLite (`knowledge_backup_*.sqlite`):**
   - `PRAGMA integrity_check`: **`ok`**
   - Số tài liệu tri thức (knowledge_documents): **376** (Khớp toàn bộ 339 WPs của Project 5 + 4 ADRs + 25 Arch + 7 Sprint reports; 0 rò rỉ từ Project 1 & 2).
   - Số đoạn văn bản (knowledge_chunks): **1742**

4. **n8n Automation Engine (`n8n_backup_*.sqlite` + Config):**
   - `PRAGMA integrity_check`: **`ok`**
   - Số active workflows: **16 / 16**
   - Số credentials mã hóa: **4**
   - Khóa giải mã (`encryptionKey`): **ĐÃ ĐƯỢC SAO LƯU AN TOÀN** (Bảo đảm giải mã được 100% credentials sau khôi phục).

5. **Qdrant Vector Database Isolated Clone Restore & DR Strategy:**
   - **Diễn tập phục hồi cô lập thực tế:** Giải nén cold volume archive vào thư mục tạm thời và khởi chạy instance Qdrant cô lập (`qdrant-isolated-drill`) trên cổng `6335`.
   - **Kết quả xác thực cô lập:**
     - Trạng thái collection: **`green`**
     - Số lượng points khôi phục: **`1745` / 1,745**
     - Cấu hình vectors: **`1024` chiều, khoảng cách `Cosine`**
     - Ba điểm dữ liệu lịch sử (`op:wp:42`, `test:local:adr:0001`, `test:wp:999`): **ĐÃ TÌM THẤY VÀ BẢO TOÀN NGUYÊN VẸN** (6 bản ghi).
     - Truy vấn tìm kiếm ngữ nghĩa mẫu: Hoàn thành thành công, trả về 3 kết quả phù hợp.
   - **Hạn chế kỹ thuật phát hiện được:** Lệnh gọi API snapshot recovery của Qdrant (`PUT /snapshots/recover`) bị lỗi `EIO` do lời gọi hệ thống Linux `syncfs()` không tương thích trên Docker Desktop Windows VirtioFS bind mount; file tar snapshot REST API bị zero-padded do WAL đang mở.
   - **Quy trình phục hồi thảm họa chính thức (Verified DR Route):** Khôi phục bằng sao lưu thư mục Volume Cold Archive (`collections/qldapm_knowledge_dense`) kết hợp khởi động lại container `qldapm-qdrant`. Phương án này đã được kiểm định thực tế 100% trong môi trường cô lập.

---

## 4. Kiểm toán Lưu trữ Thực thi n8n (Execution Retention)
- Hiện có **273** executions lưu trữ với tổng dung lượng **9.0 MB**.
- **Chính sách dọn dẹp chính thức:** Sử dụng các biến môi trường chính thức của n8n (`EXECUTIONS_DATA_PRUNE=true`, `EXECUTIONS_DATA_MAX_AGE=336`, `EXECUTIONS_DATA_PRUNE_MAX_COUNT=1000`), không sử dụng câu lệnh xóa trực tiếp bằng SQL thô (`DELETE FROM execution_entity`) để tránh làm hỏng cấu trúc dữ liệu n8n.

---
*Báo cáo được khởi tạo tự động từ script kiểm định diễn tập phục hồi cô lập toàn diện.*
