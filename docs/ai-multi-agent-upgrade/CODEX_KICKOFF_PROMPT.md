# MASTER PROMPT — CODEX NÂNG CẤP QLDAPM LOCAL 5 USERS, FREE-ONLY, DOCKER START = READY

**OWNER OVERRIDE15/10/2026:** user thay Radmin bằng Cloudflare Quick Tunnel và bỏ prerequisite thử Radmin từ máy khác, yêu cầu tiếp tục. Cho phép public HTTPS **chỉ OpenProject** với native login/5accounts/private projects; Gateway/DB/n8n vẫn private. Localhost18090 hiển thị URL hiện tại tự cập nhật khi tunnel đổi hostname. Điều này thay giới hạn no-tunnel/public-access và Radmin/client-CA trong bản gốc bên dưới; không thay free-only/RBAC/native gates/data/release approvals hoặc giả kết quả5client. TASKS giữ stable IDs, P01-11 có owner_scope_changes/acceptance mới và evidence thật trước DONE.

Bạn là implementation owner của codebase **CÓ SẴN** QLDAPM. Hãy triển khai có kiểm thử, không tạo repository/ứng dụng quản lý dự án mới.

## Nguồn và vị trí

- Authoritative workspace: `D:\AI project\QLDAPM chat`. Legacy folder trong Documents chỉ là pointer; không sửa legacy.
- Upgrade plan: `docs/ai-multi-agent-upgrade/` gồm `START_HERE.md`, `TASKS.json`, `IMPLEMENTATION_PLAN.md`, `ARCHITECTURE_TARGET.md`, `FREE_TIER_POLICY.md`, `GEMINI_FREE_QUOTA_PLAYBOOK.md`, `LOCAL_WINDOWS_RUNBOOK.md`, `FIVE_USER_LAN_ACCESS.md`, `TEST_AND_RELEASE_GATES.md`, `USER_ACCEPTANCE_DEMOS.md`, `PROJECT_STATE.md`, `CODEX_SESSION_PROTOCOL.md`, scripts và handoff.
- Đọc `AGENTS.md`, `openproject/ai/README.md`, đầu `CHECKPOINT.md`, `DATES_CHECKPOINT_2026-10-15.md`, `RBAC_CHECKPOINT_2026-10-15.md`, những test/source hiện hành, rồi đối chiếu handoff. Handoff là snapshot chưa xác minh runtime; source+test hiện tại mới là căn cứ sửa.

## OBJECTIVE (không tự diễn giải khác)

Xây **QLDAPM Multi-Agent cho đúng 5 người dùng LAN** (PM, BA, FE, BE, QA) trên **Windows hiện tại + Docker Desktop/WSL2**. Dùng OpenProject/Gateway hiện có, thêm Supervisor và agent phù hợp, n8n Community, Second Brain nội bộ, quota/trace/dashboard. **Không VPS, không public Internet access, không Kubernetes, không HA/scale lớn, không GitHub Research/crawler, không paid APIs, không subscription mới.**

**Vận hành đích:** sau INITIAL PROVISIONING, hằng ngày người dùng **CHỈ MỞ DOCKER DESKTOP** (Windows đã khởi động), các container đã được provision tự phục hồi, OpenProject + n8n + Gateway + Supervisor lên READY, private Gemini key/project hiện có được load lại **không hỏi nhập key hoặc chạy Compose nữa**. Không bật auto-start khi Windows sign-in/boot, không Task Scheduler. Nếu user manually stopped containers thì khôi phục 1 lần bằng admin repair script; ghi rõ giới hạn `unless-stopped`. Quota/Google outage có degrade rõ, không thể cam kết provider READY giả.

**Chi phí:** baseline = Google AI Pro đã sở hữu + Gemini API **Free Tier** + stack self-host free theo đúng license; ***AI Pro không nâng Free API quota.*** Verify project+model Free Tier thực tế (RPM/TPM/RPD/TPD) và dùng tối đa hợp lệ bằng fair queue/efficient deterministic routing, không vượt/né limits, không bật billing/prepay/credit, không dùng consumer OAuth/cookie làm backend. Giữ API key private hiện có, không yêu cầu cấp lại nếu hợp lệ.

## SAFETY ABSOLUTES

1. Không dùng `git reset --hard`, stash/clean tự động, overwrite dirty working tree; tuyệt đối không chạy `docker compose down -v`, prune volumes, delete SQLite WAL, destructive seeder, migrate live tùy tiện.
2. Không tự promote từ staging sang main (main 8088/8090, staging 18091/18092) trước stage tests + backup/restore + owner approval. Cuối kế hoạch phải **có local main release nếu approved**, không dùng VPS/deploy cloud.
3. Bảo toàn signed bridge, PM-only-write, roles BA/FE/BE/QA non-write, native gates, reviewer independence, consent/proposals, idempotency, readback receipts, private audit.
4. Không cho business AI/n8n tool shell/admin/Docker socket; local operator riêng không bị gộp với Gemini business functions.
5. N8n editor chỉ localhost admin, machine API identity read-only; 5 users truy cập OpenProject qua LAN HTTPS/auth; không public DB/Gateway/n8n, không Router port-forward hoặc tunnel.
6. Source note: current Gemini model in snapshot `gemini-3.5-flash-lite` không đồng nghĩa có Free Tier; verify tại AI Studio. Nếu provider key/model/tier không hợp lệ thì BLOCKED/DETERMINISTIC, **không trả phí để fix**. Không gửi dữ liệu mật/PII lên Free Tier khi chưa đủ quyền/terms.
7. Chạy unit + integration + role matrix + fault test; DONE cần evidence thực và test PASS/NOT_APPLICABLE lý do; **trạng thái ban đầu là 0%**.

## IMPLEMENTATION PROTOCOL — BẮT BUỘC

1. Chạy `python docs/ai-multi-agent-upgrade/scripts/progress.py validate` và `report`; đọc `TASKS.json` các ID P00-P10, dependency, acceptance. Nếu user từng triển khai với plan cũ, **MERGE theo stable task ID**, không đè 0% lên tiến độ thật, giữ evidence/notes/receipt.
2. P00 AUDIT trước: đọc code/checkpoints, kiểm tra dirty source, baseline images/DB, validate 5-user scope, backup/restore staging, license Docker/n8n và Free API tier/model/quota. Không chạy cost-incurring smoke khi chưa xác minh Free.
3. Làm theo gates, bắt đầu task đầu tiên ready. Với mỗi task: ghi `IN_PROGRESS`, mô tả file tác động, implement vertical slice, chạy test, ghi evidence redacted, chuyển REVIEW rồi DONE nếu test đạt. Sau mỗi task `progress.py report`, cập nhật `PROJECT_STATE.md`.
4. Phase P01: implement persistent `restart: unless-stopped`/health/recovery cho toàn stack đã provision; **KHÔNG startup service Windows**. Test user tắt/mở Docker 3 vòng, key không yêu cầu nhập lại, 5 LAN users login native.
5. P02: shared free quota manager, priorities/5-user fairness/adaptive 429/503; Gemini client lấy key private đã cấu hình; provider readiness != host health.
6. P03-P05: durable run state, n8n Community (1 owner editor), Supervisor + PM/BA/QA/DEV Reviewer; không GitHub Research hoặc code-deploy agent. n8n schedule phải đi qua gateway scope/permissions, không native writes tự động.
7. P06-P08: knowledge nội bộ, role-ACL FTS, daily/weekly report, deadline risk, workload imbalance, AC/test readiness; dashboard owner/agent/quota. Không web research.
8. P09-P10: test 5 concurrent LAN clients, RBAC/safety, backup/restore and Docker manual-start; local main promote **chỉ với owner approval** và release note/rollback.
9. Nếu thiếu account entitlement/data/host capability, ghi BLOCKED lý do rõ và phương án free, không yêu cầu mua add-on. Nếu source có thứ đã hoàn thành, TEST+EVIDENCE trước khi marking DONE, không code trùng.

## MẪU BÁO CÁO SAU MỖI PHIÊN

```text
Branch/commit, environment, git status:
Task IDs changed [TODO/IN_PROGRESS/REVIEW/DONE/BLOCKED]:
Feature implemented and files changed:
Tests executed (real pass/fail/skip) and evidence:
Local startup status [Docker manual => core/gateway/agents/n8n]:
Gemini project/model free verified? key persisted? provider READY/WAITING/INVALID?:
5-user LAN HTTPS, PM-only-write, n8n machine role, data isolation:
Current quota snapshot and ZERO extra costs:
Risk, rollback and known issues:
Next 3 ready IDs:
```

**BẮT ĐẦU NGAY:** đọc toàn bộ kế hoạch + source; báo cáo P00 audit và 3 task đầu. Không tự cài/sửa main trước khi xác minh backup, source parity, runtime identity. Tiếp tục cho tới khi scope được kiểm thử hoặc có blocker thực, không giả vờ đã chạy.
