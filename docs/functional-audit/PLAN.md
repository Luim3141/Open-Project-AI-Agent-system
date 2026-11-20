# QLDAPM Functional Audit — kế hoạch thực thi

**Goal:** Kiểm kê và nghiệm thu chức năng theo hành vi, sửa P0/P1 có repro, không tối ưu p95.
**Architecture:** Giữ hệ thống hiện hành, một agent, CLI/headless; MAIN read-only và controlled restarts. Mutation chỉ isolated, không create/run/approve/merge trên MAIN.
**Spec:** Attachment f8127b88-44d2-491f-835e-7c1fe0592483/Pasted text.txt.
**Tech Stack:** Rails/Python/aiogram/Gemini/n8n/OpenProject/React/SQLite/PostgreSQL/GitHub.

## Ràng buộc
- Model gemini-3.5-flash-lite/key/caps giữ nguyên, zero budget.
- #398 chờ Owner; PR15OPEN; catalog14; SupervisorOFF/idle.
- Không newTask/Subtask/Supervisor, không xóa/reset DB/history/volumes, không merge/deploy PR.
- Không gửi notification mới khi chưa có quyền cụ thể. Owner tự gửi4live read turns; không giả inbound Telegram.
- Phân loại fixture/isolated/Main read/historical/live mới trong từng evidence.

## Thực hiện tuần tự
- [x] 1. Pin source/images/config/data fingerprints; AST inventory routes/commands/tools/UI và live n8n workflows.
- [x] 2. Core integration reads/ACL/state/PR15 + actual #398 history/acceptance; targeted contracts cho mutation trong isolated environment.
- [x] 3. Telegram connectivity/metadata/authorization/outbox/context, actual Owner conversation khi có input; bounded Gemini/Gateway tests trong budget còn lại.
- [x] 4. CommandCenter/Mission/Workforce/Reports/Studio browser functional UAT, không performance campaign.
- [x] 5. n8n workflow contracts/history; RAG known-document queries/citation/filter/isolation qua actual services; distinguish known semantic gate.
- [x] 6. Repro/RED→GREEN cho bug được chứng minh; cập nhật architecture cùng code, immutable candidate và guarded release nếu cần.
- [x] 7. Controlled Telegram/Gateway restart khi OFF/idle; verify persistence/no-replay, không restart toàn stack.
- [x] 8. Targeted→broad appropriate regression; after integrity; functional matrix/E2E/results/remaining issues, commit exact whitelist.

## Review focus
Unknown dữ liệu không được coi complete; freshness/current agent khác history; mutations confirmation/idempotency; project/RBAC; notification false completion; tool-result truncation/citations. Rollback dùng exact current images, giữ volumes/config/new records/catalog14, không oldDB restore. Báo cáo FULL PASS chỉ khi evidence đầy đủ, các forbidden live mutations ghi BLOCKED BY AUTHORIZATION.

Các bước audit đã thực hiện; dấu hoàn tất ở đây là hoàn tất bước điều tra/báo cáo, không phải FUNCTIONAL FULL PASS. Các nhánh chưa được phép hoặc chưa đủ bằng chứng giữ PARTIAL/BLOCKED/NOT TESTED trong matrix.
