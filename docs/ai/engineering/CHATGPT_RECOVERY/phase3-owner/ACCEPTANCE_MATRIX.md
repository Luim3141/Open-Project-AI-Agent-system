# Phase3 acceptance matrix

Exact commands/images/source hashes and per-feature limitations: `ACCEPTANCE_MATRIX.json`. Owner UAT remains PENDING for every row; no OWNER ACCEPTED. Clone adapter proof is not complete workflow business acceptance.

| Feature | Actual / status | Remaining scope |
|---|---|---|
| Mission Control | MAIN OFF/EMPTY/workerALIVE, persisted revision/lastcommand;10livefragments · DEPLOYED, API VERIFIED | No additional known defect in tested contract; browser acceptance pending |
| Agent Workforce | Durable bounded receipts and profile projection; no invented calls/reasoning · DEPLOYED, API VERIFIED | No additional known defect in tested contract; browser acceptance pending |
| Work Intake | Invalid swallowed mode call removed; actual controller+session request contract passed · DEPLOYED, TESTED IN CLONE | No Phase3 new planning run created |
| PM/BA Planning | Historical390 planning8751… mapped correctly on current telemetry · DEPLOYED, API VERIFIED | Current-image new provider planning not exercised |
| RUN ONCE | Backend singleton/dependency/admission fixtures; MAIN EMPTY projection and disabled NO ELIGIBLE WORK · DEPLOYED, TESTED IN CLONE | Actual active-work control effects not fault-injected on MAIN |
| AUTO | Idle/full-delivered AUTO remains enabled in fixture; stale OFF race protected · DEPLOYED, TESTED IN CLONE | Actual active-work control effects not fault-injected on MAIN |
| PAUSE | Fixture active PAUSE_REQUESTED vs PAUSED; no MAIN fault injection · DEPLOYED, TESTED IN CLONE | Actual active-work control effects not fault-injected on MAIN |
| RESUME | Existing resume/fencing regressions + durable request reservation · DEPLOYED, TESTED IN CLONE | Actual active-work control effects not fault-injected on MAIN |
| CANCEL | Fixture/control/worker cleanup regressions; current UI consumes actual state · DEPLOYED, TESTED IN CLONE | Actual active-work control effects not fault-injected on MAIN |
| OFF | MAIN signed OFF accepted; exact UUID replay; final OFF/queue0 · DEPLOYED, API VERIFIED | No additional known defect in tested contract; browser acceptance pending |
| Queue | MAIN EMPTY/ready0/active0; eligibility/concurrency reasons in fixtures · DEPLOYED, API VERIFIED | No additional known defect in tested contract; browser acceptance pending |
| Live Agent Timeline | 100events/cursor;390artifact pipeline correct, ReportsUNKNOWN · DEPLOYED, API VERIFIED | Browser delivery latency not measured;3s/15s/60s timers tested as contract |
| Run Inspector | Request token isolates late A success/error after B; text/escaped rendering · DEPLOYED, TESTED IN CLONE | No additional known defect in tested contract; browser acceptance pending |
| GitHub Sync | MAIN twiceSUCCESS changedfalse; sameUUID exact replay; UI fixtures fresh PR withoutF5 · DEPLOYED, API VERIFIED | External PR state mutation simulated in fixtures; Owner browser recheck pending |
| GitHub PR reconciliation | Native activity marker confirmation before ACK; current7/8/9OPENstacked · DEPLOYED, API VERIFIED | Unknown external POST still needs read-back, never automatic repost |
| OpenClaw Dev | Historical390commit4a794… and reviewed diff mapped; host protocol unchanged · DEPLOYED, API VERIFIED (historical artifacts) | No fresh Phase3 coding run; Phase2 E2E image boundary preserved |
| Reviewer | Internal PASS matches persisted diff revision; not GitHub review · DEPLOYED, API VERIFIED (historical artifacts) | No fresh Phase3 coding run; Phase2 E2E image boundary preserved |
| QA | Internal PASS/exit0/testloghash matches persisted artifacts · DEPLOYED, API VERIFIED (historical artifacts) | No fresh Phase3 coding run; Phase2 E2E image boundary preserved |
| n8n WF01–WF16 | 16published;14cloneadapters;WF07/12denied19/PARTIAL; historyOFF forWF04 · PARTIAL | Not16businessE2E; master-key/history unresolved |
| Second Brain Exact | MAIN10/10samplecurrent;387/389/390version2,denseREADY · DEPLOYED, API VERIFIED | Exact IDs do not certify semantic recall |
| Second Brain Semantic | Existing semantic gate failed; new pool hypothesis rejected before tuning; freshness defect repaired · PARTIAL, BLOCKED QUALITY GATE | Human labels pending; no new semantic candidate deployed |
| Reports | Actual report metrics schema, auto fragments, text reader; stored reports readback · DEPLOYED, TESTED IN CLONE, API VERIFIED (existing reports) | No new narrative/model generation requested; per-run Reports linkageUNKNOWN |
| Notifications | Live region added; dismiss posted toexistingGatewaycommand · DEPLOYED, TESTED IN CLONE | MAIN unread notification not dismissed just for test |
| Scheduling | Actual bool+time schema, allfields POST, latestmodalreadback · DEPLOYED, TESTED IN CLONE | Did not wait for production calendar timer as acceptance |
| Demo release | HTTPhealth200;PR6revision0498…;TESTRELEASE/mergedfalse · API VERIFIED | PR7/8/9notdeployed; no auto-merge |
| Data preservation | 13scoped/globaltables entire rows identical before/after bothrollouts · API VERIFIED | Not exhaustive every DBtable/DR assurance |
| Security/DR | Byte-onlycopychecker10PASS/1SKIP;6vendorfilesystemleakcanariesconfirmBLOCKED · PARTIAL, BLOCKED | Master-key/history/offhostcustody/physicalDRpending |
| n8n WF01 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF02 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF03 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF04 | Publishedadaptercloneverified;historical390ACKobserved via currentGateway · TESTED IN CLONE (ADAPTER ONLY) | No new write-heavy MAIN workflow exercise; WF04 retentionOFF |
| n8n WF05 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF06 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF07 | All5collectorPARTIAL:actor19adminDENIED · PARTIAL/FAILED BUSINESS | Do not infer active=businessPASS |
| n8n WF08 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF09 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF10 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF11 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF12 | All5collectorPARTIAL:actor19adminDENIED · PARTIAL/FAILED BUSINESS | Do not infer active=businessPASS |
| n8n WF13 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF14 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF15 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
| n8n WF16 | Publishedadapterverified in prior isolatedn8n;businesswritebranchNOT_EXERCISED · TESTED IN CLONE (ADAPTER ONLY) | Do not infer active=businessPASS |
