# P04-10 accepted — 17Oct2026

Test restart Docker + schedule không chạy trùng / outage behaviour; nghiệm thu toàn bộ Phase P04.

## 1. Tóm tắt kết quả
- Đã kiểm tra và thẩm định toàn diện chính sách xử lý sự cố (outage), khởi động lại container/Docker, trễ lịch (missed schedule) và bù lịch (catch-up) cho cả 3 workflow n8n trong danh mục:
  1. **`qldapmManualStatus`**:
     - *Trigger*: `manualTrigger` duy nhất; trạng thái: `active: false`.
     - *Chính sách outage*: Không có lịch định kỳ (no schedule), không kích hoạt khi khởi động lại (`After startup: false`). Giữ nguyên trạng thái inactive khi restart. Chỉ chạy khi operator bấm nút thủ công; được bảo vệ bởi dedup request_key và nonce.
  2. **`qldapmDailyBrief`**:
     - *Trigger*: `scheduleTrigger` (`0 0 9 * * *` Asia/Bangkok) + `n8nTrigger` (`init` event - sau khi khởi động n8n) + `manualTrigger`. Trạng thái: `active: true`.
     - *Chính sách missed schedule / outage*:
       - Nếu hệ thống tắt qua mốc 09:00 Bangkok: Khi Docker/n8n khởi động lại, trigger `After startup` kích hoạt ngay lập tức để bù lịch trong ngày.
       - Cơ chế chống chạy trùng (Zero-duplication): Lệnh sử dụng `request_key = 'daily:' + $now.setZone('Asia/Bangkok').toISODate()`. Nếu trong ngày đã hoàn thành (kể cả khi restart container nhiều lần), Gateway phát hiện run đã tồn tại và trả về cùng receipt đã lưu (`same_daily_receipt: true`), không thu thập lại snapshot, không gọi Gemini API và không ghi đè dữ liệu.
       - Xử lý gián đoạn giữa chừng (crash midway): Lượt thu thập bị ngắt được đánh dấu `FAILED_NO_REPLAY` với `reconcile_required: true`, không tự động retry vòng lặp vô tận.
       - Không dồn tích lịch cũ: Nếu máy tắt nhiều ngày, khi bật lại chỉ thực hiện bù cho ngày hiện tại (Bangkok date), không sinh bão request cho các ngày đã qua trong quá khứ.
  3. **`qldapmWorkflowErrors`**:
     - *Trigger*: `errorTrigger` (`Workflow error`); trạng thái: `active: true`.
     - *Chính sách outage*: Hoạt động theo sự kiện lỗi phát sinh từ các workflow con; giữ nguyên trạng thái active sau restart; không kích hoạt lỗi giả lúc khởi động. Dedup theo execution key `error:<workflow_id>:<execution_id>:<day>`.

## 2. Bằng chứng kiểm thử và thẩm định (Evidence)
- **Kiểm thử đơn vị chuyên biệt (`openproject/ai/tests/test_n8n_outage_policy.py`)**:
  - `test_workflow_catalog_trigger_and_schedule_declarations`: PASS.
  - `test_missed_schedule_startup_catchup_creates_single_daily_receipt`: PASS.
  - `test_multiple_restarts_on_same_day_return_identical_receipt_without_duplication`: PASS (mô phỏng 5 lần restart liên tiếp trong cùng ngày, 100% trả về cùng receipt, không tạo thêm bản ghi nào).
  - `test_interrupted_outage_run_marked_failed_and_not_auto_replayed`: PASS.
  - `test_stale_or_expired_outage_command_rejected_at_gateway_boundary`: PASS (lệnh trễ quá hạn ngoài cửa sổ -15s..+60s bị từ chối với 403 `COMMAND_EXPIRED_OR_FUTURE`).
  - `test_error_workflow_outage_and_deduplication`: PASS.
- **Tổng hợp n8n test suite**: 27/27 tests PASS trong 1.265s.
- **Kiểm tra trạng thái live trên Staging (`http://localhost:5678`)**:
  - `qldapmManualStatus`: `active: false` (chính xác).
  - `qldapmDailyBrief`: `active: true` (chính xác).
  - `qldapmWorkflowErrors`: `active: true` (chính xác).
- **Trạng thái môi trường Staging**:
  - Toàn bộ 7 staging containers (`staging-gateway`, `staging-web`, `n8n`, `n8n-editor`, `db`, `local-backup`, `quick-tunnel`) đều `Up` và `(healthy)`.
  - Database OpenProject: 221 tables được bảo toàn nguyên vẹn.
  - Quota ledger: 471 records (0 Gemini API calls phát sinh).
  - Native business writes: 0.

## 3. Hoàn thành Phase P04
- Với việc hoàn thành Task P04-10, **11/11 tasks trong Phase P04 (P04-01 đến P04-11) đã hoàn thành 100%** có đầy đủ bằng chứng kiểm thử đạt chuẩn.
- **Phase P04 Gate: PASS**.
- Tiến độ tổng thể dự án: **55/113 tasks DONE (48.7%)**.
- Bước kế tiếp: Chuyển sang Phase P05 — Kiến trúc Supervisor Agent & Multi-Agent Role Coordination.
