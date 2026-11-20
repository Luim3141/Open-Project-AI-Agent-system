# BIÊN BẢN NGHIỆM THU — TASK P10-07
## Local-Only Release Cho Tối Đa 20 Người Sau Owner Approval; Tuyệt Đối Không VPS/WAN

- **Mã Task:** `P10-07`
- **Giai đoạn:** Phase P10 — Local main release + no-touch Docker runtime handover
- **Ngày hoàn thành:** 2026-10-17
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** DONE
- **Tiêu chí nghiệm thu:**
  - Đạt tiêu chuẩn Stage Qualification (36 suites, 180+ tests PASS 100%) và Restore Drill (Postgres dump, tar assets, SQLite WAL với SHA-256).
  - Phê duyệt phát hành cục bộ (Local Main Promotion) dưới sự kiểm soát tường minh của Chủ dự án (Owner Approval Token).
  - Tuyệt đối không tự động phát hành (zero auto-promote: `can_auto_promote = False`).
  - Phạm vi phát hành nghiêm ngặt chỉ chạy trên máy chủ Windows cục bộ qua mạng LAN (tối đa 20 người dùng), tuyệt đối không mở WAN/VPS. Phụ thuộc `P10-06`.

---

### 1. Bằng Chứng Đánh Giá 4 Cổng Kiểm Soát (Release Gate Assessment)

- **Công cụ kiểm soát:** [`openproject/ai/release_gate.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/release_gate.py).
- **Kết quả đánh giá 4 Cổng:**
  1. `[PASS] Restore Drill Gate`: Toàn vẹn cơ sở dữ liệu Postgres, n8n encryption key, và SQLite WAL đạt `PRAGMA integrity_check = ok`.
  2. `[PASS] Parity Check Gate`: Cấu hình `MODEL_ALLOWLIST.json` tuân thủ nghiêm ngặt chính sách `FREE_ONLY` và mô hình 20 người dùng LAN.
  3. `[PASS] Source Freeze Gate`: Xác thực trạng thái Git an toàn trên nhánh `codex/local-multi-agent-upgrade` tại commit `de7fe8f10e`.
  4. `[APPROVED] Owner Approval Gate`: Cơ chế xác thực Token phê duyệt `OWNER_APPROVED_LOCAL_MAIN_20261017` hợp lệ.
- **Ràng buộc bất biến:**
  - `can_auto_promote = False` (nghiêm cấm mọi hành vi tự động vượt rào).
  - Hệ thống chỉ được cấp phép phát hành nội bộ cho tối đa 20 người dùng mạng LAN nội bộ.
