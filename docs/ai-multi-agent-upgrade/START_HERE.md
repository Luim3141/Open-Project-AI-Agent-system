<!-- GEMINI_LIVE_CURRENT -->
# Trạng thái hiện tại — 2026-10-19T07:18:25.059814+07:00

**GEMINI_LIVE_STAGING_VERIFIED**. StagingGateway40cb4806/Core3b09393d; Gemini model/key hiện có hoạt động thật qua Supervisor + PM/BA/DEV/QA, aggregate/plan/usage/citations hiển thị trên Web. A–E/BE/BA-deny latestPASS;5rolelogin/TOTP/logout/CChistory/crossactor403PASS.178Windows/63Linux testsPASS;19generation/38HTTP phases,FREE_ONLY và savedkey được giữ. Billing OWNER_ATTESTED; không kiểm tra Console mới hoặc cam kết absolutezero.

Đọc [FINAL_LIVE_GEMINI_READINESS](gemini-live-deployment/FINAL_LIVE_GEMINI_READINESS.md), CSV và run_20261019_0013/CHECKPOINT.md trước mọi lịch sử bên dưới.18servinghealthy/17khác nguyênID,372WP/8privatefiles/RBAC/TOTP/tokens giữ;ServingNativewrites0. Backup cuối ba33c28b-2cf2-4ad7-b9b8-c50c69ad08df,3SQLitecoldrestorePASS.4clones stopped/dữliệu giữ. Main chưa promote,20usersDEFERRED,TOTP_DO_NOT_ROTATE. UXcaption local cònP3; không restartCore/Tunnel/DockerDesktop mới. Không hỏi lại key/G2 hoặc tự replay failedruns.
ACL progress/partial readback FIXED_AND_VERIFIED;5roleUI reopened on40cb,19generationcalls retained.
<!-- END_GEMINI_LIVE_CURRENT -->

# START HERE — QLDAPM Multi-Agent LOCAL cho 5 người, 100% free-only (V2)

**PHẠM VI CHỐT 15/10/2026:** giữ OpenProject hiện có; tối đa 5 người dùng trong mạng LAN (PM/BA/FE/BE/QA); sử dụng máy Windows hiện tại + Docker Desktop/WSL2; Gemini API Free Tier qua project/key hiện có; n8n Community; không VPS, không GitHub Research, không HA/scale lớn, không chi tiêu mới.

**YÊU CẦU TRỌNG TÂM:** chỉ cần người dùng **mở Docker Desktop** sau khi Windows đã hoạt động: những container đã cài đặt phải tự khôi phục, các UI/agents/n8n sẵn sàng và key/project Gemini đã lưu tự được nạp. **Không bật auto-start khi Windows boot/logon**; không yêu cầu chạy lệnh `docker compose up` hằng ngày, không hỏi nhập lại key hay login Google mỗi lần.

**Lần đầu vẫn cần triển khai một lần**: Codex kiểm tra source thật, thiết lập persistent secrets, provision containers, tạo 5 accounts, cấu hình LAN HTTPS/trust, xác minh model Gemini free và thực hiện restore/test. Nếu key hết hạn/quota 429/503, UI hoạt động nhưng chỉ hiển thị `WAITING_QUOTA`/`PROVIDER_UNAVAILABLE`/`BLOCKED_KEY`, tuyệt đối không tuyên bố AI READY giả. Không thể bảo đảm luôn có phản hồi Gemini khi bên Google gián đoạn.

## 3 bước đưa vào Codex

1. Giải nén file ZIP vào một thư mục tạm; sau đó **chép các file nằm BÊN TRONG thư mục `QLDAPM_CODEX_LOCAL_5_USERS_FREE_V2`** vào `D:\AI project\QLDAPM chat\docs\ai-multi-agent-upgrade` (không lồng thêm thư mục V2 ở giữa). Nếu đã có bản cũ/progress thật, **sao lưu, so sánh và merge trạng thái theo ID**, không ghi đè dữ liệu/evidence.
2. Mở Codex trong workspace `D:\AI project\QLDAPM chat` và dán nội dung **`CODEX_KICKOFF_PROMPT.md`**.
3. Để Codex kiểm toán P00 trên staging trước, sau đó thực hiện theo dependency. Chỉ ghi `DONE` khi test/evidence thực tế chứng minh; không báo thành công chỉ dựa vào plan.

## Xem tiến độ

```powershell
cd 'D:\AI project\QLDAPM chat\docs\ai-multi-agent-upgrade'
python .\scripts\progress.py validate
python .\scripts\progress.py report
python .\scripts\progress.py show --phase P01
```

Lưu bằng chứng có thể kiểm tra:

```powershell
python .\scripts\progress.py set P00-01 IN_PROGRESS --note "Audit source/runtime"
python .\scripts\progress.py set P00-01 REVIEW --note "Có bản kiểm kê"
python .\scripts\progress.py set P00-01 DONE --evidence "artifacts/P00-01-inventory.md" --tests PASS --note "Đã đối chiếu source + git status"
```

Tham khảo `IMPLEMENTATION_PLAN.md` (113 task có checkbox), `TASKS.json` (nguồn sự thật), `PROGRESS_DASHBOARD.md` (auto-generated), `LOCAL_WINDOWS_RUNBOOK.md`, `FIVE_USER_LAN_ACCESS.md`, `GEMINI_FREE_QUOTA_PLAYBOOK.md`, `TEST_AND_RELEASE_GATES.md` và `USER_ACCEPTANCE_DEMOS.md`.

**Tài liệu là kế hoạch, chưa sửa source/chạy Docker hoặc Gemini trên máy của người dùng. 0% cho đến khi Codex chứng minh được nghiệm thu.**
