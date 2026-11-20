# 10 — SƠ BỘ ĐÁNH GIÁ HAI BÁO CÁO ĐÃ GỬI

**Nguồn:** `source_reports/FINAL_REPORT_HANDOVER.md` và `source_reports/RELEASE_NOTES_LOCAL_V2.md` do Gemini tạo. Chưa được kiểm chứng bằng runtime/source đầy đủ Windows. Không kết luận dự án chưa chạy được.

| ID | Tuyên bố từ report | Đánh giá lúc này | Cần xác minh trực tiếp |
|---|---|---|---|
| R-01 | 113/113 DONE / 100% | CLAIM_UNVERIFIED | TASKS.json, evidence files, test map, native readback, test gate |
| R-02 | 37 suites / 184+ tests PASS | CLAIM_UNVERIFIED | Runner logic, test discovery, failures/skip/xfail, raw logs, executed time/source SHA |
| R-03 | 20 concurrent users | CLAIM_UNVERIFIED | 20 independent sessions and realistic traffic; separate 20 LLM calls |
| R-04 | 0 đồng / `paid_api_disabled` | CLAIM_UNVERIFIED | AI Studio/Google project tier & billing: app flags không chứng minh bên provider |
| R-05 | Quick Tunnel exposes remote URL | **OWNER REQUIREMENT — ALLOWED** | Remote HTTPS auth, role, route isolation, URL after restart, no nonconsensual exposure |
| R-06 | `unless-stopped` no-touch | CLAIM_NEEDS_LIMITATION | Manually-stopped container không tự hồi trong mọi tình huống; đo engine restart |
| R-07 | Model/Quota `gemini-3.5-flash-lite`, 15/250k/500 | CLAIM_UNVERIFIED | model.list, AI Studio actual quotas, reset timezone, provider errors 429 vs 503 |
| R-08 | RAM total 2.4–2.8 GB | ACCOUNTING_UNCLEAR | Sum 5 listed component ranges ≈1.405–1.655 GB. Difference could be WSL/OpenProject companion services; cần đo và phân tách. |
| R-09 | Restore checked SHA-256 | CLAIM_UNVERIFIED | Disposable restore, DB+attachments+SQLite WAL consistent snapshot, no main mutation |
| R-10 | Supervisor/n8n/Second Brain truly integrated | CLAIM_UNVERIFIED | Native functional tests with actor/scope, not unit mocks only |

**Ưu tiên:** P0 tunnel path authorization, live/staging distinction, billing verification, native rights/data safety; P1 test completeness/20-session performance, reliability and recovery; P2 RAM accounting/style.

**Cần sửa trong nhận định kiểm toán cũ:** Không coi Quick Tunnel là rủi ro chỉ vì nó tồn tại. Rủi ro cần đánh giá là *route nào được public, user nào truy cập, auth và data isolation có đạt hay không*. Chủ dự án đã chủ động cho phép Quick Tunnel.
