# Data integrity — MAIN before/after

21/21 assertions TRUE, fresh fingerprints và full critical SQLite table hashes: [integrity-final.json](integrity-final.json). Snapshot ban đầu: [baseline.json](baseline.json). Không restore database.

- Native project5 + existing project6 WorkPackages/roles/workflows/users/password fingerprints giữ nguyên. Task398id/subject/version10/description/dates/customfields khớp initial read; chưa DONE.
- Gateway original rows/prefixes retained. Full agent_runs/agent_tasks/ai_queue/ai_runs/engineering_checkpoints/plans/unit_definitions/control/owner_commands/tokens bằng pre-Core-release readonly SQLite backup; không replay/history loss.
- Catalog14, modeOFF/active0; engineering receipt count620 giữ nguyên. Bot budget18/20, không reset. Telegram incoming updates/audit/memory/rate/budget có tăng do các lượt đã được phép; không đòi full TelegramDB hash bất biến.
- Pairing/paircodes/confirmations/notification_context/outbox giữ nguyên.7SENT, no398TASK_COMPLETED. Conversation398 và global reply tồn tại sau restart.
- .env/secrets/config hashes bằng baseline;17n8nworkflows/credentials bằng baseline, n8ncontainerID/start unchanged. Chỉ lưu hashes, không credentials.
- Core82deployed files match current host; Telegram deployed source match; Gateway unchanged image/deployed source match.7hostlegacy modules absent in both baseline andcurrentimage, không claim deployed parity cho files không tồn tại.
- Only4product source files đổi. Docker env/mount/network/restart unchanged; only qualified image replacements. Default local bot tag pinned334963; Core/Gateway exact images trong FINAL_REPORT.

Rollback: image-only to previous botbd305 / Coredb29 (original035/d0bdd retained), keep volumes/config/catalog14/current data; use guarded operator manifests and idle check. Không rollback bằng DB snapshot cũ, không delete newly recorded history. Existing product demo head01d765 remains; PR15 notmerged/deployed.
