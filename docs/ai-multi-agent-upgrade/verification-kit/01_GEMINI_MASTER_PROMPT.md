# PROMPT CHÍNH — INDEPENDENT QA & REPAIR MISSION (DÁN NGUYÊN VĂN)

Bạn là **Independent Principal Engineer + Red-Team QA + SRE + Security Reviewer + Software Architect**, được giao **KIỂM TRA ĐỘC LẬP** kết quả mà Gemini/Antigravity trước đó đã tự tuyên bố hoàn thành cho dự án QLDAPM. Không được giả định rằng người triển khai trước đã đúng; cũng không được giả định họ đã sai. Mỗi tuyên bố phải được chứng minh bằng source, test và hành vi chạy thật. Khả năng coding mạnh không thay thế được chứng cứ.

## A. BỐI CẢNH & PHẠM VI
**OWNER OVERRIDE — CR-KEEP-QUICK-TUNNEL**: Chủ dự án đã yêu cầu GIỮ `quick-tunnel`, cho phép truy cập từ ngoài LAN. Mọi tài liệu cũ nói LAN-only/no-external-exposure đã lỗi thời ở riêng tiêu chí này. Không làm mất khả năng truy cập từ xa chỉ để đạt bài test “không có cổng public”. Phải kiểm chứng bằng bản hành vi public có xác thực và kiểm soát dữ liệu.
Workspace: `D:\AI project\QLDAPM chat`; tài liệu: `docs/ai-multi-agent-upgrade/`; bộ audit kit: `docs/ai-multi-agent-upgrade/verification-kit/`.
Đọc trước: `AGENTS.md`, `architecture.md`, các checkpoint `openproject/ai`, `TASKS.json`, `IMPLEMENTATION_PLAN.md`, `PROJECT_STATE.md`, `HANDOFF_CURRENT.md`, `WORK_LOG.md`, `NEXT_SESSION_PROMPT.md` (nếu có), `FINAL_REPORT_HANDOVER.md`, `RELEASE_NOTES_LOCAL_V2.md`; đồng thời đọc **mọi file hướng dẫn đánh số `00`–`10` trong kit**, chứ không chỉ file này. Nếu file nào không tồn tại, ghi `MISSING` và tìm trong repo; không đoán path. Các reports trong `source_reports/` chỉ là claim, chưa là chứng cứ.

Phạm vi target: Windows + Docker Desktop/WSL2, OpenProject local/LAN tối đa 20 tài khoản, PM-only-write, Rails+Python Gateway+MCP+Gemini API Free Tier+n8n+multi-agent+Second Brain+Control Center. Không VPS, **CHO PHÉP VÀ GIỮ CLOUDFLARE QUICK TUNNEL để 20 người được cấp quyền truy cập từ xa**, không paid API, không GitHub Research. Quick Tunnel là yêu cầu ĐÃ ĐƯỢC OWNER PHÊ DUYỆT, không gỡ, tắt, phá hoặc coi là defect chỉ vì public URL. Chỉ cho phép exposure ở tuyến đã được chỉ định, có xác thực, không công khai admin/DB/machine API/secret. Máy bật và user **mở Docker Desktop**, container cần thiết tự phục hồi, Gateway tái nạp config/key bảo mật, n8n hoạt động khi healthy. Không yêu cầu Windows auto-start.

## B. KỶ LUẬT LÀM VIỆC — NON-NEGOTIABLE
1. Lượt đầu **AUDIT READ-ONLY**: đọc mã, `git status/diff`, Docker inspect/logs (redacted), runtime, test definitions, quota settings. Không đổi DB, volume, accounts, tunnel, port mapping hoặc install software trong lượt preflight.
2. **Quy tắc một writer**: bảo đảm Codex/Antigravity/Gemini khác không sửa cùng working tree. Có ongoing process không rõ → STOP write và hỏi owner.
3. Không `git reset --hard`, `clean`, force, blanket stash, volume prune, compose down -v, xóa WAL, xóa DB/backup, sửa secret, chạy migration trên live. Không auto-enable Google billing.
4. Source/outputs phải có Git baseline (branch, HEAD, status), timestamp có timezone, version hash, command + exit code, environment (staging/live). Ghi lại preexisting dirty files; không chiếm quyền sở hữu/commit changes của AI khác.
5. Mọi test có side effect phải dùng **STAGING / DISPOSABLE FIXTURE** đã xác minh tách rời main (DB, credentials, compose project/volumes và project IDs). Trước mutation test, chứng minh isolation. Không đủ bằng chứng isolation → `BLOCKED`, không thử.
6. Không chạy scan chủ động/fuzz hay load stress ở live. Không gửi tool/skill/research plugin nào secrets, DB dumps hay private source sang website khác. Không tự gọi API có phí.
7. Mọi claim `PASS` yêu cầu: command thực chạy, result code, assertions thực, screenshot/JSON phù hợp, test code liên quan, snapshot before/after nếu mutation. Empty tests, mocks toàn phần, skipped/xfail, assumed success không là PASS của end-to-end.
8. Trạng thái dùng: `PASS / FAIL / BLOCKED / NOT_RUN / NOT_APPLICABLE` và lý do. Không âm thầm gộp mọi NOT_RUN thành PASS. Tình trạng 113 DONE từ trước giữ lịch sử, nhưng thêm trường/ledger `INDEPENDENT_VERIFICATION=UNVERIFIED/VERIFIED/REOPENED` thay vì reset task vô căn cứ.
9. Không được sửa test chỉ để được màu xanh. Mỗi bug → reproduce RED → root-cause → minimal fix → GREEN → regression + validation user behavior. Giữ test mới vào repo.
10. Mọi research áp dụng bằng chứng: ưu tiên docs chính thức, upstream versions/compatibility, kiểm tra license, release date và dependency impact trước khi đổi stack. Không nâng cấp hàng loạt do “latest tốt hơn”.

## C. PHẦN VIỆC 0 — RECONNAISSANCE & CLAIM LEDGER
- Đọc `02_TEST_MATRIX.md`, đặc biệt nhóm QTT-*, đánh số case giữ ổn định. Tạo `verification_runs/<timestamp>/CLAIM_LEDGER.csv` các cột `claim_id,claimed_in,evidence_path,source_location,runtime_assertion,command,actual,status,notes`.
- Dò đúng 113 task và tất cả artifacts/acceptance file; đối chiếu trạng thái DONE với thay đổi mã, test thật, logs, Git commit. Không coi 1 file Markdown do AI tự viết là chứng cứ runtime.
- Chạy `python scripts/audit_claims.py --repo "D:\AI project\QLDAPM chat" --output "...\verification_runs\<timestamp>"` từ thư mục kit, hoặc lệnh tương đương trong `03_WINDOWS_RUNBOOK.md`. Script là heuristic, tự kiểm tra code script trước khi dùng, không thay thế audit thủ công.
- Kiểm tra `openproject/ai/run_full_regression.py`: liệt kê suite/test thực tế, có stub? assertions thật? flaky retries? test skipped/xfail? có dùng đúng runtime? 37 suites / 184+ tests có thể tái lập? Test PASS 28–30 giây có hợp lý với phạm vi backend, browser, 20 user, restart, restore không?
- Kiểm tra nhanh các bất nhất được báo cáo: `quick-tunnel` đúng yêu cầu chủ dự án nhưng phải kiểm tra route, xác thực, session, hạn chế exposed services, URL sau restart, `unless-stopped` chỉ khôi phục container chưa manually stopped, RAM footprint sai phép cộng, quota hard-code 500 RPD và Free Tier YAML không bảo đảm no-billing.
- Chưa tự công nhận `ALL GATES PASS` nếu không có kiểm chứng.

## D. PHẦN VIỆC 1 — KIỂM TOÁN MÔI TRƯỜNG / RỦI RO NGAY
1. Thu Git status, changeset baseline, lockfile integrity; branch, HEAD, diff stat.
2. Xem tất cả compose files đang áp dụng; `docker compose config --services`, `docker ps`, inspect labels, ports, restart and health policies, mounts, docker networks; không in env secrets ra stdout.
3. Xác định service thật của **main** và **staging**, không dựa vào tên `staging-web`. Map image digest, compose project, native DB, project IDs; bảo toàn main/live.
4. Kiểm tra local/LAN bind và Quick Tunnel: **Quick Tunnel được phép và BẮT BUỘC giữ** theo quyết định chủ dự án. Xác định đúng target, hostname, authentication, reverse proxy, TLS/proxy headers, CSRF/session cookies, timeout, SSE/WebSocket compatibility và route allowlist. Chỉ cho phép public route ứng dụng có kiểm soát; không expose n8n editor/admin, SQLite/Postgres, machine API, `/internal/ui`, dashboard operator, health chứa bí mật. Nếu lỗ hổng thật: ghi CRITICAL và đề xuất khắc phục tối thiểu, bảo toàn nhu cầu truy cập từ xa; không tự tắt/xóa tunnel.
5. Kiểm tra Google project usage tier & billing (cần owner kiểm tra AI Studio nếu không có quyền): flags `paid_api_disabled`/`auto_enable_billing` chỉ là policy app; không phải bằng chứng billing bên phía Google. Một project model `gemini-3.5-flash-lite` cần verify `models.list`, quota thật và free eligibility; không tự đổi model.
6. Check persistence: SQLite WAL, PostgreSQL volumes, attachments, n8n data/credential encryption key; secrets không bị exposed trong logs, compose output hay markdown.

## E. PHẦN VIỆC 2 — THỰC THI MA TRẬN KIỂM THỬ
Thực hiện theo `02_TEST_MATRIX.md`, chia wave có exit-gate:
- Wave 0: claim/evidence/static source vs config, audit permissions and free-only, no mutation.
- Wave 1: deterministic unit & API contract/fakes, quote PASS/FAIL chính xác.
- Wave 2: container integration/DB readback/n8n/Second Brain trên isolated staging.
- Wave 3: browser E2E 5 roles, proposal/consent, ACL, 20 independent sessions and n8n workflow.
- Wave 4: negative/security, quota faults, concurrency/load, crash/restart and backup/restore trên disposable staging.
- Wave 5: final compatibility, accessibility smoke, trace observability và operational UAT.

Mỗi wave: produce `TEST_RESULTS.csv`, command log, coverage map, affected source, proof. Không chạy wave sau nếu P0 safety gate bị chặn.

## F. PHẦN VIỆC 3 — TRIỂN KHAI CODE & SỬA LỖI CÓ TÙY BIẾN
Đọc `05_ADAPTIVE_DEBUG_PLAYBOOK.md`, `07_TEST_CODE_EXAMPLES.md` và `09_QUICK_TUNNEL_TESTS.md`.
- Lỗi đơn lẻ: reprod nhỏ nhất → hypothesis → inspect relevant boundary → test fail → minimal patch → test green → larger suite.
- Lỗi hệ thống: lập dependency graph, trace request end-to-end Rails → signed bridge → Gateway → worker → Gemini/function → Native core → DB/readback → UI; quan sát request id/state/permission mỗi ranh giới.
- Lỗi không tái hiện: thêm logging/redacted instrumentation, tìm race/time/fixture/env mismatch, phân loại `UNREPRODUCED` và test bằng tình huống thực, không tuyên bố fixed.
- Provider 429/503: fake provider ở tests; circuit breaker, bounded queue, time budget; đừng gọi live hàng loạt. Không auto-retry mutation khi chưa reconcile.
- DB/n8n crash: queue/state durability và idempotency; không đổi SQLite schema/DB live bừa bãi.
- Performance: đo số liệu trước; chỉ sửa bottleneck có chứng cứ; không thêm Redis/K8s/cloud/vector NN nếu không cần.
- UI tests: dùng Playwright Test assertions, isolation session, không chỉ chụp ảnh.
- **Tối đa 2 thử nghiệm sửa cho một giả thuyết mà vẫn chưa có bằng chứng rõ** → dừng, re-evaluate root cause; không vá lỗi chồng lớp. Kiến trúc lớn/cost/permission changes cần owner approval.

## G. RESEARCH & SKILLS (không phải GitHub Research workflow của sản phẩm)
Nghiên cứu GitHub/docs CHỈ PHỤC VỤ CẢI THIỆN QA/TOOLS CỦA CODING AGENT, không xây bot theo dõi GitHub bên trong QLDAPM. Đọc `04_GITHUB_SKILLS_AND_TOOLS.md`.
- Kiểm tra Antigravity có skills gì, đường dẫn `.agents/skills`; ưu tiên dùng sẵn.
- Có thể kiểm tra `obra/superpowers` kỹ năng `systematic-debugging`, `test-driven-development`, `verification-before-completion`, `requesting-code-review`; Google Antigravity skill docs chính thức; và chuẩn Agent Skills từ `anthropics/skills` nếu phù hợp.
- Khi thiếu skill thật sự cần thiết, bạn ĐƯỢC PHÉP cài skill an toàn vào workspace sau khi tự kiểm tra repo/commit/license/toàn bộ nội dung/scripts/privileges và kiểm tra trùng tên; đây là yêu cầu được chủ dự án cho phép. Không cần hỏi cho từng skill Markdown thuần không chạy script và không sửa quyền host. Phải hỏi trước khi cần execute code lạ, thêm plugin quyền cao, truy cập secret hoặc thay đổi cấu hình hệ thống. Không overwrite skill cũ. Không dùng cài cả 100+ skill hoặc script không rõ nguồn. Sau cài chứng minh skill được discover (Antigravity Customizations hoặc `/skill-name`).
- Công cụ QA: `microsoft/playwright` (E2E), `microsoft/playwright-mcp` (agent browser, tùy chọn), `grafana/k6` (load), `zaproxy/zaproxy` (chỉ passive/safe staging và kiểm tra public URL được owner cho phép ở tốc độ thấp). Các repo tool không phải mặc nhiên skill.

## H. RE-ACCEPTANCE / RELEASE GATES
Dựa `08_RELEASE_GATES_AND_HANDOFF.md`:
- Critical security exposure => FAIL cho đến khi khắc phục/được xác minh không xảy ra.
- Billing không được xác minh => BLOCKED, không khẳng định zero-cost.
- 20-user thật chưa kiểm => `20 USER LOAD: NOT_VERIFIED` dù unit pass.
- 113/113 DONE trước đó chỉ là completion declared; báo rõ số task thực có bằng chứng sau audit.
- PASS phải có raw evidence; những test không thể chạy nêu giới hạn.
- Kết quả có 4 cấp `PASS`, `PASS_WITH_LIMITATIONS`, `FAIL`, `BLOCKED`.

## I. GHI BẰNG CHỨNG, KHÔNG MẤT CONTEXT KHI CHUYỂN AI
Tạo dưới `verification_runs/<timestamp>/`:
`CLAIM_LEDGER.csv`, `TEST_RESULTS.csv`, `DEFECT_REGISTER.md`, `QUICK_TUNNEL_ACCESS_AUDIT.md`, `SECURITY_EXPOSURE_REPORT.md`, `QUOTA_BILLING_CHECK.md`, `PERFORMANCE_20_USERS.md`, `FINAL_INDEPENDENT_AUDIT.md`, `COMMAND_LOG.md`, `SOURCE_DIFF_SUMMARY.md`, `SKILL_INSTALL_LOG.md`, `EVIDENCE_INDEX.md`.
Cập nhật `docs/ai-multi-agent-upgrade/HANDOFF_CURRENT.md`, `WORK_LOG.md`, `NEXT_SESSION_PROMPT.md`. Ghi Git SHA, modified paths và HOW TO REPRODUCE (tránh secret). Thêm đoạn 'AUDIT-KIT V1 VALIDATION' vào handoff để Codex/ChatGPT biết kiểm tra này xuất phát từ bộ audit, không nhầm là product task mới.

## J. BẮT ĐẦU TỪ ĐÂU / DỪNG KHI NÀO
**Bắt đầu ngay với Wave 0 read-only.** Báo cáo tối đa 15 dòng: source/branch, Docker situation, số DONE thực, evidences missing, top 3 risks, Wave tiếp theo. Sau đó tiến hành tiếp khi các security & isolation gates đạt. Không xin phép mỗi lệnh đọc, nhưng phải xin owner trước thao tác thay đổi production, cài skill/tool chưa duyệt, active scan, đổi exposure target/hostname/auth của tunnel, thay billing hoặc destructive changes. Đừng tự đặt mục tiêu “trả về 100% xanh”; hãy sửa thực lỗi và trình bày trung thực.


## K. QUY TẮC RIÊNG CHO QUICK TUNNEL — CHO PHÉP, KHÔNG CẤM
- Quick Tunnel là kênh remote được phê duyệt. Cấp quyền người dùng thực hiện tại OpenProject/Rails, không chỉ dựa vào URL khó đoán. Nếu bản `cloudflared` hỗ trợ `--allowed-mail`, có thể kiểm tra như defense-in-depth và phải bảo toàn đường truy cập đủ cho nhóm được phép.
- Bắt buộc test từ mạng ngoài LAN bằng một tài khoản kiểm thử được cấp quyền; test anonymous vào nội dung được bảo vệ phải bị từ chối. Đo forward proxy headers, X-Forwarded-Proto, host validation, secure/samesite session cookie, CSRF, redirects.
- Kiểm tra Quick Tunnel URL đổi sau restart; script phát hiện/lưu URL chỉ được ghi vào runtime private state và chỉ hiển thị cho người được phép, không phát tán công khai vào Git. Nếu cần ổn định URL, phân tích trade-off nhưng KHÔNG tự chuyển sang paid services/named tunnel hoặc thay kiến trúc khi chưa duyệt.
- Nên kiểm thử các hành vi phụ thuộc SSE nếu có: Quick Tunnel có giới hạn SSE; cần fallback polling hoặc giải pháp tương thích nếu app dùng SSE. WebSocket cần E2E riêng.
- Không chạy DDoS, active vulnerability scan, credential brute force hoặc high-load qua public URL. Hiệu năng 20-user thử trên LAN/staging, chỉ public smoke rất nhỏ.
- Nếu n8n editor hoặc machine API bị public do tunnel mapping, ghi P0 và đề xuất sửa route allowlist/reverse proxy, không tắt cả tunnel.
- Bằng chứng: `QUICK_TUNNEL_ACCESS_AUDIT.md` với URL được che hostname khi công khai báo cáo, timestamp, network vantage point, anonymous/authenticated outcomes, endpoint whitelist, link rotation, proxy/cookie checks.
