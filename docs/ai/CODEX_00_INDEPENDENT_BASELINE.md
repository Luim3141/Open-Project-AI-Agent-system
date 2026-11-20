<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — Independent baseline, 23/10/2026

**Status: PARTIAL. Main production release: NO-GO.** Chỉ đọc Main; không triển khai hoặc thử nghiệm trên Staging.

Workspace `D:\AI project\QLDAPM chat`, branch `codex/local-multi-agent-upgrade`, HEAD `de7fe8f`. Phần lớn source đang untracked; không commit, reset, clean hoặc ghi đè các thay đổi cũ. Đã đọc các báo cáo Gemini Phase 0–10 và các báo cáo audit/recovery được yêu cầu; kết luận dưới đây dựa trên source/runtime mới.

## Baseline và rollback

Snapshot riêng: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/codex-takeover-20261023-035922/` (chỉ LUIM và SYSTEM). Có `source-before.zip` gồm 595 file, manifest hash, Git status, workflow JSON live, container identity và backup SQLite nhất quán. Archive SHA256 `1a5b84dc81bb6e66ff3b09a272c7d8b5653be7eee9887a462f671cdc9edfa64b`.

Main Gateway image trước sửa `bcd7158e4feb…`; Main web `a3214219127e…`; worker/cron `95da6c8eed2e…`. Chênh image web/worker cần qualification riêng. Compose labels xác nhận Gateway dùng `openproject/ai/compose.yml` + `gemini-free.main.yml`; OpenProject dùng `openproject/compose.yml` + private `ui-bridge.yml`. n8n/Qdrant không có Compose labels; không suy đoán file cấu hình cho hai container này.

## Component inventory

| Component | Code path | Runtime / test evidence | Defect / risk | Next action |
|---|---|---|---|---|
| Router / service | `openproject/ai/gateway/{app,service}.py` | 8090 health OK; fixture REST/MCP tests | P0 auto-execute bypass trên image live | Triển khai candidate sau phê duyệt |
| Native API | `gateway/native.py`, `service.py` | Native actor 19/PM, project5, 332 WP | Write E2E chưa được duyệt | Giữ read-only; chọn test resource riêng |
| Auth / RBAC | `gateway/{permissions,bridge,store}.py` | BA direct trace403; qua n8n200/10 events PM | P0 shared PM credential | Revoke credential lộ; chuyển caller binding |
| Approval | `gateway/{store,service}.py` | Hai regression RED trước sửa; security suite PASS sau sửa | Live vẫn có bypass và thiếu payload rehash | Deploy P0 |
| Supervisor / agents | `gateway/{supervisor,planner,live_agents,*_agent}.py` | Run Gemini đã lưu, 1 QA generation + Reviewer local | FE/BE gộp `dev`; chưa đủ sáu vai trò E2E | Nghiệm thu theo role sau P0 |
| Gemini SDK | `gateway/gemini.py` | Runtime google-genai **2.30.1**, receipts có usage | Báo cáo cũ ghi SDK1.53.0; quota không phải live billing | Giữ provider/key/quota hiện có |
| Execution store | `gateway/{store,execution_events,business_runs}.py` | 55 queue rows finished; backup quick_check OK | Receipt tồn tại không tự chứng minh toàn chuỗi | Kiểm tra theo correlation/run |
| Ingestion | `gateway/knowledge_ingestion.py` | 360 docs/1713 chunks; source vector chưa deploy | Gateway ingest không truyền VectorClient | Sửa wiring/retry sau P0 |
| Retrieval | `gateway/{knowledge_search,knowledge_retrieval}.py` | Gateway thật trả FTS_KEYWORD; Hit@5 mẫu1/3 | Chưa có hybrid trong image live | Wire dense + ACL + fresh readback |
| Ollama | `gateway/vector_client.py`, `Start-OllamaDaemon.ps1` | BGE-M3 1024 chiều; Docker→host200; 100%GPU | Concurrency/reboot chưa nghiệm thu đầy đủ | Task health đã tạo; xem operations |
| Qdrant | `gateway/vector_client.py` | v1.20.0, 1693 points, persistent mount | 23 missing points, 3 unmatched | Không xóa; reconcile theo identity |
| SQLite FTS5 | `gateway/knowledge_storage.py` | quick_check OK; lexical API thật | 4 stale doc versions | Incremental sync có kiểm chứng |
| n8n generation | `automation/{generate_n8n_main_workflows,deploy_real_n8n_workflows}.py` | 16/16 live nodes khác bundle repo | Nhiều entrypoint cũ/stub | Chỉ harden từ snapshot live |
| n8n production | Container `qldapm-n8n-main` | 16 active, lịch sử success/error; zero retry nodes | P0 shared PM; P1 nghiệp vụ thiếu | Xem CODEX_02 |
| UI Control Center | `core/overlay/app/{controllers,views}/qldapm_ai*` | Source/route inspected; chưa fresh browser UAT | UI vẫn có checkbox bypass ở runtime cũ | Source đã bỏ; core deployment riêng |
| Tests | `openproject/ai/tests` | 90 Windows /76 Linux offline tests PASS | 90 legacy tests chạm Main state/business/vectors | Đánh dấu BLOCKED; không tính PASS |
| Backup / recovery | `local_backup.py`, ops scripts | 3 consistent SQLite backups quick_check OK | Backup daemon cũ là **staging**, chưa chứng minh Main restore | Không chạy daemon staging; Main restore gate riêng |

## Priorities

- **P0:** credential vẫn còn hiệu lực; n8n nâng quyền caller; auto_execute bypass; payload proposal không được rehash khi claim (đã sửa source, chưa sửa live).
- **P1:** RAG runtime thiếu vector wiring/sync; thiếu vector và stale versions; WF01–16 chưa đạt nghiệp vụ; missing Weekly Summary; Gemini/Native/RAG E2E chưa đủ.
- **P2:** đồng bộ phiên bản runtime/source, resource limits/concurrency, monitoring và Main restore rehearsal.

Commands đã chạy: `git status --short`, `git branch --show-current`, `git log -5 --oneline`, `docker ps -a`, `docker compose ls`, scoped `docker inspect`, Native GET, Qdrant scroll, Ollama embed, tests nêu trong CODEX_05. Changed files và exact hashes ở `CODEX_SECURITY_DEPLOY_PREVIEW.json` sau khi candidate hoàn tất.

Rollback: chỉ khôi phục đúng file source mình sửa từ archive, không chép đè toàn workspace/state. Runtime chưa đổi image. Không phục hồi token bị lộ hoặc database cũ để rollback code.
