# AI Control Center stabilization — implementation plan

Authority: Owner attachment02f3dcd8,04/11/2026. One root works sequentially. Pause feature development and RAG experiments; Project5 read-only, no coding replay/PR change/Demo release/DR. Preserve final PAUSED and delegation OFF.

## Observed baseline

- Actual Owner browser on127.0.0.1: clicking Backlog changes URL to `/#tab-backlog`; reload renders Home. Relative History API URL resolves against OpenProject's root base tag.
- Actual Main Gateway status5samples: p50=9.8377s, sample p95/max=18.9763s, approximately634KB. One isolated profile took22.6078s, GitHub11.8131s and24Native calls. Poll abort12s can turn otherwise working runtime into STALE.
- Native387/389/390/391/394 all NEW/v2. Succeeded engineering receipts bind exact IDs/project/version/PRs. Current Native forms only permit the next valid analysis transition. Existing GitHub reconciliation publishes comments/metadata, not status progress.

## Changes and checks

Current04/11: Native386/387/389/390/391/394 READY FOR RELEASE/v10 on Main;166immutable Gateway regressions and actual Rails/Native clone PASS. Reports Daily6766chars/6sections/Raw and structured audit facts/provenance verified in actual Owner browser; Sync NO CHANGES12/0 verified without F5. Initial data-load performance remains OPEN: Gateway p50=7.2148s/max12.8446s, Core load can exceed4s. Native↔AI cross-document history bug repaired by qualified/deployedv12; actual Native→Back restored AI DOM, and JSON RUN ONCE returned explicit NO_ELIGIBLE_WORK without creating a run. Final modePAUSED/delegationOFF/21coding runs/531receipts preserved; Project5/global13scopes identical. Current evidence: final-live-verification.json/browser-uat.json;18Owner answers and demo checklist are in existing top-level reports. Do not mark Demo Ready while performance gate remains open.

- [ ] Navigation: RED real inline-handler test with root base tag; preserve canonical pathname/query/hash, use history entries and popstate, preserve selected run/tab and ARIA. Fix local anchors that resolve to Home. Prove F5/back/forward in actual authenticated Owner browser.
- [ ] Read/transport performance: profile remaining cost; remove GitHub network/details and health probes from interactive refresh, reuse existing background reconciliation and durable timestamped snapshots. Keep fresh Native permissions/source status. Reduce large repeated artifacts/hidden-panel renders, keep single-flight and stale ordering. RED tests for slow dependencies and bounded command ACK.
- [ ] Controls: separate immediate authenticated accepted/rejected receipt from long operation completion; persist UUID/outcome, polling/reconnection/unknown-write reconciliation and no-changes GitHub feedback. Existing worker remains scheduler. Test mode conflicts/no work/403/409/timeout/duplicate/RESUME/CANCEL without replaying completed runs; restore PAUSED through authenticated control.
- [ ] Native status reconciliation: discover actual Task workflow/role/forms, record explicit semantic mapping/config binding. Add durable source-event/Native-write/readback journal; own principal25, Project6 only, version/identity/eligibility guards, finite retries, no blind unknown replay or silent human override. Dry-run requested historical WPs, actual Native clone qualification, then Main read-back. Never map PR OPEN or merely merged to DONE.
- [ ] Core/UI projection: independently show Engineering/Native/GitHub delivery and sync reason, current vs historical activity, loading/error/unknown feedback, targeted current data refresh without losing tab/form/selection. RAG UI bounded transport only.
- [ ] Build exact affected images, actual Rails/Core/Gateway/Native clone checks, minimal rollback snapshot, deploy app pair, Main controls/status sync/correlation/source/Project5 verification and before/after performance. Browser rehearsal including F5/rapid tabs/slow dependency/error/links/200%zoom. Update existing reports with18Owner answers and short5–10minute demo checklist.

Roll back images/config only if necessary; never restore business DB or erase audit/history. Discovered valid transitions are not permission to falsify intermediate engineering/QA evidence or override human decisions. Unsupported/gated transitions become STATUS_SYNC_BLOCKED with exact reason.
