# Trạng thái sau Owner approval — MAIN đã đổi

Proposal30218aff đã được duyệt và áp dụng. Xem [MAIN_ROLLOUT_RESULT.md](MAIN_ROLLOUT_RESULT.md) và `rollout-20261101T110426Z/deployment-result.json`. Các đoạn NOT_DEPLOYED/AWAITING_OWNER_APPROVAL phía dưới là pre-rollout snapshot, không phải trạng thái hiện tại. Chưa human acceptance/full business E2E.

---

# Gateway lifecycle → n8n — Phase2

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

`gateway/execution_events.py` enqueue cùng transaction với event gốc. `n8n_lifecycle_outbox.py` giữ stable event ID, atomic lease30s, timeout tổng3s qua cancellable async HTTP, cap ACK8192bytes trong lúc streaming, exponential backoff tối đa300s, DEAD sau5 lần lỗi. Chỉ Project6 và9 event types có thật; payload không có prompt/source/token. work_package_id/unit_id chưa có ở event source nên là null, không bịa mapping.

Dispatcher knowledge hiện hữu gọi publisher; không thêm coding scheduler. WF04 thêm adapter riêng; chữ ký HMAC expiry60s kiểm tại Gateway, cùng actor/project/run/event source. HTTP200 hoặc n8n green thiếu exact OBSERVED ACK vẫn RETRY. Observation dedup theo event_id; execution metadata chỉ giữ execution ID/thời điểm. Lỗi delivery lưu fixed code, không raw remote exception. DEAD visibility hiện qua bảng SQLite, chưa có dashboard riêng; kiểm bằng connection read-only.

Clone cuối `phase2-20261101T050128Z/n8n-clone-real-gateway-final.log` dùng actual Gateway ASGI lifespan + Service background dispatcher và n8n2.43.6 image mới. AGENT_STARTED được append trước Gateway startup; không gọi thủ công WF04 để giả publisher. Outbox ACKED sau3attempts (startup readiness retry),1observation, n8n execution1. Callback đi qua actual signed observation route. Source trace read và ACK được đối chiếu; Source event/consumer commit trước publisher crash + expired lease recovery có regression riêng.

Tests: outbox8, adapter1; đều nằm trong182Linux affected tests. Local slow-header/body fixtures chứng minh total deadline; HMAC/expiry/source tamper/cross-project/bearer denial, transaction rollback, duplicate/retry/DLQ/restart đều được thử. Signature sai không tạo observation.

Preview actual published WF04 `elfapV5D2PTnLiHW`, activeVersion `4a8ddd7c-763a-45dc-adb1-99633047b62e`:4old nodes giữ nguyên, thêm4nodes. Callback URL host.docker.internal:18089 dùng Host localhost:18089 đã có trong allowlist; không nới Host guard. Candidate JSON nằm private theo n8n-rollout-preview.json. MAIN chưa publish/configure/enable. Các WF khác vẫn là adapters theo matrix06; không ép generic commands vào coding Project6.
