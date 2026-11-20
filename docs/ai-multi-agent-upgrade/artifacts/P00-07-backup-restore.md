# P00-07 — Actual isolated restore drill

Private staging backup: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/jira-sync/backups/87a81a0b-47d7-451c-8a13-13fc819fff88`. Existing `jira_sync_backup.py backup --target staging` used scoped writer stop/start, pg_dump snapshot, assets archive, private config manifest; no main stop/recreate/migrate/restore.

Executed `jira_sync_backup.py rehearse --data-only --backup <above>`. PASS: 220 public tables + sequences fingerprint record (221 total), assets SHA256 lists and private config file hashes reproduced exactly in an isolated internal Docker network/database/new volume. Pinned original images, no public ports, no credentials/live volumes/Docker socket in clone. Disposable resources removed by existing ownership-label guards; original volumes/backups remain.

Receipt `P00-07-restore-result.json`: `passed=true`, `database_assets_config=true`, **configuration_transaction=false**, purpose=data-restore-only, import_exercise=null; backup manifest hash `e2c4a46a338976fdf3689fb288eb42baf50b711492f85d8397a72fb299b7cd91`. **Not import/release qualification or permission to promote.**

Original full helper failed twice on its unrelated Jira configuration test: `PM_ROLE_NOT_PROJECT_SCOPED` (the existing Administrator's PM role covers three projects). DB/assets/config comparisons had already passed. Preserved failed drill records privately. Added explicit data-only mode to the existing helper, leaving default qualification path and Jira `backup_proof` requirements intact. Regression29 PASS includes rejection of data-only receipt for import and rejection of mixing data-only with candidate-image/import exercise. Do not claim old Jira fixture PASS.

Gateway: stopped-state private stage-ai snapshot byte-verified before disabling provider; key/config/credentials/SQLite kept unchanged except enabled flag. Restored SQLite via Linux sqlite3 backup API into disposable tmpfs with network=none; quick_check=ok and complete logical dump fingerprint identical (`P00-07-sqlite-restore.json`). No Windows access to live SQLite and no WAL deletion.

Rollback: retain current DB/key/ledger/receipts. Any production restore/promotion needs separate reviewed operation. Source helper rollback is just removal of this mode/tests using private source-before snapshot after comparing later edits. Never restore an old gateway database or reopen historical paid authorization automatically.
