from support import *
assert CONTEXT['stage']=='DEPLOYMENT_VERIFIED_AND_METADATA_RECORDED'
result=json.loads((RUN/'deployment-result.json').read_text())
canary=json.loads((RUN/'n8n-negative-canary.json').read_text())
pack=json.loads((RUN/'source-packaging-security-correction.json').read_text())
reads=json.loads((RUN/'authenticated-service-read-smoke.json').read_text())
DOC=RUN.parent
table='| Service | Serving image ID |\n|---|---|\n'+''.join(f'| {kind} | `{image}` |\n' for kind,image in result['images'].items())
report=f'''# MAIN rollout 30218aff — đã áp dụng và xác minh

Trạng thái: **DEPLOYED_TO_MAIN_READ_SMOKE_VERIFIED_WITH_LIMITS**. Owner đã duyệt proposal SHA256 `{CONTEXT['approved_hash']}`. Evidence: `{RUN.name}/deployment-result.json`; thời điểm chốt `{result['at']}`. Không coi approval triển khai là Owner UAT acceptance.

{table}

Đã thay đúng Gateway/Core/n8n và restart task QLDAPMEngineeringDelivery khi idle.15 file runtime khớp candidate hashes. AI_IMAGE, Core bridge image và image-lock được pin để Compose sau này giữ đúng version. Config chỉ thêm n8n_lifecycle với signing key private; provider/model/quota/Native credentials/TOTP/UI key không đổi. Worker mới có một process tree, heartbeat mới, run_id=null; engineering OFF, queue active0, provider receipts358.

WF04 `elfapV5D2PTnLiHW` đã publish version `{result['wf04_active_version']}`,8 nodes:4 cũ giữ nguyên và4 lifecycle adapter mới.16 workflows active;15 workflow còn lại không đổi graph/settings/version. Owner, encrypted credentials và sharing được đối chiếu giữ nguyên. Container n8n cũ được giữ stopped tại `{CONTEXT['n8n_previous_name']}` để rollback, không xóa volume.

Kiểm tra dữ liệu: Project5=341WP/maxlock4, Project6=7WP/maxlock9;379status7/lock4;385absent;386status1/lock2. Full WorkPackage/relation rows, Native users/security/roles/membership/tokens/TOTP được đối chiếu với fresh backup theo các cột trong evidence.9 bảng history Gateway không thay đổi, gồm raw verdict cũ và Native request receipts. Không sửa verdict lịch sử hoặc replay unknown outcome.

Read smoke dùng Native identity/permission guards: Owner18 và PM20 đọc reports list/detail; sample IDs khớp và narrative nonempty,22reports hiện hữu. Owner RAG healthz truy xuất WP384. Actor19 vẫn DENIED đúng guard. Đây là Service read checks trên serving runtime, không phải browser/Owner UI UAT.

Live n8n negative canary execution `{canary['execution_id']}`: chữ ký sai → callback403/webhook500 đúng dự kiến; không admit AI run/outbox/observation hoặc ghi nghiệp vụ Native. Canary không xuất hiện trong execution storage/daemon log. Theo policy saveDataErrorExecution=none, bản ghi được tombstone/cleanup; cột status thô có thể còn running nhưng deletedAt khác null, không phải active execution. Test đầu đọc raw status chưa lọc tombstone đã được sửa; không sửa production status bằng SQL. Chưa thử positive ACK cho một business lifecycle event MAIN mới.

18 container ngoài phạm vi giữ nguyên ID/image. Stage quick tunnel có StartedAt thay đổi trong khoảng quan sát và RestartCount2; không có lệnh rollout nào nhắm tới container đó. Không khẳng định toàn bộ StartedAt ngoài phạm vi giữ nguyên. Gateway/Core healthy, n8n readiness200; worker idle. Demo18791 vẫn release cũ, health404/summary405; chưa deploy demo.

Fresh backup private: `{PRIVATE}` gồm PG/Gateway/knowledge/n8n/assets/config và cold n8n volume archive. Candidate đã giải mã credentials của fresh n8n backup trên clone; isolated restore/startup/rollback qualification của Phase2 vẫn được giữ. Hai khác biệt Docker default Dns=[]/null và OomKillDisable=null/false được ghi trong ledger, không thay policy.

**Source packaging correction:** phát hiện một legacy script chứa encryption key n8n hiện hữu; regex scan cũ bỏ sót literal hex. Snapshot/bundle27db được giữ private và đánh dấu sensitive, không được publish. Gói sạch mới `{pack.get('clean_commit','N/A')}` có{pack.get('clean_source_files',0)} source files, loại file credential-bearing; không đổi code đã triển khai hay rewrite shared history. Dùng clean bundle được ghi trong source-packaging-security-correction.json cho handoff/export. Key hiện hữu không được xoay trong approval này.

Còn giới hạn: semantic RAG VN/EN; actor19 admin guard; historical n8n secrets/rotation; WP385 replacement/audited correction; demo18791; fresh OpenClaw/provider/Native/GitHub business E2E; UI **PENDING OWNER MANUAL UAT**. Không Computer Use, không provider call mới do rollout, không xóa lịch sử/WP hoặc restore DB cũ lên MAIN.
'''
(DOC/'MAIN_ROLLOUT_RESULT.md').write_text(report,encoding='utf-8')
header=f'''<!-- CHATGPT_RECOVERY_MAIN_30218AFF -->
# MAIN hiện hành — approved recovery patch30218aff

**DEPLOYED_TO_MAIN_READ_SMOKE_VERIFIED_WITH_LIMITS**, `{result['at']}`. Gateway1c102481/Corec237e4a7/n8n9e8d3393;15 runtime file hashes match; WF04 thêm lifecycle adapter và retention/redaction,16 workflows active. Host worker đã restart, heartbeat ALIVE/idle, modeOFF/active0/provider receipts358. Project5=341/maxlock4 và379status7/lock4 giữ nguyên; credentials/TOTP/history được đối chiếu bảo toàn.

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/MAIN_ROLLOUT_RESULT.md` và `{RUN.relative_to(ROOT).as_posix()}/deployment-result.json`. Những image/title COMPLETE/UAT bên dưới là lịch sử. Không replay run, re-provision hoặc restore DB theo lịch sử cũ. Positive MAIN lifecycle/provider business E2E chưa chạy; UI PENDING OWNER MANUAL UAT. Demo18791/WP385/history cleanup/credential rotation không nằm trong rollout này.
<!-- END_CHATGPT_RECOVERY_MAIN_30218AFF -->

'''
for relative in ['openproject/ai/README.md','openproject/ai/CHECKPOINT.md','architecture.md']:
    path=ROOT/relative;path.write_text(header+path.read_text(encoding='utf-8'),encoding='utf-8')
notice=f'''# Trạng thái sau Owner approval — MAIN đã đổi

Proposal30218aff đã được duyệt và áp dụng. Xem [MAIN_ROLLOUT_RESULT.md](MAIN_ROLLOUT_RESULT.md) và `{RUN.name}/deployment-result.json`. Các đoạn NOT_DEPLOYED/AWAITING_OWNER_APPROVAL phía dưới là pre-rollout snapshot, không phải trạng thái hiện tại. Chưa human acceptance/full business E2E.

---

'''
for name in ['FINAL_PRE_ROLLOUT_ACCEPTANCE.md','10_DEPLOYMENT_AND_ROLLBACK.md','12_CONTINUATION_HANDOFF.md','06_N8N_16_WORKFLOW_INTEGRATION.md','N8N_EVENT_PUBLISHER_EVIDENCE.md','N8N_SECRET_RETENTION_REMEDIATION.md']:
    path=DOC/name;path.write_text(notice+path.read_text(encoding='utf-8'),encoding='utf-8')
path=DOC/'12_CONTINUATION_HANDOFF.md'
text=path.read_text(encoding='utf-8').replace('Không DB/env/credential nào nằm trong source bundle.','Correction sau rollout: bundle gốc có credential-bearing legacy script, đã đánh dấu sensitive/private; dùng clean-source bundle theo MAIN_ROLLOUT_RESULT.md.')
path.write_text(text,encoding='utf-8')
matrix_path=DOC/'09_TEST_EXECUTION_RESULTS.json';matrix=json.loads(matrix_path.read_text())
matrix.update(status=result['status'],main_rollout_approved=True,main_rollout_evidence=str(RUN/'deployment-result.json'),owner_manual_uat='PENDING OWNER MANUAL UAT')
matrix['suites'].append({'test_id':'MAIN-30218AFF-ROLLOUT','phase':'MAIN_ROLLOUT','status':'PASS_WITH_LIMITS','exit_code':0,
 'logs':str(RUN/'deployment-result.json'),'actual_result':'3 pinned images,15runtimehashes,WF04targetonly,workerALIVE/OFF/active0,Nativebusiness/security and9Gatewayhistorytablespreserved; readsmoke+negativecanaryPASS; positivebusinessE2E/UIUATnotrun'})
matrix_path.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
(DOC/'CURRENT_RUN.txt').write_text(RUN.name+'\n')
write('handoff-recorded.json',{'at':datetime.now(timezone.utc).isoformat(),'authority':str(DOC/'MAIN_ROLLOUT_RESULT.md'),'approved_hash':CONTEXT['approved_hash'],'deployment_status':result['status']})
stage('COMPLETE_APPROVED_ROLLOUT_WITH_DOCUMENTED_LIMITS')
