# Functional matrix — 12/11/2026

206 dòng: {"PASS": 52, "PARTIAL": 70, "NOT TESTED": 30, "BLOCKED BY AUTHORIZATION": 54}. Đây là danh mục coverage, không phải tỷ lệ hoàn thành sản phẩm. PASS chỉ áp dụng evidence level ghi ở dòng tương ứng; không suy PASS live mutation từ isolated tests.

Input/output: [Gateway schema](gateway-openapi.json), [29 Telegram schemas](telegram-tool-schemas.json), [n8n node/auth/error contracts](n8n-contracts.json). Chi tiết source, expected/actual, input/output, risk và evidence của từng dòng: [matrix.json](matrix.json).

MCP có97 action names mirror Command enum; chưa có session MAIN MCP mới. Các read bị token engineering giới hạn403 là expected authorization boundary, không phải quyền để bypass.

| ID | Module / chức năng | Kết quả | Mức bằng chứng | Evidence |
|---|---|---|---|---|
| F001 | Gateway route / GET/HEAD /health | PASS | MAIN READ + ISOLATED ERRORS | [main-integrations.json](main-integrations.json), [final-smoke.json](final-smoke.json), [qualification.json](qualification.json) |
| F002 | Gateway route / POST /api/v1/commands | PASS | MAIN READ + ISOLATED ERRORS | [main-integrations.json](main-integrations.json), [final-smoke.json](final-smoke.json), [qualification.json](qualification.json) |
| F003 | Gateway route / POST /api/v1/ai-runs | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F004 | Gateway route / GET/HEAD /api/v1/ai-runs/{id} | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F005 | Gateway route / GET/HEAD /api/v1/proposals/{id} | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F006 | Gateway route / POST /api/v1/proposals/{id}/decision | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F007 | Gateway route / POST /api/v1/knowledge-feedback/{id}/decision | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F008 | Gateway route / POST /api/v1/qa-evidence/{id}/decision | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F009 | Gateway route / POST /api/v1/native-phases/{id}/decision | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F010 | Gateway route / GET/HEAD /api/v1/agent-runs | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F011 | Gateway route / GET/HEAD /api/v1/agent-runs/{id} | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F012 | Gateway route / GET/HEAD /api/v1/agent-runs/{id}/trace | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F013 | Gateway route / GET/HEAD /api/v1/control-center/state | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F014 | Gateway route / GET/HEAD /api/v1/insights | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F015 | Gateway route / POST /internal/ui | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F016 | Gateway route / GET/HEAD /api/v1/openapi.json | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F017 | Gateway command / observer_task_progress | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F018 | Gateway command / observer_active | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F019 | Gateway command / observer_run_details | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F020 | Gateway command / delegated_status | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F021 | Gateway command / delegated_control | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F022 | Gateway command / delegated_preview | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F023 | Gateway command / engineering_report_schedule_get | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F024 | Gateway command / engineering_report_schedule_update | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F025 | Gateway command / engineering_notifications_list | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F026 | Gateway command / engineering_notifications_dismiss | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F027 | Gateway command / engineering_report_generate | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F028 | Gateway command / engineering_report_list | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F029 | Gateway command / engineering_report_get | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F030 | Gateway command / engineering_github_sync | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F031 | Gateway command / engineering_plan | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F032 | Gateway command / engineering_cancel | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F033 | Gateway command / engineering_resume | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F034 | Gateway command / engineering_status | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F035 | Gateway command / engineering_run_once | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F036 | Gateway command / engineering_control | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F037 | Gateway command / delete_work_package | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F038 | Gateway command / update_dependency | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F039 | Gateway command / delete_dependency | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F040 | Gateway command / create_dependency | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F041 | Gateway command / identity | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F042 | Gateway command / list_work_packages | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F043 | Gateway command / get_work_package | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F044 | Gateway command / get_project_options | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F045 | Gateway command / analyze | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F046 | Gateway command / create_work_package | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F047 | Gateway command / update_work_package | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F048 | Gateway command / comment | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F049 | Gateway command / transition | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F050 | Gateway command / get_gate | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F051 | Gateway command / change_gate | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F052 | Gateway command / list_code | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F053 | Gateway command / read_code | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F054 | Gateway command / write_code | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F055 | Gateway command / request_test | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F056 | Gateway command / propose_operation | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F057 | Gateway command / get_job | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F058 | Gateway command / request_status | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F059 | Gateway command / reconcile_request | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F060 | Gateway command / get_configuration | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F061 | Gateway command / get_proposal | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F062 | Gateway command / reject_proposal | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F063 | Gateway command / get_assistant_status | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F064 | Gateway command / get_action_history | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F065 | Gateway command / start_ai_run | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F066 | Gateway command / get_ai_run | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F067 | Gateway command / get_insights | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F068 | Gateway command / get_permissions | PARTIAL | MAIN DENIAL | [main-integrations.json](main-integrations.json) |
| F069 | Gateway command / list_agent_runs | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F070 | Gateway command / get_agent_run | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F071 | Gateway command / get_agent_trace | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F072 | Gateway command / cancel_agent_run | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F073 | Gateway command / knowledge_ingest | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F074 | Gateway command / knowledge_search | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F075 | Gateway command / knowledge_deindex | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F076 | Gateway command / knowledge_integrity | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F077 | Gateway command / weekly_summary | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F078 | Gateway command / sprint_risks | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F079 | Gateway command / get_report | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F080 | Gateway command / knowledge_sync_status | PARTIAL | MAIN DENIAL | [main-integrations.json](main-integrations.json) |
| F081 | Gateway command / knowledge_sync_retry | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F082 | Gateway command / get_control_center | PARTIAL | MAIN DENIAL | [main-integrations.json](main-integrations.json) |
| F083 | Gateway command / get_execution_monitor | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F084 | Gateway command / list_execution_monitors | PASS | MAIN READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [browser-uat.json](browser-uat.json), [additional-reads.json](additional-reads.json) |
| F085 | Gateway command / owner_inspect | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F086 | Gateway command / knowledge_file_ingest | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F087 | Gateway command / knowledge_file_search | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F088 | Gateway command / knowledge_file_read | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F089 | Gateway command / knowledge_incremental_sync | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F090 | Gateway command / knowledge_incremental_status | PARTIAL | MAIN DENIAL | [main-integrations.json](main-integrations.json) |
| F091 | Gateway command / knowledge_feedback_submit | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F092 | Gateway command / knowledge_feedback_get | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F093 | Gateway command / knowledge_feedback_apply | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F094 | Gateway command / bug_triage | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F095 | Gateway command / bug_propose | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F096 | Gateway command / wbs_draft | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F097 | Gateway command / wbs_get | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F098 | Gateway command / wbs_adopt | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F099 | Gateway command / wbs_next | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F100 | Gateway command / wbs_from_ba | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F101 | Gateway command / qa_evidence_capture | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F102 | Gateway command / qa_evidence_get | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F103 | Gateway command / qa_transition_prepare | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F104 | Gateway command / qa_test_run | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F105 | Gateway command / qa_test_get | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F106 | Gateway command / qa_evidence_from_run | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F107 | Gateway command / qa_evidence_list | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F108 | Gateway command / phase_draft | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F109 | Gateway command / phase_get | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F110 | Gateway command / phase_list | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F111 | Gateway command / phase_transition_prepare | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F112 | Gateway command / qa_application_proof_verify | NOT TESTED | SOURCE INVENTORY | [qualification.json](qualification.json) |
| F113 | Gateway command / qa_application_proof_admit | BLOCKED BY AUTHORIZATION | ISOLATED CONTRACT / NO NEW MAIN WRITE | [qualification.json](qualification.json) |
| F114 | Telegram tool / list_projects | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F115 | Telegram tool / search_tasks | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F116 | Telegram tool / get_task_details | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F117 | Telegram tool / get_project_options | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F118 | Telegram tool / get_task_progress | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F119 | Telegram tool / get_task_agent_runs | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F120 | Telegram tool / get_current_agent | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F121 | Telegram tool / get_run_details | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F122 | Telegram tool / get_run_errors | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F123 | Telegram tool / get_checkpoint_status | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F124 | Telegram tool / get_task_artifacts | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F125 | Telegram tool / get_github_prs | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F126 | Telegram tool / get_review_results | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F127 | Telegram tool / get_qa_results | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F128 | Telegram tool / search_knowledge | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F129 | Telegram tool / get_worker_status | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F130 | Telegram tool / get_queue_status | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F131 | Telegram tool / get_system_health | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F132 | Telegram tool / get_n8n_status | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F133 | Telegram tool / create_task | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F134 | Telegram tool / update_task | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F135 | Telegram tool / request_task_execution | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F136 | Telegram tool / resume_task | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F137 | Telegram tool / pause_task | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F138 | Telegram tool / set_execution_mode | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F139 | Telegram tool / request_github_sync | BLOCKED BY AUTHORIZATION | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F140 | Telegram / poller/token/webhook/one-consumer | PASS | ACTUAL OWNER LIVE + MAIN RESTART | [telegram-live-global.json](telegram-live-global.json), [telegram-live-postfix.json](telegram-live-postfix.json), [final-smoke.json](final-smoke.json), [integrity-final.json](integrity-final.json) |
| F141 | Telegram / Vietnamese multi-turn #398 | PASS | ACTUAL OWNER LIVE + MAIN RESTART | [telegram-live-global.json](telegram-live-global.json), [telegram-live-postfix.json](telegram-live-postfix.json), [final-smoke.json](final-smoke.json), [integrity-final.json](integrity-final.json) |
| F142 | Telegram / reply notification397 context | PASS | HISTORICAL OWNER LIVE | [live-reply-397.json](../telegram-observer/live-reply-397.json) |
| F143 | Telegram / pairing/unauthorized/stale/duplicate | PARTIAL | SOURCE / ISOLATED CONTRACT | [telegram-live-global.json](telegram-live-global.json), [telegram-live-postfix.json](telegram-live-postfix.json), [final-smoke.json](final-smoke.json), [integrity-final.json](integrity-final.json) |
| F144 | Telegram / restart conversation persistence | PASS | ACTUAL OWNER LIVE + MAIN RESTART | [telegram-live-global.json](telegram-live-global.json), [telegram-live-postfix.json](telegram-live-postfix.json), [final-smoke.json](final-smoke.json), [integrity-final.json](integrity-final.json) |
| F145 | Telegram / network/Gateway reconnect | PASS | ACTUAL OWNER LIVE + MAIN RESTART | [telegram-live-global.json](telegram-live-global.json), [telegram-live-postfix.json](telegram-live-postfix.json), [final-smoke.json](final-smoke.json), [integrity-final.json](integrity-final.json) |
| F146 | Telegram / Gemini exact model/quota/tool feedback | PASS | ACTUAL OWNER LIVE + MAIN RESTART | [telegram-live-global.json](telegram-live-global.json), [telegram-live-postfix.json](telegram-live-postfix.json), [final-smoke.json](final-smoke.json), [integrity-final.json](integrity-final.json) |
| F147 | Runtime / BA/PM planning379→398 | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F148 | Runtime / Dev398 exact revision | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F149 | Runtime / Reviewer398 verdict/rework | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F150 | Runtime / QA398 JUnit64 | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F151 | Runtime / OFF/AUTO/RUN_ONCE guards | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F152 | Runtime / checkpoint/resume/idempotency | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F153 | Runtime / Owner gates398 vs DONE397 | PARTIAL | HISTORICAL REAL EXECUTION + CURRENT READ | [demo-final.json](../agent-studio-v2-stabilization/demo-final.json), [demo-tests.json](../agent-studio-v2-stabilization/demo-tests.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F154 | Studio / CommandCenter entry/Project/Task/deep link | PARTIAL | MAIN TERMINAL UI + HISTORICAL RUNNING | [browser-uat.json](browser-uat.json), [demo-final.json](../agent-studio-v2-stabilization/demo-final.json) |
| F155 | Studio / Explorer/back/forward/reload | PARTIAL | MAIN TERMINAL UI + HISTORICAL RUNNING | [browser-uat.json](browser-uat.json), [demo-final.json](../agent-studio-v2-stabilization/demo-final.json) |
| F156 | Studio / graph/nodes/edges/attempts/runtime/freshness | PARTIAL | MAIN TERMINAL UI + HISTORICAL RUNNING | [browser-uat.json](browser-uat.json), [demo-final.json](../agent-studio-v2-stabilization/demo-final.json) |
| F157 | Studio / Inspector/timeline/artifacts/native/PR links | PARTIAL | MAIN TERMINAL UI + HISTORICAL RUNNING | [browser-uat.json](browser-uat.json), [demo-final.json](../agent-studio-v2-stabilization/demo-final.json) |
| F158 | Studio / poll/error recovery/no stale overwrite | PARTIAL | MAIN TERMINAL UI + HISTORICAL RUNNING | [browser-uat.json](browser-uat.json), [demo-final.json](../agent-studio-v2-stabilization/demo-final.json) |
| F159 | Studio / mobile touch/layout | PARTIAL | MAIN TERMINAL UI + HISTORICAL RUNNING | [browser-uat.json](browser-uat.json), [demo-final.json](../agent-studio-v2-stabilization/demo-final.json) |
| F160 | Command Center / Mission Control/queue/current run | PASS | MAIN UI READ | [browser-uat.json](browser-uat.json) |
| F161 | Command Center / Workforce roles/availability | PASS | MAIN UI READ | [browser-uat.json](browser-uat.json) |
| F162 | Command Center / Intake/control actions/gates | BLOCKED BY AUTHORIZATION | MAIN UI READ | [browser-uat.json](browser-uat.json) |
| F163 | Command Center / Reports/Analysis/read/export/audit | PASS | MAIN UI READ | [browser-uat.json](browser-uat.json) |
| F164 | OpenProject / projects/search/details/journals/parent | PARTIAL | MAIN READ / ACL | [main-integrations.json](main-integrations.json), [integrity-final.json](integrity-final.json) |
| F165 | OpenProject / members/ACL/workflow status | PARTIAL | MAIN READ / ACL | [main-integrations.json](main-integrations.json), [integrity-final.json](integrity-final.json) |
| F166 | GitHub / auth/repository/branch/commit/PR15 | PARTIAL | MAIN READ + HISTORICAL AI REVIEW | [github-pr15.json](github-pr15.json), [github-pr15.diff](github-pr15.diff), [semantic-read-checks.json](semantic-read-checks.json) |
| F167 | GitHub / review/CI/provenance/state sync | PARTIAL | MAIN READ + HISTORICAL AI REVIEW | [github-pr15.json](github-pr15.json), [github-pr15.diff](github-pr15.diff), [semantic-read-checks.json](semantic-read-checks.json) |
| F168 | RAG / known-document lexical/semantic/citations | PARTIAL | MAIN RETRIEVAL / UNQUALIFIED ANSWERABILITY | [rag-main-queries.json](rag-main-queries.json), [browser-uat.json](browser-uat.json), [rag-recovery-probe.json](rag-recovery-probe.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F169 | RAG / project/role/actor isolation | PARTIAL | MAIN RETRIEVAL / UNQUALIFIED ANSWERABILITY | [rag-main-queries.json](rag-main-queries.json), [browser-uat.json](browser-uat.json), [rag-recovery-probe.json](rag-recovery-probe.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F170 | RAG / index/sync/storage/recovery | PARTIAL | MAIN RETRIEVAL / UNQUALIFIED ANSWERABILITY | [rag-main-queries.json](rag-main-queries.json), [browser-uat.json](browser-uat.json), [rag-recovery-probe.json](rag-recovery-probe.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F171 | RAG / Telegram knowledge adapter/report integration | PARTIAL | MAIN RETRIEVAL / UNQUALIFIED ANSWERABILITY | [rag-main-queries.json](rag-main-queries.json), [browser-uat.json](browser-uat.json), [rag-recovery-probe.json](rag-recovery-probe.json), [semantic-read-checks.json](semantic-read-checks.json) |
| F172 | Notifications / N01 completed397 | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F173 | Notifications / N02 dev-only no completion | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F174 | Notifications / N03 QA_FAILED | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F175 | Notifications / N04 BLOCKED | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F176 | Notifications / N05 awaiting owner398 | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F177 | Notifications / N06 n8n offline/retry | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F178 | Notifications / N07 Telegram offline/persistence | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F179 | Notifications / N08 duplicate semantics | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F180 | Notifications / N09 reply context | PARTIAL | HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT | [notification-main-history.json](notification-main-history.json), [live-reply-397.json](../telegram-observer/live-reply-397.json), [qualification.json](qualification.json) |
| F181 | Operations / startup/restart policy/persistence/networks | PASS | MAIN CONTROLLED RESTART + INTEGRITY | [bot-deployment.json](bot-deployment.json), [deployment.json](core-candidate-v2/deployment.json), [integrity-final.json](integrity-final.json), [final-smoke.json](final-smoke.json) |
| F182 | Operations / controlled Telegram/Gateway restart/no replay | PASS | MAIN CONTROLLED RESTART + INTEGRITY | [bot-deployment.json](bot-deployment.json), [deployment.json](core-candidate-v2/deployment.json), [integrity-final.json](integrity-final.json), [final-smoke.json](final-smoke.json) |
| F183 | Gateway route / GET /internal/automation/status | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F184 | Gateway route / GET /internal/automation/monitor | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F185 | Gateway route / POST /internal/automation/commands | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
| F186 | n8n workflow / QLDAPM — Telegram Agent Notifications | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F187 | n8n workflow / WF01: Local Document Ingestion | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F188 | n8n workflow / WF02: OpenProject Event Sync | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F189 | n8n workflow / WF03: Natural Language Request Orchestrator | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F190 | n8n workflow / WF04: Multi-Agent Execution Tracking | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F191 | n8n workflow / WF05: Native API Approval Workflow | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F192 | n8n workflow / WF06: Native API Execution & Verification | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F193 | n8n workflow / WF07: Daily Project Brief | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F194 | n8n workflow / WF08: Sprint Risk | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F195 | n8n workflow / WF09: Bug Lifecycle Automation | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F196 | n8n workflow / WF10: Task Orchestration & Decomposition | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F197 | n8n workflow / WF11: QA Gate Transition | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F198 | n8n workflow / WF12: Weekly Summary | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F199 | n8n workflow / WF13: Second Brain RAG Re-indexing | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F200 | n8n workflow / WF14: Durable RAG Recovery | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F201 | n8n workflow / WF15: Reconciliation & Drift Detection | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F202 | n8n workflow / WF16: Main Health Monitoring | PARTIAL | DEPLOYED CONTRACT + HISTORICAL EXECUTIONS | [n8n-inventory.json](n8n-inventory.json), [n8n-contracts.json](n8n-contracts.json) |
| F203 | Telegram tool / get_active_agents | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F204 | Telegram tool / get_blocked_tasks | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F205 | Telegram tool / get_pending_approvals | PASS | MAIN ADAPTER READ | [main-integrations.json](main-integrations.json), [semantic-read-checks.json](semantic-read-checks.json), [additional-reads.json](additional-reads.json) |
| F206 | Gateway MCP / 97 action tools, filtered by role, /mcp transport | PARTIAL | SOURCE / ISOLATED CONTRACT | [qualification.json](qualification.json) |
