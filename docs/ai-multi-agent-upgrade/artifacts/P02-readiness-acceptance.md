# P02-12 acceptance — 16/10/2026

Owner resumed upgrade after Docker work. Cached key/proof/model-bound readiness was implemented and smoke-tested before pause (P02-live-free-smoke.json, P02-ready-recovery-check.json). Liveness/status never call Google; no extra provider calls in this acceptance.

Resolved finalization defect: readonly live WAL SQLite may lack SHM. Backup now copies DB plus optional WAL into private temporary storage, validates exact source/copied fingerprints, opens only the private copy, and runs SQLite backup API into DELETE-journal destination. Concurrent source changes reject the backup. Source never gets write access or immutable=1.

- P02-backup-readonly-red.log reproduces defects before fix; P02-backup-windows-tests.log and P02-backup-linux-tests.log: 7/7 PASS each, committed WAL retained/uncommitted excluded/source unchanged/concurrent change rejected.
- P02-backup-full-regression.log: 174/174 PASS, 68.364s, no skips.
- P02-readiness-private-backup.json: real staging backup d03c34e3-25c1-4a52-b4b9-15fd0721e016 PASS, 221 tables.
- P02-readiness-native-restore.json: isolated data/assets/config restore PASS, 221 tables, cleanup scoped temporary resources only; no live restore.
- P02-readiness-sqlite-restore.json: gateway/n8n logical hashes equal after isolated private tmpfs restore, no live WAL opened.
- P02-readiness-backup-pairing.json: owner consent/proof/readiness/config/key archives exactly paired, no secret output.
- Restarted only local-backup sidecar to reload fixed watch code; healthy. P02-backup-recovery-check.json: 19 selected containers same images/mounts/ports; native schemas/roles/counts/gateway ledger and private config unchanged; all seven selected stage services healthy. HTTP main8088/8090 and stage18091/18092 all200.

No Desktop restart, CSDLDPT changes, main promotion or key reenrollment. Readiness is cached evidence, not live billing verification; no physical five-client/sleep acceptance claimed. P02-05 fair queue remains unfinished.
