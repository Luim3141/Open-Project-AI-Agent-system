# P01-11 Quick Tunnel / P01-08 recovery acceptance

Observed15–16/10/2026 Asia/Bangkok. Owner explicitly replaced Radmin with Quick Tunnel and removed the other-Radmin-device prerequisite. TASKS preserves the original acceptance and exact instruction under owner_scope_changes. No five remote browser sessions are claimed; that remains P09 end-to-end testing.

Implemented pinned cloudflared2026.10.0, native web hostname supervisor and localhost18090 current-link page. Only staging native8080 is forwarded. Gateway18092/n8n5678/link page18090 bind loopback; DB/metrics have no host ports. Before exposure, actual native login_required=true/self_registration=0/all3projects private asserted. Retired Radmin proxy stopped, container/CA/data retained. Existing native core image and role configuration unchanged.

Executed evidence:

- QUICK-compose-tests-final.log:10targeted unit/Compose boundary tests PASS. QUICK-ruby-tests-fixed.log: strict hostname/parser/child graceful termination PASS in network-none pinned core container. Recovery checker self-test: running service failure and retired-service restart both rejected.
- QUICK-public-https.json and QUICK-public-after-rotation.json: actual public system-CA TLS, native login CSRF/Secure cookie, anonymous project redirect/login and native work-package API401 PASS.
- QUICK-url-rotation.json: actual connector restart changes public hostname, native child reloads without container recreation/manual Compose/key entry; public HTTPS recheck PASS.
- QUICK-suspend-resume.json: actual35seconds docker pause/unpause of7fixed stage containers, same IDs, all healthy, ledger/jobs/runs/proposals unchanged. No power settings changed. This is process suspension, **not a physical Windows sleep test**.
- QUICK-desktop-restart.log: actual docker desktop restart --detach. QUICK-desktop-recovered.json shows7services healthy automatically. No Compose/up/Repair/container-start command or key entry after Desktop starts. QUICK-before/after-desktop-restart.json and QUICK-desktop-check.json:19containers retained, same images/mounts/ports, schema/memberships/counts/ledger/provider state equal, intentionally stopped Radmin remains stopped. Earlier P01-10-three-cycles.md supplies the3prior engine-cycle tests.
- QUICK-public-after-desktop.json: public TLS/auth checks PASS after whole Desktop restart/new hostname. QUICK-persisted-keys.json verifies private key/config exact bytes; no Google call.

P01-08 written acceptance is Desktop rerun restores services, scheduled jobs do not flood, no power settings changed. These are covered by actual engine cycles, bounded process suspension, unchanged ledger, and P01-09-scheduler-tests.log missed-day clock tests. It closes against those explicit criteria; physical Windows sleep/wake remains untested and is carried to P09 as a residual test. No Windows startup/wake automation created.

Main remains unchanged/unreachable on8088/8090 due existing Windows exclusions; no promotion/migration/data deletion. Public native login is intentional owner-approved exposure. Quick Tunnel hostname is temporary and availability depends on Cloudflare/network; current entry http://localhost:18090. Gemini remains OFF, existing key retained, no inference/cost/billing change. Rollback uses saved private manifest/source and retained Radmin resources, not stale DB/ledger restoration.
