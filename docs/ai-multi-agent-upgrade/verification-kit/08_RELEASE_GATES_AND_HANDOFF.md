# 08 — RELEASE GATES, CLAIM VERIFICATION, HANDOFF

## Mục tiêu
Không đổi kế hoạch triển khai 113 task thành 0%. Giữ `TASKS.json` lịch sử như cũ, **đính thêm một bộ sổ KIỂM TOÁN ĐỘC LẬP** trên 113 task. Kết quả Gemini 100% trước audit là `CLAIMED_DONE`, chưa phải `INDEPENDENT_VERIFIED`.

## Cấp độ bằng chứng
A. **Realtime observation**: công cụ hiện chạy và behavior có raw logs/trace/source SHA; đáng tin hơn.
B. **Reproducible local test**: runner có assertions, environment/version/fixture; cần kiểm source của test.
C. **Static artifact**: Markdown/screenshots/checkpoint nói PASS nhưng thiếu raw trace → chưa đủ E2E.
D. **Unverified statement**: tuyên bố không có artifact; phải ghi thiếu bằng chứng.

## Audit claims bắt buộc từ hai file Gemini
- CLM-001: `113/113 DONE` → so sánh 113 task IDs/source/acceptance artifacts, cả test và proof.
- CLM-002: `37 test suites, 184+ tests, 100% PASS` → đọc runner và chứng minh exit 0 và count thực; loại các skipped.
- CLM-003: `20 concurrent users` → 20 sessions độc lập với scope/tài khoản khác, không chỉ k6 20 VU GET login.
- CLM-004: `0 đồng tuyệt đối` → xác minh Google account/project billing/tier độc lập ngoài code flags.
- CLM-005: `Docker open -> all services healthy` → thực nghiệm engine restart (chỉ trên stage/an toàn; owner OK cho thử laptop).
- CLM-006: `Quick Tunnel no-touch remote` → tiếp tục hoạt động sau reboot bằng hostname hiện tại; URL rotation, HTTPS auth, no privileged exposure.
- CLM-007: `RAM 2.4–2.8GB` → đo memory thực dưới load, phân biệt host+containers+WSL; báo cáo có sai số.
- CLM-008: `Restore/backup validated` → thử phục hồi trên disposable environment, chứng minh schema+attachments+receipts.
- CLM-009: `n8n/second-brain/supervisor` → end-to-end tests với fixture, permissions, receipts/traces.
- CLM-010: `PM-only-write` → negative tests xuyên Rails UI/Core/API/MCP/tunnel.

## Gates
| Gate | Điều kiện | Khi fail |
|---|---|---|
| G0 Baseline | Source SHA, env map, volume isolation, checkpoint | STOP mutation, BLOCKED |
| G1 Security | No secret leak, cross-user data, admin exposure via tunnel | P0; test auth; minimal fix |
| G2 Cost | Free Tier billing verified or explicitly blocked; no paid calls | Không gọi live paid; BLOCKED |
| G3 Functional | Native UI/API workflow, 5-role policy, n8n/agent results | Defect+re-test |
| G4 Resilience | No duplicate write, persisted queue, restart/readback | Defect+re-test |
| G5 User capacity | 20 separate sessions, measured load per accepted SLO | FAIL/BLOCKED nếu không đo được |
| G6 Remote Quick Tunnel | Login/HTTPS/roles/URL rotation, no unintentional public admin | Không gỡ tunnel; sửa proxy/route |
| G7 Release | Fresh regression, backup+restore, human UAT, verified handoff | Không promote/live nếu chưa duyệt |

## Trạng thái
`PASS` = gates đều đạt theo chứng cứ. `PASS_WITH_LIMITATIONS` = chỉ minor P2 limitation được chấp nhận (KHÔNG dùng cho P0). `FAIL` = lỗi có bằng chứng. `BLOCKED` = không có đủ quyền/tài nguyên/test isolation. Mỗi case `NOT_RUN` cũng phải ghi.

## Kết quả phải tạo
`docs/ai-multi-agent-upgrade/verification_runs/<timestamp>/`
```text
CLAIM_LEDGER.csv
TEST_RESULTS.csv
DEFECT_REGISTER.md
COMMAND_LOG.md
GIT_BASELINE.md
SERVICE_PORT_MATRIX.md
QUICK_TUNNEL_ACCESS_AUDIT.md
SECURITY_EXPOSURE_REPORT.md
QUOTA_BILLING_CHECK.md
PERFORMANCE_20_USERS.md
SKILL_INVENTORY.md
SKILL_INSTALL_LOG.md
SOURCE_DIFF_SUMMARY.md
BACKUP_RESTORE_REPORT.md
EVIDENCE_INDEX.md
FINAL_INDEPENDENT_AUDIT.md
```
Không tạo file trống ghi PASS; mỗi file ghi test/scope/limitations có thật. Dùng đường dẫn tương đối, không lộ tunnel hostname hay secret trong Git artifacts.

## Report mẫu
```
Assessment: FAIL | PASS | PASS_WITH_LIMITATIONS | BLOCKED
Project: QLDAPM
Baseline branch/HEAD:
Verified code version and image digests:
Timestamp/timezone:
Scope: local + Quick Tunnel remote, 20 users, free-only
Original claims: N
Verified: N | Rejected: N | Unverified: N
Test cases PASS / FAIL / BLOCKED / NOT_RUN:
P0 open defects:
P1 open defects:
Provider billing/tier verified: YES | NO | OWNER_ACTION_NEEDED
Quick Tunnel remote auth verified: YES | NO | BLOCKED
20 individual sessions verified: YES | NO | BLOCKED
No data loss native readback: YES | NO | BLOCKED
Backup restore: YES | NO | BLOCKED
Known limits:
Files changed / commit / uncommitted changes:
Evidence index:
Next exact task for Codex / ChatGPT:
```

## Handoff liên agent
Sau mỗi wave và khi kết thúc, cập nhật `HANDOFF_CURRENT.md`, append `WORK_LOG.md`, `NEXT_SESSION_PROMPT.md`, `PROJECT_STATE.md`; phản ánh rõ `CR-KEEP-QUICK-TUNNEL` để AI sau KHÔNG nhầm public tunnel thành lỗi. Nếu task DONE trước đây bị chứng minh sai, ghi `REOPENED_BY_AUDIT` trong ledger, sửa `TASKS.json` chỉ qua tool hiện có và có audit trace, không rewrite lịch sử.
