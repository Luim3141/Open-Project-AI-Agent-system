# BIÊN BẢN NGHIỆM THU TASK P09-05
## Diễn tập Sao lưu và Khôi phục Dữ liệu (Backup & Restore Drill)

- **Mã task:** `P09-05`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (3/3 restore drill tests PASS, 10/10 local backup tests PASS)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Diễn tập và chứng minh khả năng sao lưu (Backup) và phục hồi (Restore) toàn diện, nhất quán cho toàn bộ các thành phần dữ liệu của hệ thống QLDAPM Local Multi-Agent: SQLite WAL (AI Gateway store), PostgreSQL (OpenProject core), và n8n Community (Workflows + Encryption Key).
- **Tiêu chí chấp nhận:**
  - **SQLite WAL Consistent Snapshot:** Sử dụng SQLite Online Backup API (`sqlite_snapshot`) kết hợp temp copy, không bao giờ mở file snapshot ở chế độ ghi trên mount nguồn. Sau khi phục hồi tại vị trí mới, lệnh `PRAGMA integrity_check` phải trả về `ok`, số lượng bản ghi proposals và token balance nguyên vẹn 100%.
  - **n8n Encryption Key & Owner Credentials:** Sao lưu và phục hồi đầy đủ khóa mã hóa `encryptionKey` và thông tin quản trị `owner.json`. Nếu file khóa hoặc DB bị thiếu, cơ chế fail-closed phải từ chối khởi động (`CREDENTIAL_BACKUP_REQUIRED`).
  - **PostgreSQL & Assets Archive:** Quy trình tạo file nén `.tar.gz` kèm bảng checksum SHA-256 (`archive()`). Khi giải nén phục hồi vào môi trường staging, từng file phải khớp chính xác 100% hash sha256.
  - Tuyệt đối không cần cloud bên ngoài, không cần VPS, toàn bộ kịch bản chạy an toàn trên host Windows cục bộ.

---

### 2. Các kịch bản kiểm thử đã thực hiện
1. **SQLite WAL Snapshot & Restore Roundtrip:**
   - Tạo DB với `PRAGMA journal_mode=WAL`, chèn 100 bản ghi proposals và số dư token.
   - Chụp snapshot qua `sqlite_snapshot()`, phục hồi ra file DB độc lập.
   - Kết quả: `PRAGMA integrity_check` trả về `ok`, 100/100 proposals và token balance được khôi phục chính xác.
2. **n8n Credentials & Encryption Key Roundtrip:**
   - Kiểm tra `owner.json` chứa `encryptionKey` 256-bit và password.
   - Sao lưu qua `backup_n8n_owner()`, giải nén và phục hồi.
   - Kết quả: Nội dung JSON và key mã hóa trùng khớp từng byte.
3. **Backup Archive & SHA-256 Manifest Verification:**
   - Nén thư mục chứa database dump, file cấu hình và token.
   - Giải nén ra thư mục restore độc lập, tính toán lại hash sha256 của từng file.
   - Kết quả: 3/3 files khớp hoàn toàn với manifest gốc.

---

### 3. Bằng chứng kiểm thử tự động
1. **File diễn tập khôi phục:** [`openproject/ai/tests/test_backup_restore_drill.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_backup_restore_drill.py)
```text
...
----------------------------------------------------------------------
Ran 3 tests in 0.175s

OK
- test_sqlite_wal_backup_and_restore_roundtrip: PASS
- test_n8n_encryption_key_and_credentials_backup_restore: PASS
- test_backup_archive_manifest_checksum_verification: PASS
```

2. **File kiểm thử sao lưu SQLite & Secrets:** [`openproject/ai/tests/test_local_backup.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_local_backup.py)
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.520s

OK
```
