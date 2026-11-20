# BÁO CÁO SAO LƯU VÀ PHƯƠNG ÁN PHỤC HỒI HỆ THỐNG (ROLLBACK)
## BACKUP AND ROLLBACK REPORT

- **Thời điểm tạo backup:** 2026-10-21T13:40:00+07:00
- **Thư mục lưu trữ:** `docs/ai-multi-agent-upgrade/run_20261021_final_delivery/backups/`

---

### 1. DANH MỤC CÁC BẢN SAO LƯU ĐÃ XÁC MINH TOÀN VẸN

1. **Bản sao lưu nhị phân PostgreSQL Main (`main-database.dump`):**
   - Định dạng: Custom format (`pg_dump -Fc`), kích thước: **1,336,509 bytes**.
   - Kiểm tra phục hồi: Đã phục hồi thử nghiệm thành công vào cơ sở dữ liệu tạm thời trên `qldapm-rd-db-20261021`, đối chiếu 221 bảng khớp 100%.
2. **Bản sao lưu SQLite AI Gateway (`gateway.sqlite`):**
   - Kỹ thuật: Online Backup API an toàn với WAL, kích thước: **229,376 bytes**.
   - Kiểm tra tính toàn vẹn: `PRAGMA integrity_check = ok`.
3. **Ảnh chụp hiện trạng Project 5 (`project5-baseline-snapshot.json`):**
   - Ghi lại toàn bộ 329 Work Packages, 344 relations trước khi áp dụng ngày tháng.

---

### 2. QUY TRÌNH PHỤC HỒI NGUYÊN TRẠNG (ROLLBACK PROCEDURE)

Nếu cần hoàn tác bất kỳ thay đổi nào trên Main:
1. **Phục hồi Cơ sở dữ liệu PostgreSQL:**
   ```bash
   docker exec -i qldapm-openproject-db-1 pg_restore -U postgres --clean --no-owner -d openproject < docs/ai-multi-agent-upgrade/run_20261021_final_delivery/backups/main-database.dump
   ```
2. **Phục hồi SQLite AI Gateway:**
   ```bash
   docker cp docs/ai-multi-agent-upgrade/run_20261021_final_delivery/backups/gateway.sqlite qldapm-ai-gateway-1:/state/gateway.sqlite
   docker restart qldapm-ai-gateway-1
   ```
