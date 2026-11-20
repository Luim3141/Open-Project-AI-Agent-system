"""Publish the bounded demo evidence without rewriting historical test receipts."""
import datetime,json
from pathlib import Path

out=Path(__file__).parent;docs=out.parent
def read(path):return json.loads(path.read_text(encoding='utf-8'))
live=read(out/'final-live-verification.json');status=read(out/'readback-final.json');dr=read(out/'dr/restore-final.json')
assert dr['status']=='LOCAL_RESTORE_VERIFIED'
wf=read(out/'n8n/business-qualified.json');history=read(out/'n8n/run391-completed-readback.json');reports=read(out/'n8n/main-report-readback.json')
backup=read(out/'dr/creation-final.json');deploy=read(out/'deployment.json');n8n=read(out/'n8n/deployment.json');rag=read(out/'rag/holdout-result.json')
assert live['engineering']['wp391']['recovery_count']==3 and status['wp391']['result']=='succeeded'
assert wf['passed']==16 and reports['daily']['ready']==4 and reports['weekly']['ready']==4
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
images=live['containers'];run='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
def current(name,body):
 path=docs/name;old=path.read_text(encoding='utf-8')
 marker='<!-- FINAL_DEMO_CURRENT -->';end='<!-- END_FINAL_DEMO_CURRENT -->'
 if marker in old:old=old.split(end,1)[1].lstrip()
 path.write_text(marker+'\n'+body.strip()+'\n'+end+'\n\n'+old,encoding='utf-8')

common=f'''# Final Demo — 03/11/2026, verified {stamp}

**PARTIAL DEMO ACCEPTANCE: runtime/n8n/provider recovery/DR verified; semantic RAG FAILED; Owner Browser UAT PENDING.** Không coi security defer là PASS hoặc RAG functional failure là được defer.

MAIN images: Gateway `{images['gateway']['image']}`, Core `{images['core']['image']}`, n8n `{images['n8n']['image']}`. Exact source/pins: `demo-final/final-live-verification.json`. OFF/active0/workerALIVE/provider gatefalse. OpenClaw READY và Demo UP từ API/CLI nguồn thực (`demo-final/readback-final.json`).

#391 cùng run `{run}` SUCCEEDED, checkpoint39, recovery3 (một continuation mới), total45generation calls (9 mới). Dev/Reviewer/QA và37pytest PASS; commit `1914f10d3bd0b2b05459914100c53549f63d0bc5`, [PR10](https://github.com/Luim3141/mini-task-manager/pull/10) OPEN, chưa merge/deploy Demo. Native391 version2, status độc lập engineering success; WP379 chưa Done. Không tạo duplicate WP/unit/run/PR. Probe riêng1generation/24tokens; tổngproviderreceipts474→484.

n8n16/16 bounded business scenarios PASS trên clone, không khẳng định mọi nhánh/approval/generation. WF07/12 MAIN collectors READY4/4, actor19 vẫn bị403; WF12 schedule branch thực thi trên clone, MAIN dùng đúng signed collector contract. WF04 MAIN retained execution3074 SUCCESS chứa exact RUN_COMPLETED event/ACK của #391; 3060 trước đó là replay failure event. Credentials4/4 decrypt vàusers/671execution trước cutover được bảo toàn; master key giữ nguyên; pruning720h/10000.

RAG locked holdout baselineHit@5=3/20,FPR0/20; rejectedcandidate13/20,FPR14/20. Không rollout/tune holdout đã xem, servingthreshold0.65. Exact childcitation/version vàfreshness read-back riêng không chứng minh semantic PASS.

DR **LOCAL_RESTORE_VERIFIED**, kit `{backup['kit']}`, ciphertext `{backup['ciphertext_sha256']}`. `demo-final/dr/restore-final.json`, hướng dẫn `demo-final/dr/README.md`. OFF_HOST_COPY_PENDING_OWNER; chưa physical-machine DR. Project5:13table fingerprints identical,341WP/344relations/968journals (`demo-final/native-after.json`).

Fresh coding task0; actual391continuation1/1; noGUI/paidservice/keyrotation/autoPRmerge/productionDBreset. Owner UAT chưa thực hiện.
'''
current('FINAL_SYSTEM_STATUS.md',common)
current('CONTINUATION_HANDOFF.md',common+'''

Không chạy lại `provider_probe.py`/`resume391_once.py` hoặc seed/replay run391. Exclusive intent files ghi lượt đã sử dụng. Không bật AUTO để chứng minh UI; mặc định auto_continuefalse. Engineering AUTO429 chỉ chờ fresh readiness/cooldown/checkpoint/source/budget/mode; không có background inference health probe. Unknown external write cần reconcile.

Phần còn lại thực chất: semantic RAG cần thiết kế ranking/answerability và bộ nhãn độc lập mới; không tune holdout cũ. Owner thao tác UAT; tự copy encrypted archive và recoverykey theo custody riêng. Security hardening/masterkey/historylegacy/fullphysicalDR được Owner defer, không yêu cầu đổi key để làm xanh demo.
''')
current('FULL_DEFECT_REGISTER.md',f'''# Final Demo defect dispositions — {stamp}

| Defect | Disposition | Evidence |
|---|---|---|
| WF04 không hiện retained history | LIVE VERIFIED; canonical-only workflow + projection ở persistence; bounded success/error retention | n8n3074 exact391completion, cloneerror/nested/retry/restart |
| WF07/WF12 PARTIAL do admin19 | LIVE VERIFIED; explicit20–23, giữ19deny, không impersonateOwner | main-report-readback.json READY4/4 each |
| OpenClaw/Demo UNKNOWN | LIVE VERIFIED measuredREADY/UP, CLI+HTTP, heartbeat độc lập | readback-final.json |
| Provider391429/dead-end | RECOVERED; perrequestlimiter/backoff andfreshprobe; same391SUCCEEDED in1continuation | provider-recovery-probe.json,45calls,PR10 |
| RAG semantic VN/EN | FAILED FUNCTIONAL ACCEPTANCE; candidate rejected, baseline retained | 13/20Hit5,14/20falsepositive holdout |
| Portable disaster recovery | LOCAL_RESTORE_VERIFIED; offhostOwnerpending | dr/restore-final.json |
| n8n master-key rotation | DEFERRED_BY_OWNER_FOR_LOCAL_DEMO; currentcredentialfunction verified4/4 | n8n/deployment.json |
| Historical secrets/enterprise hardening | PRODUCTION_HARDENING_DEFERRED; không tuyên bố đã clean mọihistory | Owner65747289 |
| Owner Browser UAT/physical laptop DR | PENDING OWNER / NOT TESTED | noGUI/no secondmachine |

Old register phía dưới là lịch sử, không ghi đè dispositions hiện tại.
''')
current('N8N_16_WORKFLOW_STATUS.md',f'''# Final Demo n8n — LIVE VERIFIED with bounded scope

16/16 bounded business scenarios trên actual n8n/Native/Service/Qdrant clone: `demo-final/n8n/BUSINESS_MATRIX.md`, `business-qualified.json`. Raw15/16 giữ nguyên, WF11 corrected documented PASSED enum thực thi webhook/replay/readback riêng; không sửa sản phẩm để làm test xanh. WF03 actualstart/status/replay qua deterministicNativecount; không giả Gemini generation.

MAIN image `{n8n['image']}`,16active, other15published unchanged,4credentialsdecrypt,users/encryptedcredentials671existingexecutions preserved. WF04 canonical lifecycle-only vớiHeaderAuth, không fulltraceprompt; xemGatewayInspector cho traces. Success/errorhistoryall,progressfalse, pruning720h/max10000, không purgeoldhistory lúccutover. Execution3074 retainedSUCCESS exact391RUN_COMPLETED event `{history['event_id']}`/GatewayACK; fresh history canopen in n8n. Newexecution correlation không thay đổi firstexecutionmetadata trên duplicate.

WF07 daily MAINwebhook→signedmachinecollector4/4READY; WF12 MAINsignedcollector4/4READY, scheduledbranch exercisedactualclone; actor19 still403. Reports sourcecount/citations/fingerprint andduplicate receiptsreadback `main-report-readback.json`. ScopeexistingreportingProject5 Native READ-ONLY, clonewritesProject6 only. Schedule definition preserved; wall-clockcronfuturefiring not claimed.

WF04error/nested/transportretry/restart coveredactualserverclone +6vendorstorage paths. Mỗiworkflow một kịch bản hợp lệ, sharedcontract/auth/failure/idempotency tests; không branch-complete hoặc human approval acceptance.
''')
current('SECURITY_AND_CREDENTIAL_AUDIT.md',f'''# Final Demo Owner disposition — {stamp}

`MASTER_KEY_ROTATION = DEFERRED_BY_OWNER_FOR_LOCAL_DEMO`. Không đổi instance masterkey và không nhầm data-encryption-keyrotation thành masterkeyrotation. `CURRENT_CREDENTIAL_FUNCTIONALITY = VERIFIED` ở phạm vi4/4decrypt, retained4credentials/usersunchanged vàactualworkflows auth/business. Existingkey cần để restore, chỉ lưu trongprivateencryptedkit/custody.

Historical execution secrets/legacy source/enterprisehardening = PRODUCTION_HARDENING_DEFERRED, không phải PASS và chưa được clean triệt để. WF04 mới chỉ minimalcanonicalevent/ACK, persistenceprojection chặnnestedarbitrarypayload; giữgenericredactor vàauthredaction. Cloneactualsuccess/error/retry/restart/nested +6storagepaths; không khẳng địnhmọiworkflowsecret đã loại bỏ.

Providerprivateendpoint córoot-sharedtoken+claimbinding; noBrowserAuthorization/Origin/query; cap/lease/mode enforced; settlementafterOFF chỉghiusageknownreservation, không phátrequest. No model fallback, key/quota bypass hoặc paid service. Private portablearchive vàrecoverykey hai thưmụctách trêncùngmáy chưa phảioffhostcustody. Owner cầncopyriêng tư; physicalDR chưa thử.
''')
current('DEPLOYMENT_AND_ROLLBACK.md',f'''# Final Demo deployed / rollback

{common.split('MAIN images:',1)[1].split('#391',1)[0]}

Gateway/Core backup `{deploy['backup']}`; parentprivatefolder giữconfig/imagepins/worker.before/provider_gate.before. n8n backup `{n8n['backup']}`, previouscontainer `{n8n['previous_container']}` stoppedretained; coldvolume archive cócredentials/history/key. No automaticDBrestore.

Rollback khiOFF/idle: stopQLDAPMEngineeringDelivery; restoreprivateconfig/pins/sourceworker+rootWSLprovider_gate.py và restartproviderunit; recreateGateway/Core bằngoldb184/e847; health/sourceverify rồistartworker. WSLrollbackfailure không được chặnimagerollback; nếu chưaverifyđủ thì giữworkerSTOPPED. Workernewdeferredreserve phảiđi cùngGatewayprivateadmission/gatecode; khôngmixprotocolversions.

n8nrollback: stopnewcontainer, preservefailedcontainer/privatebackup, restoreoldworkflowdefinition bằngsupportedCLI, renameoldcontainerback/start; không restoreDB tựđộng hoặc xóanewexecutions. CácCLI/import/publish cóbảnscripts `demo-final/n8n/deploy_history.py`, noautoapplywhenreadingdocs. Exactcomposeparity preserved. Backuprestoreonlyisolatedclone; noMainDBreset.

RAGcandidatekhôngdeploy. Demoapplication18791khôngđổi release; PR10OPENkhôngphảiDEPLOYED. OpenClawruntimeđượcfence(stop) sau mỗi delivery; idleGateway đãstart/readinessverified riêng, providertransportvẫnOFF. DOWN trong lúcfencingphảihiển thịthực, khôngsuy ra providerAVAILABLE.
''')
current('OWNER_MANUAL_UAT_GUIDE.md',f'''# Owner manual UAT — PENDING, Final Demo03/11/2026

Không Browserautomation đã chạy. API/Rails/NodeVM/CSScontracts không pixelvalidation. Owner tựthử:

1. Backlog/Mission/Workforce: #391 theo title/shortID/date, engineeringCOMPLETED sauDev/Review/QA; Native status riêng, không épDone. Lastactivity vàPR10đúng; OFFkhônghiển thịAgentRUNNING.
2. Inspector: same run `{run}`,45cumulativecalls,checkpoint39COMPLETE, freshsessionDev/Review/QA receipts; khôngResume taskđãhoàn tất. Mộtcontinuationchođợtnàyđãdùng1/1.
3. n8nExecutions: mởWF04execution3074, thấyminimal RUN_COMPLETED/event/run391 vàSUCCESS; cótimestamps/correlation. Old3060failureeventreplaylàlịchsửkhác.
4. Daily/Weekly: report4validreaders20–23 READY; source/citations/provenance. Actor19khôngđượcđổiOwnerhoặcbỏguard.
5. Integrations: OpenClawHTTP/CLI READY, Demo18791UP; Worker/providerriêng,providerprobeexpiredphảihiển thịREADINESS_STALE khiđúng. n8ncorrelation,indexscanage,DRbackupstatuscónguồnthời gian.
6. Reports: fullMarkdown headings/lists/table/TOC/rawcopy vàsource/narrativeverification; zoom200%/narrowviewport/keyboardscroll.
7. Notifications: đọccompletion391/oldblockedhistory,clickđúngrun,markreadpersist/reload,dedup. KhôngtựdismissOwnernotesbằngscript.
8. Control/GitHubSync: nếuOwnerbậtAUTO thìđọcqueue/backlogtrước; queueemptyAUTO_IDLE,OFFconfirmation. Auto_continuefalsemặcđịnh; khôngbậtđểtestkhiunreviewedworkeligible. Syncmộtlần,kiểmkhôngduplicate.
9. SecondBrain: exactWP391/citationversion2córeadback; semanticVN/EN**chưađạt**. KhôngcoiqueryđúngmãWP làsemanticacceptance.
10. Copykitciphertextvàbootstrap từ `{backup['kit']}` sangổngoài/custodyriêng; giữrecoverykeybí mật theoDRREADME. OFF_HOST_COPY_PENDING_OWNER, chưatestmáykhác.
''')

matrix='''# Demo completion matrix — Final03/11/2026

Overall PARTIAL: semantic RAG vẫn FAILED vàOwnerUATPENDING. Securitydeferkhôngchặncácchứcnăngđãverify.

| Component | Expected | Tested | Runtime Evidence | Status | Remaining |
|---|---|---|---|---|---|
|OpenProject|Task/data preservation|Native391v2;13Project5tablesidentical|native-after.json;readback-final.json|LIVE VERIFIED|OwnerUAT|
|AI Gateway|Orchestration/fencing|161immutabletests;source/pins|final-live-verification.json|LIVE VERIFIED|No allbranches claim|
|OpenClaw|Codingrunner/readiness|Real391Dev/Review/QA;HTTP+CLI|readback-final.json;runartifacts|LIVE VERIFIED|Idlefencingmaystopprocess truthfully|
|Gemini|Limits/recovery|Sharedledger10RPM175KTPM;actualprobe+9calls|providerprobe;391receipts|LIVE VERIFIED|Upstreamcapacitycannotguarantee|
|Multi-Agent|PM/BA/Dev/Reviewer/QA|Historicalplanning +same391delivery|checkpoint39;37pytest|LIVE VERIFIED|Not freshworkintakeE2E|
|GitHub|Commit/Push/PR/Sync|PR10headmatches;sourceAPI|readback-final.json;PR10|LIVE VERIFIED|PR10OPEN;noautomerge/deploy|
|WF01–WF16|Actualbusinesscontracts|16boundedscenariosactualclone|n8n/BUSINESS_MATRIX.md|TESTED IN CLONE|Branch-complete/humanapprovalnotclaimed|
|WF07/WF12|Validreportprincipals|MAINdaily/weekly4/4READY,19DENIED|n8n/main-report-readback.json|LIVE VERIFIED|Futurecronwallclocknotclaimed|
|WF04history|Retainedcanonicalevents|MAIN3074exactRUN_COMPLETED|n8n/run391-completed-readback.json|LIVE VERIFIED|Genericlegacysecretsdeferred|
|SecondBrainsemantic|VN/ENHit5>=80%,FPR<=5%|Candidate65%/70%;baseline15%/0%|rag/holdout-result.json|FAILED|Newranking/design+independentlabels|
|Knowledgefreshness/citation|Exactsource/version|391v2;actualcloneupdate/tombstone/integrity|391knowledge;n8nWF01/02/15|LIVE VERIFIED bounded|Not semanticPASS|
|Reports|Correctgeneration/reader|Native4reports;RailsMarkdown/NodeVM|n8nreports;checks|LIVE VERIFIED|OwnerlayoutUAT|
|Notifications|Scopedcompleted/blocked|161tests+actualnotesdedup|readback-final.json|LIVE VERIFIED|Ownerdismiss/clickUAT|
|DR|Portablelocalrestore|PG/Core/n8n/Gateway/Knowledge/Qdrant/OpenClaw/Git/demo|dr/restore-final.json|LIVE VERIFIED LOCAL_RESTORE|OFF_HOST_COPY_PENDING_OWNER;physicalNOTTESTED|
|OwnerUI|ManualUAT|NoGUIautomation|OWNER_MANUAL_UAT_GUIDE.md|OWNER UAT PENDING|Owneractions|
|Masterkeyrotation|Keepworkingcredentials|4/4decryptactualbusiness|n8ndeployment|DEFERRED BY OWNER|NotPASS,notfunctionalblock|
|Historysecurity/enterprise/physicalDR|Productionhardening|Ownerexplicitdisposition|SECURITY_AND_CREDENTIAL_AUDIT.md|DEFERRED BY OWNER|Legacyrisksremain|

Actual391continuation1/1; freshcodingtask0/1; noGUI/P5Nativewrites/paid/keyrotation/autoPRmerge/reset.
'''
(docs/'DEMO_COMPLETION_MATRIX.md').write_text(matrix,encoding='utf-8')
prior=docs/'FINAL_TEST_RESULTS.json';archive=out/'previous-final-test-results-schema5.json'
if not archive.exists():archive.write_bytes(prior.read_bytes())
record={'schema_version':6,'snapshot_utc':stamp,'overall_status':'PARTIAL_DEMO_ACCEPTANCE_SEMANTIC_RAG_FAILED_OWNER_UAT_PENDING',
 'current_images':{k:v['image'] for k,v in images.items()},'serving_source':'demo-final/final-live-verification.json',
 'checks':{'immutable_gateway':read(out/'gateway-candidate-final.json'),'core_clone':read(out/'core-clone-result.json'),
  'independent_review':read(out/'independent-release-review.json'),'n8n_16_business':{'passed':16,'scope':'one bounded scenario each; clone','evidence':'demo-final/n8n/business-qualified.json'},
  'main_reports':'demo-final/n8n/main-report-readback.json','main_history':'demo-final/n8n/run391-completed-readback.json',
  'wp391':{'status':'succeeded','same_run_id':run,'new_continuations':1,'new_generation_calls':9,'cumulative_generation_calls':45,'pytest_passed':37,'head_sha':'1914f10d3bd0b2b05459914100c53549f63d0bc5','pr':10,'merged':False},
  'node_vm':[str(p.relative_to(docs)).replace('\\','/') for p in (out/'checks').glob('node*.json')],
  'project5':read(out/'native-after.json'),'rag_holdout':rag['metrics'],'rag_disposition':'REJECTED_NOT_DEPLOYED',
  'dr_restore':'demo-final/dr/restore-final.json','dr_creation':'demo-final/dr/creation-final.json'},
 'scope_limits':['No browser/pixel UAT','No physical-machine restore/off-host copy','No overlapping test counts summed','WF03 bounded Native deterministic generation, not blanketGemini workflow test','WF05/06 clonepreview/reject, notOwnerapproval','FinalRAG agentlabelsnotindependenthumanadjudicated'],
 'deferred_by_owner':['MASTER_KEY_ROTATION','HISTORICAL_SECRET_CLEANUP','ENTERPRISE_HARDENING','FULL_PHYSICAL_DR'],
 'historical_index':'demo-final/previous-final-test-results-schema5.json'}
prior.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
current('PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md',common+'\nPhase3.1UIretained; onlyIntegrationscards/healthprojectionupdated, nofullUIrewrite.\n')
for name in ['README.md','CHECKPOINT.md']:
 path=Path(__file__).resolve().parents[5]/'openproject/ai'/name
 old=path.read_text(encoding='utf-8');path.write_text('<!-- FINAL_DEMO_CURRENT -->\n# Final Demo03/11/2026\n\nAuthority: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_SYSTEM_STATUS.md`, `DEMO_COMPLETION_MATRIX.md`, `demo-final/final-live-verification.json`. Gateway3c065590/Core5936d90e/n8n05376355 deployed; OFF/active0/workerALIVE. #391SUCCEEDED/PR10OPEN/checkpoint39, oneauthorizedcontinuationused. 16boundedbusinessscenariosPASS, WF04history/WF07/12verified. LOCAL_RESTORE_VERIFIED/offhostOwnerpending. SemanticRAGFAILED/candidaterejected; OwnerUATPENDING. Oldblocksbelowarehistory; do notresume391/rotatekeys/reseed.\n<!-- END_FINAL_DEMO_CURRENT -->\n\n'+old,encoding='utf-8')
print(json.dumps({'status':'FINAL_REPORTS_UPDATED','utc':stamp,'overall':record['overall_status']}))
