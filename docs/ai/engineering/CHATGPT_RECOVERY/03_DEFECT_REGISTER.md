# Defect register — Phase2 current

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

| ID | Priority | Current evidence/status |
|---|---|---|
| REC-001/002/003 | P0 | AUTO/owned resume/atomic claim SOURCE_FIXED+CANDIDATE_TESTED; liveworker restart pending |
| REC-004/005/006/007 | P0/P1 | GitHub failures/mapping/cache/UI honesty candidate tested; no live write |
| REC-008/009/010 | P1 | Receipt-derived workforce/factualreports/escaping candidate tested |
| REC-011 | P1 remaining | Wrong one-token negatives fixed; corpus exact/ACL/fallbackPASS, semanticVN/EN recallGAP; current0.65 retained |
| REC-012 | P0 data loss | CONFIRMED; newreplacement proposal testedNativeclone; original385 history not restored; MAIN approval pending |
| REC-013 | P0 historical | Raw verdict corruption preserved; ownerprojection detects contradiction; auditedcorrection pending |
| REC-014 | P0 serving | Redaction candidate+canary clean; MAIN stillunpatched/historycontainssecrets; purge/rotation separately approved |
| REC-015 | P0 integration | Outbox/actualGateway→n8nclone verified; MAINconfig/WF04activation pending |
| REC-016 | P1 | actor19 credentials resolve19/admin=true;DENIEDcorrect; membershipchange notauthorized;PARTIALremainshonest |
| REC-017 | P0 reported UI | Parser/stale-ID/controller contracts fixed/tested; original OwnerUI symptom not accepted; manualUATpending |
| REC-018 | P1 | Durable journal+unknown/concurrent/crashlocalhostHTTP10testsPASS; no blindunknownPOSTreplay |
| REC-019 | P1 boundary | Phase2images built/tested; MAINNOTDEPLOYED; sourceprivateversioned |
| REC-020 | P1 deployment | Demoexact0498candidate15tests/actualHTTPPASS;serving18791still404/405 |
| REC-021 | P1 foundPhase2 | ACKdripheader/body timeout repaired/cap8192; slow-servertestsPASS |
| REC-022 | P1 foundPhase2 | Resumeafterrework revisionmismatch + originaldiff overwrite repaired;7fulljournaltestsPASS |

Phase1 original severity/findings/logs preserved in currentrun/backups/03_DEFECT_REGISTER.md. Scope-specific PASS is not fullsystemacceptance; openMAIN vulnerabilities remain until approveddeployment.
