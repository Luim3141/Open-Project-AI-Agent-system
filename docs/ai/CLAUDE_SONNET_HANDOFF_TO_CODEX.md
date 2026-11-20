# Claude Sonnet 5.5 → Codex handoff (QLDAPM Main)

Cập nhật sau mỗi milestone. Mục mới nhất ở trên cùng của "Milestones".

## Trạng thái hiện tại

- Writer đang hoạt động: **Sonnet** (từ 2026-10-27 02:20 +07). Codex dừng do hết quota; Argon chưa làm việc trên Main.
- Phạm vi: chỉ Main; không Staging; không Native write; không replay approval/model call.
- Release: **PARTIAL, không FULL GO** (blocker cũ của Codex vẫn còn, xem checkpoint).
- Nguồn tham chiếu: `CODEX_MAIN_CONTINUATION_CHECKPOINT.json` + `CODEX_MAIN_APPROVAL_CONSUMPTION_LEDGER.json`.

## Milestones

### M2 – Manager409 fix deployed và xác minh (xong, 02:28)
- Triển khai Gateway-only `qldapm-ai:codex-phase-stale-read-v1-20261027` (`sha256:e76038d4…`, container `3f883e32…`, healthy, 0 restart) bằng `deploy-phase-stale-read-sonnet.py prepare/apply`; script tự rollback nếu lỗi. Core và 9 container khác không đổi, 16 workflow n8n không đổi.
- Read-only trên Main: WP371 = status 37 (IN ANALYSIS), v4; 375 physical rows; 0 delete event; `phase_get` actor 18 và 19 đều HTTP 200 (`accepted`, `source_current=false`, `status_options=[]`); RAG 373/1739/1742, 338 visible, 3 unmatched legacy, sạch.
- 0 Native write, 0 model call, 0 human decision, không Staging.
- Rollback: gateway `sha256:7d7e39b3…` (chỉ image app; không restore DB).
- Hạn chế: không chạy actual Native clone riêng cho thay đổi 1 dòng này; bằng chứng live là `CLAUDE_SONNET_PHASE_STALE_READ_POSTDEPLOY_READONLY.json`.
- Artifact: `CLAUDE_SONNET_PHASE_STALE_READ_{DEPLOY_PREVIEW,DEPLOYMENT_RESULT,POSTDEPLOY_READONLY}.json`, `CLAUDE_SONNET_MAIN_CHECKPOINT.json`; `architecture.md` đã cập nhật.
- Lưu ý: trạng thái `status` trong DEPLOYMENT_RESULT là chuỗi kế thừa từ script Codex ("RUNTIME_REGRESSION_PENDING"); kết luận thực tế nằm ở file POSTDEPLOY_READONLY (PASS).

### M1 – Preflight + snapshot (xong, 02:24)
- Runtime Gateway/Core/n8n/Qdrant/Ollama khớp checkpoint; không có job ghi/test/deploy nền.
- Chỉ `gateway/native_phase.py` trên host khác runtime (bản vá Manager409 của Codex, 1 dòng).
- Snapshot trước khi sửa: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\sonnet-takeover-20261027\pre-edit-snapshot`.
- Chi tiết: `CLAUDE_SONNET_TAKEOVER_PREFLIGHT.json`.
- Codex đã qualification đầy đủ cho image candidate `qldapm-ai:codex-phase-stale-read-v1-20261027`
  (`sha256:e76038d4…`): Windows 606/606, Linux 591 pass + 15 skip. Hash `native_phase.py` trong image = host.
- **Chưa triển khai** bản vá lên Main tại M1.

## Việc tiếp theo (theo thứ tự)

1. (Xong ở M2) Bản vá Manager409 đã chạy trên Main.
2. Tiếp tục phần việc còn dở: thiết kế luồng Native-compatible fix/build/application-QA/retest/closure (WF09/WF11). Chỉ thiết kế, test offline và clone; mọi Native write cần phê duyệt chính xác mới của người dùng.
3. Giữ nguyên các blocker WF14, WF15, WF07/WF16.
4. Sau mỗi milestone: cập nhật `CLAUDE_SONNET_MAIN_CHECKPOINT.json` và file này.

## Không được làm

- Không chạy lại transition #371; không replay approval/model call đã `CONSUMED_DO_NOT_REPLAY`.
- Không khôi phục DB/checkpoint cũ; rollback chỉ ở mức image ứng dụng.
- Không sửa Staging; không tạo báo cáo PASS giả.

## Blocker còn lại (từ checkpoint Codex)

- WF14: 2 comment lịch sử unknown; full Qdrant restore bị chặn bởi policy.
- WF15: 3 point legacy chưa rõ nguồn (giữ, loại khỏi retrieval).
- WF07/WF16: gửi ngoài BLOCKED_CONFIGURATION; có local sink.
- Chưa có luồng đầy đủ fix/build/QA ứng dụng/retest/closure.
