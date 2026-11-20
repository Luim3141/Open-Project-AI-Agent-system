# Phase2 current — 01/11/2026

Phase2 current: engineering_delivery.py resume advances pastdone reworkattempts and resumesknown interruptedreworkwithoriginalfeedback. Candidate-N.diff is preserved whenreviewNdone. Initialtreehashfence, terminalknownGatewayguard and no-replayunknown remain. Reviewfoundbothbugs, RED/GREEN+independentre-review savedphase2. Historicalsuccessprojectionadded; no directDBrepair.

---

# Core engineering fixes

Chi tiết root cause, RED/GREEN commands và snapshots tại [core-audit.md](core-audit.md).

Ba sửa đổi có phạm vi hẹp:

1. `automation/engineering_worker.py::agent_process`: AUTO và RUN_ONCE tiếp tục polling; giữ deadline/OFF/PAUSED/CANCEL fence.
2. `gateway/engineering_lifecycle.py::resume`: source_matches và pending Native request lookup dùng run.actor_id sau authorization, không dùng actor người thao tác làm receipt owner.
3. `gateway/store.py::claim_run`: mode của OpenClaw queue được kiểm lại bên trong BEGIN IMMEDIATE, trước claim; không thay scheduler của generic queue.

Tests dùng SQLite temp, fake Native, mock subprocess và concurrent claim; không chạy OpenClaw/Gemini thật. Snapshot byte-for-byte trước sửa ở backups/core với manifest before/after. Không đổi ownership, schema workflow hoặc hoàn tất WP379. Worker process đang chạy đã load code cũ có thể cần restart có kiểm soát khi rollout; chưa tự terminate task/WSL.

Intake409 và lock contention lịch sử chưa được coi là giải quyết chỉ bằng core tests. Run b1c có metadata bị sửa thủ công; điều tra trong WP385_FORENSICS.md. Không replay run này hoặc tự phục hồi xóa WP.
