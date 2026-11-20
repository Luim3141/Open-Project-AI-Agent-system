# P03-03 — additive SQLite persistence accepted16Oct2026

Staging Gateway `sha256:2e117f87624e9a8202c71eeda589751fe2ea4d5b509f1084778e419f02d00cb7` contains strict agent contracts and two new metadata tables, `agent_tasks` / `agent_runs`, in existing Gateway SQLite. No extra DB/queue/service/dependency. Create/read operations bind actor/project, preserve exact idempotent IDs, reject conflicting/expired/orphan/non-queued initial runs and revalidate serialized models. No task execution/public API is activated by this migration; the existing ai_queue remains the execution queue.

Executed:

-10targeted model/store tests PASS Windows0.685s. Initial fixture cleanup error WinError32 was fixed by explicitly closing the fixture SQLite connection; no product workaround.
-219full Windows regression tests PASS134.271s, exit0+finalOK checked before deployment. `P03-store-regression.log`, `P03-store-test-exit.json`.
-53Linux candidate tests PASS9.026s, network none/readonly root/non-root; `P03-store-linux.log`.
-Private cold copy of actual staging: migration keeps every legacy row and original schema definition; typed task/QUEUED run survive reopen; cross-actor/project denied; separate rollback copy equals original before snapshot.471usage and79done/11failed AI receipts preserved. No provider/native calls. `P03-migration-clone.json`, executable test `tests/container_agent_migration.py`.
-Previous immutablebccd1d2c Gateway successfully opens the migrated clone and preserves new metadata plus legacy receipts/usage. `P03-old-image-compatibility.json`. Image rollback needs no table deletion. Full data rollback was tested only on separate cold copy.
-Actual staging source parity8files, new tables empty, SQLite quick_checkOK,5real native roles/335counts/PM-only ceiling, cachedREADY/471usage; config/credentials/Gemini/UI keys byte-identical to private pre-provision backup. `P03-store-live-check.json`.
-19selected runtime containers preserved;7active stagehealthy/retiredRadminstopped/all4HTTP200. Only allowed changes: Gateway image and two empty metadata tables. Native schema/counts/roles and legacy Gateway states/ledger unchanged. `P03-store-after.json`, `P03-store-preservation-check.json`.

Build reused verified localbccd base tag; first attempt using bare image ID as Dockerfile FROM failed metadata resolution and performed no deployment, then local exact-image alias build succeeded without dependency install. `P03-store-build-final.log`. Previousbccd image retained; private source snapshot operator/p03-before-20261016 and cold Gateway pre-provision backup `local-runtime/before-provision-1792139124157547100` retained. No drop/reset/destructive migration, main promotion, Desktop/CSDLDPT operation, billing change or real Google call.

Next: P03-04 context references, P03-05 state transitions, P03-06 reuse fair executor, P03-07 trace and P03-08 actor-scoped APIs. Contracts/persistence are implemented; Supervisor/n8n schedules/knowledge and five physical clients remain unfinished.
