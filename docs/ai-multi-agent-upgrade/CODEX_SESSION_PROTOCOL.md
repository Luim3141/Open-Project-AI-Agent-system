# Codex Session Protocol — evidence-first, no fake completion

`TASKS.json` là trạng thái máy đọc được, `IMPLEMENTATION_PLAN.md` checkbox mirror, `PROGRESS_DASHBOARD.md` auto-generated, `PROJECT_STATE.md` chú giải + next tasks. Đừng viết DONE trong chat mà chưa có log/test/evidence.

**Statuses:** TODO → IN_PROGRESS → REVIEW → DONE; BLOCKED nếu dependency/quota/privacy; SKIPPED chỉ khi optional hoặc approved waiver (scope hiện tại P00-P10 đều required).

```powershell
python .\scripts\progress.py validate
python .\scripts\progress.py report
python .\scripts\progress.py show --phase P01
python .\scripts\progress.py set P01-04 IN_PROGRESS --note "Implement restart policies"
python .\scripts\progress.py set P01-04 REVIEW --note "Waiting Docker restart test"
python .\scripts\progress.py set P01-04 DONE --evidence "artifacts/P01-04-restart-test.md" --tests PASS --note "Engine restart test repeated and logged"
```

DONE phải có file evidence thực không rỗng, `tests=PASS` hoặc NOT_APPLICABLE có giải trình, dependencies DONE, earlier phase gates đủ. Fail/skip rõ ràng; không tự bịa chứng cứ. Đã có work đã triển khai với plan trước → merge bằng ID, không xóa history, không đảo DONE thành TODO vô lý. Không sửa source dirty không có snapshot.

## Report after each session

- Workspace/branch/commit/dirty status, phase+IDs, files modified.
- Evidence relative paths + actual commands/results + native readback; no secrets.
- Docker manual start criterion (not Windows boot autostart), Gemini persisted-key FREE verified state; n8n CE, LAN security/5-role matrix.
- Model/project usage, 429/503/credit/billing disabled evidence.
- Risks/rollback; blockers requiring owner decisions; next three eligible tasks.

If context exhausts, update state files and write resume ID, do not promise background actions. User manually starts next coding session from the plan.
