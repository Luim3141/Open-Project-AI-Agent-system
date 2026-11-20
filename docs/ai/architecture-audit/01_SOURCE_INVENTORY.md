# HỒ SƠ PHÁP Y M1: DANH MỤC MÃ NGUỒN TOÀN DIỆN (SOURCE INVENTORY)
> Thời điểm kiểm toán: `2026-10-30 20:26:54 UTC`  
> Git Branch: `codex/local-multi-agent-upgrade`  
> Trạng thái: **CHÍNH XÁC 100% THEO FILESYSTEM THẬT**

---

## 1. TỔNG QUAN HỆ THỐNG MÃ NGUỒN

Hệ thống **QLDAPM MAIN** bao gồm 4 phân hệ mã nguồn chính tham gia trực tiếp vào kiến trúc điều phối và thực thi AI:

1. **AI Gateway (`openproject/ai/gateway/`):** 102 files. Backend Python Async FastAPI điều phối Agent, quản lý ngân sách Gemini Free Tier, Qdrant Vector DB, và kết nối OpenClaw.
2. **OpenProject Overlay (`openproject/ai/core/overlay/`):** 63 files. Ruby on Rails Engine mở rộng OpenProject: Controller, Views (UI Command Center), Model Hooks, RBAC, và Routes.
3. **Automation & Workflows (`openproject/ai/automation/`):** 71 files. Kịch bản vận hành, worker pipeline, n8n deployment, Docker definitions.
4. **Tools & Verification (`tools/`):** 90 files. Bộ công cụ UAT, Playwright tests, invariant checkers, deployment builders.

### Thống kê theo phân loại chức năng (Categories):
- **Build / Deployment:** 17 files (2,385 lines)
- **Contract / Interface:** 7 files (167 lines)
- **Implementation:** 237 files (47,141 lines)
- **Legacy / Maintenance:** 2 files (116 lines)
- **Test / Verification:** 63 files (3,936 lines)

**Tổng cộng khảo sát trực tiếp:** 326 files (53,745 lines)

---

## 2. CHI TIẾT PHÂN HỆ AI GATEWAY (`openproject/ai/gateway/`)

| File Path | Category | Lines | SHA256 (12 chars) | Mục đích / Chức năng |
| :--- | :--- | :--- | :--- | :--- |
| `openproject/ai/gateway/__init__.py` | Implementation | 4 | `0aad176a746f` | Thành phần cốt lõi của AI Gateway (__init__.py) |
| `openproject/ai/gateway/agent_models.py` | Implementation | 182 | `23d01813e618` | Thành phần cốt lõi của AI Gateway (agent_models.py) |
| `openproject/ai/gateway/agent_registry.py` | Implementation | 194 | `69fedcafcc6a` | Thành phần cốt lõi của AI Gateway (agent_registry.py) |
| `openproject/ai/gateway/agent_status.py` | Implementation | 173 | `774fc625c95d` | Thành phần cốt lõi của AI Gateway (agent_status.py) |
| `openproject/ai/gateway/agent_trace.py` | Implementation | 45 | `823b0d9b7955` | Thành phần cốt lõi của AI Gateway (agent_trace.py) |
| `openproject/ai/gateway/ai_worker.py` | Implementation | 142 | `fa078049399c` | Thành phần cốt lõi của AI Gateway (ai_worker.py) |
| `openproject/ai/gateway/app.py` | Implementation | 418 | `ebc0401c5a9b` | Thành phần cốt lõi của AI Gateway (app.py) |
| `openproject/ai/gateway/application_qa_intake.py` | Implementation | 109 | `66cf4709d1a0` | Thành phần cốt lõi của AI Gateway (application_qa_intake.py) |
| `openproject/ai/gateway/application_qa_proof.py` | Implementation | 129 | `550213cf9f9a` | Thành phần cốt lõi của AI Gateway (application_qa_proof.py) |
| `openproject/ai/gateway/automation.py` | Implementation | 118 | `f15c37cf1220` | Thành phần cốt lõi của AI Gateway (automation.py) |
| `openproject/ai/gateway/ba_agent.py` | Implementation | 246 | `bf79889ece1f` | Thành phần cốt lõi của AI Gateway (ba_agent.py) |
| `openproject/ai/gateway/bridge.py` | Implementation | 31 | `3e8d3e3eb167` | Thành phần cốt lõi của AI Gateway (bridge.py) |
| `openproject/ai/gateway/bug_lifecycle.py` | Implementation | 123 | `f978e1626481` | Thành phần cốt lõi của AI Gateway (bug_lifecycle.py) |
| `openproject/ai/gateway/business_acceptance.py` | Implementation | 121 | `5d94990f8203` | Thành phần cốt lõi của AI Gateway (business_acceptance.py) |
| `openproject/ai/gateway/business_runs.py` | Implementation | 350 | `ac11549797a7` | Thành phần cốt lõi của AI Gateway (business_runs.py) |
| `openproject/ai/gateway/catalog.py` | Implementation | 137 | `f588aaca446e` | Thành phần cốt lõi của AI Gateway (catalog.py) |
| `openproject/ai/gateway/control_center_state.py` | Implementation | 126 | `a677f2d1580a` | Thành phần cốt lõi của AI Gateway (control_center_state.py) |
| `openproject/ai/gateway/conversation_memory.py` | Implementation | 108 | `f4de9f058de8` | Thành phần cốt lõi của AI Gateway (conversation_memory.py) |
| `openproject/ai/gateway/daily_brief.py` | Implementation | 76 | `065208e8ccfb` | Thành phần cốt lõi của AI Gateway (daily_brief.py) |
| `openproject/ai/gateway/decision_memory.py` | Implementation | 94 | `87b39e4917af` | Thành phần cốt lõi của AI Gateway (decision_memory.py) |
| `openproject/ai/gateway/dev_agent.py` | Implementation | 222 | `12fc846f44e4` | Thành phần cốt lõi của AI Gateway (dev_agent.py) |
| `openproject/ai/gateway/e2e_demo.py` | Implementation | 4 | `0e9fb36ce68a` | Thành phần cốt lõi của AI Gateway (e2e_demo.py) |
| `openproject/ai/gateway/engineering.py` | Implementation | 445 | `3fb503af9e31` | Thành phần cốt lõi của AI Gateway (engineering.py) |
| `openproject/ai/gateway/engineering_auto.py` | Implementation | 91 | `765201ef48ae` | Thành phần cốt lõi của AI Gateway (engineering_auto.py) |
| `openproject/ai/gateway/engineering_github_sync.py` | Implementation | 272 | `a5b028dfc4ca` | Thành phần cốt lõi của AI Gateway (engineering_github_sync.py) |
| `openproject/ai/gateway/engineering_lifecycle.py` | Implementation | 135 | `3b3602b01682` | Thành phần cốt lõi của AI Gateway (engineering_lifecycle.py) |
| `openproject/ai/gateway/engineering_monitor.py` | Implementation | 67 | `948553193022` | Thành phần cốt lõi của AI Gateway (engineering_monitor.py) |
| `openproject/ai/gateway/engineering_operator.py` | Implementation | 208 | `b8370d639a25` | Thành phần cốt lõi của AI Gateway (engineering_operator.py) |
| `openproject/ai/gateway/engineering_personas.py` | Contract / Interface | 17 | `9d5c4b7dc3df` | Thành phần cốt lõi của AI Gateway (engineering_personas.py) |
| `openproject/ai/gateway/engineering_planning.py` | Implementation | 176 | `d7955e861ade` | Thành phần cốt lõi của AI Gateway (engineering_planning.py) |
| `openproject/ai/gateway/engineering_reporting.py` | Implementation | 521 | `45cbbc96e815` | Thành phần cốt lõi của AI Gateway (engineering_reporting.py) |
| `openproject/ai/gateway/engineering_state_sync.py` | Implementation | 348 | `a3c48281e4f9` | Thành phần cốt lõi của AI Gateway (engineering_state_sync.py) |
| `openproject/ai/gateway/engineering_units.py` | Contract / Interface | 18 | `96045c0f210c` | Thành phần cốt lõi của AI Gateway (engineering_units.py) |
| `openproject/ai/gateway/execution_events.py` | Implementation | 49 | `e10e8247f81f` | Thành phần cốt lõi của AI Gateway (execution_events.py) |
| `openproject/ai/gateway/execution_monitor.py` | Implementation | 188 | `84a726ffa545` | Thành phần cốt lõi của AI Gateway (execution_monitor.py) |
| `openproject/ai/gateway/file_knowledge.py` | Implementation | 104 | `a0cc223eddc4` | Thành phần cốt lõi của AI Gateway (file_knowledge.py) |
| `openproject/ai/gateway/gemini.py` | Implementation | 748 | `e2a5da071888` | Thành phần cốt lõi của AI Gateway (gemini.py) |
| `openproject/ai/gateway/intent_evals.py` | Implementation | 529 | `19f534aab5dc` | Thành phần cốt lõi của AI Gateway (intent_evals.py) |
| `openproject/ai/gateway/knowledge_classifier.py` | Implementation | 138 | `6c22928025a4` | Thành phần cốt lõi của AI Gateway (knowledge_classifier.py) |
| `openproject/ai/gateway/knowledge_feedback.py` | Implementation | 106 | `b2aa826227f6` | Thành phần cốt lõi của AI Gateway (knowledge_feedback.py) |
| `openproject/ai/gateway/knowledge_ingestion.py` | Implementation | 184 | `c4283da4f9db` | Thành phần cốt lõi của AI Gateway (knowledge_ingestion.py) |
| `openproject/ai/gateway/knowledge_integrity.py` | Implementation | 66 | `5c55025e47fa` | Thành phần cốt lõi của AI Gateway (knowledge_integrity.py) |
| `openproject/ai/gateway/knowledge_lock.py` | Implementation | 29 | `ea7bd614ca39` | Thành phần cốt lõi của AI Gateway (knowledge_lock.py) |
| `openproject/ai/gateway/knowledge_points.py` | Implementation | 46 | `223373e5e9c6` | Thành phần cốt lõi của AI Gateway (knowledge_points.py) |
| `openproject/ai/gateway/knowledge_retrieval.py` | Implementation | 62 | `762bcb4a456b` | Thành phần cốt lõi của AI Gateway (knowledge_retrieval.py) |
| `openproject/ai/gateway/knowledge_search.py` | Implementation | 336 | `35498ed3fd23` | Thành phần cốt lõi của AI Gateway (knowledge_search.py) |
| `openproject/ai/gateway/knowledge_storage.py` | Implementation | 449 | `ad0ef83d1234` | Thành phần cốt lõi của AI Gateway (knowledge_storage.py) |
| `openproject/ai/gateway/knowledge_ui_answer.py` | Implementation | 66 | `cff5a99b0fa7` | Thành phần cốt lõi của AI Gateway (knowledge_ui_answer.py) |
| `openproject/ai/gateway/live_agents.py` | Implementation | 258 | `8f6dc64822a4` | Thành phần cốt lõi của AI Gateway (live_agents.py) |
| `openproject/ai/gateway/local_loaders.py` | Implementation | 141 | `fd3d903d9a5e` | Thành phần cốt lõi của AI Gateway (local_loaders.py) |
| `openproject/ai/gateway/local_operator.py` | Implementation | 67 | `642c0b40a02f` | Thành phần cốt lõi của AI Gateway (local_operator.py) |
| `openproject/ai/gateway/local_queries.py` | Implementation | 109 | `5c9bb7980b5c` | Thành phần cốt lõi của AI Gateway (local_queries.py) |
| `openproject/ai/gateway/monitoring.py` | Implementation | 114 | `1f5eecb22301` | Thành phần cốt lõi của AI Gateway (monitoring.py) |
| `openproject/ai/gateway/n8n_indexing_hook.py` | Implementation | 156 | `d81cf3942098` | Thành phần cốt lõi của AI Gateway (n8n_indexing_hook.py) |
| `openproject/ai/gateway/native.py` | Implementation | 156 | `88f6dd6c083d` | Thành phần cốt lõi của AI Gateway (native.py) |
| `openproject/ai/gateway/native_deletion.py` | Implementation | 160 | `7d57b353c2be` | Thành phần cốt lõi của AI Gateway (native_deletion.py) |
| `openproject/ai/gateway/native_dependency.py` | Implementation | 109 | `9b781062fc91` | Thành phần cốt lõi của AI Gateway (native_dependency.py) |
| `openproject/ai/gateway/native_dependency_change.py` | Implementation | 96 | `389d6d636241` | Thành phần cốt lõi của AI Gateway (native_dependency_change.py) |
| `openproject/ai/gateway/native_incremental.py` | Implementation | 100 | `23a8eb4f8229` | Thành phần cốt lõi của AI Gateway (native_incremental.py) |
| `openproject/ai/gateway/native_phase.py` | Implementation | 161 | `468c967a7189` | Thành phần cốt lõi của AI Gateway (native_phase.py) |
| `openproject/ai/gateway/native_phase_bridge.py` | Implementation | 72 | `be9543089eae` | Thành phần cốt lõi của AI Gateway (native_phase_bridge.py) |
| `openproject/ai/gateway/native_qa.py` | Implementation | 273 | `824a9881cec3` | Thành phần cốt lõi của AI Gateway (native_qa.py) |
| `openproject/ai/gateway/native_qa_bridge.py` | Implementation | 119 | `3862469909e4` | Thành phần cốt lõi của AI Gateway (native_qa_bridge.py) |
| `openproject/ai/gateway/native_qa_runs.py` | Implementation | 280 | `1c15142d047d` | Thành phần cốt lõi của AI Gateway (native_qa_runs.py) |
| `openproject/ai/gateway/native_wbs.py` | Implementation | 383 | `dc3605f9af52` | Thành phần cốt lõi của AI Gateway (native_wbs.py) |
| `openproject/ai/gateway/native_wbs_hierarchy.py` | Implementation | 103 | `184247c963c0` | Thành phần cốt lõi của AI Gateway (native_wbs_hierarchy.py) |
| `openproject/ai/gateway/native_wbs_relations.py` | Implementation | 155 | `5b340673c1e8` | Thành phần cốt lõi của AI Gateway (native_wbs_relations.py) |
| `openproject/ai/gateway/notification_delivery.py` | Implementation | 124 | `c26307c78a5a` | Thành phần cốt lõi của AI Gateway (notification_delivery.py) |
| `openproject/ai/gateway/openproject_loader.py` | Implementation | 147 | `fb7485026a90` | Thành phần cốt lõi của AI Gateway (openproject_loader.py) |
| `openproject/ai/gateway/pdf_text.py` | Implementation | 42 | `690f5ab4f3b4` | Thành phần cốt lõi của AI Gateway (pdf_text.py) |
| `openproject/ai/gateway/permissions.py` | Implementation | 36 | `b7bc634cadd5` | Thành phần cốt lõi của AI Gateway (permissions.py) |
| `openproject/ai/gateway/planner.py` | Implementation | 185 | `698b696d620b` | Thành phần cốt lõi của AI Gateway (planner.py) |
| `openproject/ai/gateway/pm_agent.py` | Implementation | 294 | `b059338e04ac` | Thành phần cốt lõi của AI Gateway (pm_agent.py) |
| `openproject/ai/gateway/presentation.py` | Implementation | 167 | `6cd70fb1ee03` | Thành phần cốt lõi của AI Gateway (presentation.py) |
| `openproject/ai/gateway/proposal_aggregation.py` | Implementation | 108 | `dc89e3a1ee3a` | Thành phần cốt lõi của AI Gateway (proposal_aggregation.py) |
| `openproject/ai/gateway/proposal_ux.py` | Implementation | 162 | `3458917e8e5b` | Thành phần cốt lõi của AI Gateway (proposal_ux.py) |
| `openproject/ai/gateway/qa_agent.py` | Implementation | 297 | `8936dbcf01bc` | Thành phần cốt lõi của AI Gateway (qa_agent.py) |
| `openproject/ai/gateway/qa_change_workflow.py` | Implementation | 163 | `2fbadd0fbe75` | Thành phần cốt lõi của AI Gateway (qa_change_workflow.py) |
| `openproject/ai/gateway/quota_panel.py` | Implementation | 43 | `8965f532a58a` | Thành phần cốt lõi của AI Gateway (quota_panel.py) |
| `openproject/ai/gateway/reviewer_agent.py` | Implementation | 188 | `e58d39d1ae8d` | Thành phần cốt lõi của AI Gateway (reviewer_agent.py) |
| `openproject/ai/gateway/role_alerts.py` | Implementation | 209 | `e548fce01bac` | Thành phần cốt lõi của AI Gateway (role_alerts.py) |
| `openproject/ai/gateway/run_ingest_all.py` | Implementation | 95 | `5284a11de773` | Thành phần cốt lõi của AI Gateway (run_ingest_all.py) |
| `openproject/ai/gateway/scheduler_registry.py` | Implementation | 200 | `be7c2efd59ec` | Thành phần cốt lõi của AI Gateway (scheduler_registry.py) |
| `openproject/ai/gateway/service.py` | Implementation | 1807 | `2b79bad9a466` | Thành phần cốt lõi của AI Gateway (service.py) |
| `openproject/ai/gateway/sprint_readiness.py` | Implementation | 237 | `d300f4408d6c` | Thành phần cốt lõi của AI Gateway (sprint_readiness.py) |
| `openproject/ai/gateway/sprint_report.py` | Implementation | 296 | `749b3a7ed861` | Thành phần cốt lõi của AI Gateway (sprint_report.py) |
| `openproject/ai/gateway/stdio.py` | Implementation | 33 | `e22d1b414510` | Thành phần cốt lõi của AI Gateway (stdio.py) |
| `openproject/ai/gateway/store.py` | Implementation | 1118 | `3d55114d4e87` | Thành phần cốt lõi của AI Gateway (store.py) |
| `openproject/ai/gateway/supervisor.py` | Implementation | 140 | `e9c6d8624877` | Thành phần cốt lõi của AI Gateway (supervisor.py) |
| `openproject/ai/gateway/supervisor_isolation.py` | Implementation | 139 | `a3cfb03a49c6` | Thành phần cốt lõi của AI Gateway (supervisor_isolation.py) |
| `openproject/ai/gateway/tasks_progress.py` | Implementation | 138 | `aa0363e4611b` | Thành phần cốt lõi của AI Gateway (tasks_progress.py) |
| `openproject/ai/gateway/vector_client.py` | Implementation | 327 | `ed70c922d763` | Thành phần cốt lõi của AI Gateway (vector_client.py) |
| `openproject/ai/gateway/wbs_analysis.py` | Implementation | 91 | `32dbec1aa665` | Thành phần cốt lõi của AI Gateway (wbs_analysis.py) |
| `openproject/ai/gateway/weekly_report.py` | Implementation | 257 | `a827773969cc` | Thành phần cốt lõi của AI Gateway (weekly_report.py) |
| `openproject/ai/gateway/workflow_errors.py` | Implementation | 12 | `9758bb44d3a5` | Thành phần cốt lõi của AI Gateway (workflow_errors.py) |
| `openproject/ai/gateway/workflow_pause.py` | Implementation | 126 | `5b1753c2b026` | Thành phần cốt lõi của AI Gateway (workflow_pause.py) |
| `openproject/ai/gateway/workflow_timeline.py` | Implementation | 132 | `3786d94d32cb` | Thành phần cốt lõi của AI Gateway (workflow_timeline.py) |
| `openproject/ai/gateway/workload_detector.py` | Implementation | 178 | `f5c0ef68eeba` | Thành phần cốt lõi của AI Gateway (workload_detector.py) |
| `openproject/ai/gateway/workspace.py` | Implementation | 102 | `088fc84bba3d` | Thành phần cốt lõi của AI Gateway (workspace.py) |
| `openproject/ai/gateway/application_qa_producer_manifest.json` | Contract / Interface | 9 | `5758703a96e1` | Thành phần cốt lõi của AI Gateway (application_qa_producer_manifest.json) |
| `openproject/ai/gateway/MODEL_ALLOWLIST.json` | Contract / Interface | 20 | `296c5214f596` | Thành phần cốt lõi của AI Gateway (MODEL_ALLOWLIST.json) |
| `openproject/ai/gateway/knowledge_schema.sql` | Contract / Interface | 34 | `bb1340698424` | Thành phần cốt lõi của AI Gateway (knowledge_schema.sql) |

---

## 3. CHI TIẾT PHÂN HỆ OPENPROJECT OVERLAY (`openproject/ai/core/overlay/`)

| File Path | Category | Lines | SHA256 (12 chars) | Mục đích / Chức năng |
| :--- | :--- | :--- | :--- | :--- |
| `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb` | Implementation | 475 | `4e3988bfcf05` | Rails extension / view / controller (qldapm_ai_controller.rb) |
| `openproject/ai/core/overlay/app/controllers/qldapm_gates_controller.rb` | Implementation | 51 | `2d890c2ab180` | Rails extension / view / controller (qldapm_gates_controller.rb) |
| `openproject/ai/core/overlay/app/controllers/concerns/qldapm_work_package_tree.rb` | Implementation | 20 | `b7b8cb5b9566` | Rails extension / view / controller (qldapm_work_package_tree.rb) |
| `openproject/ai/core/overlay/app/helpers/qldapm_ai_helper.rb` | Implementation | 70 | `965563da6f78` | Rails extension / view / controller (qldapm_ai_helper.rb) |
| `openproject/ai/core/overlay/app/models/qldapm_work_package_tree_hook.rb` | Implementation | 3 | `20d33217d005` | Rails extension / view / controller (qldapm_work_package_tree_hook.rb) |
| `openproject/ai/core/overlay/app/models/concerns/qldapm_board_write.rb` | Implementation | 19 | `dafcc357827f` | Rails extension / view / controller (qldapm_board_write.rb) |
| `openproject/ai/core/overlay/app/models/concerns/qldapm_gate_write.rb` | Implementation | 148 | `be6770088d92` | Rails extension / view / controller (qldapm_gate_write.rb) |
| `openproject/ai/core/overlay/app/models/concerns/qldapm_relation_write.rb` | Implementation | 18 | `a5c0664d7376` | Rails extension / view / controller (qldapm_relation_write.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/board_permissions.rb` | Implementation | 8 | `72e5b4da061b` | Rails extension / view / controller (board_permissions.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/gate_policy.rb` | Implementation | 207 | `b9270f61092a` | Rails extension / view / controller (gate_policy.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/insight_response.rb` | Implementation | 8 | `6054aab05f6e` | Rails extension / view / controller (insight_response.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/insight_snapshot.rb` | Implementation | 8 | `0caefe162c1e` | Rails extension / view / controller (insight_snapshot.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/mutation_receipt.rb` | Implementation | 8 | `39d9cba1a247` | Rails extension / view / controller (mutation_receipt.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/native_deletion_event.rb` | Implementation | 7 | `f934353dfa69` | Rails extension / view / controller (native_deletion_event.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/permission_ceiling.rb` | Implementation | 21 | `1f2f8e52deff` | Rails extension / view / controller (permission_ceiling.rb) |
| `openproject/ai/core/overlay/app/models/qldapm/rbac.rb` | Contract / Interface | 57 | `80e707435460` | Rails extension / view / controller (rbac.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/ai_bridge.rb` | Implementation | 88 | `050e18d2c657` | Rails extension / view / controller (ai_bridge.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/application_qa_receipt.rb` | Implementation | 46 | `7a715283cd0d` | Rails extension / view / controller (application_qa_receipt.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/application_qa_sources.rb` | Implementation | 17 | `e477d2e58737` | Rails extension / view / controller (application_qa_sources.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/dependency_change.rb` | Implementation | 117 | `443f7502c20c` | Rails extension / view / controller (dependency_change.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/dependency_mutation.rb` | Implementation | 132 | `35a20a498fef` | Rails extension / view / controller (dependency_mutation.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/gate_actions.rb` | Implementation | 139 | `34e2e3b7959d` | Rails extension / view / controller (gate_actions.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/hierarchy_readback.rb` | Implementation | 16 | `3cb44e0ce54c` | Rails extension / view / controller (hierarchy_readback.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/insight_metrics.rb` | Implementation | 61 | `f26158ef4a51` | Rails extension / view / controller (insight_metrics.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/insights.rb` | Implementation | 120 | `5fb2a2aefabd` | Rails extension / view / controller (insights.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/mutations.rb` | Implementation | 114 | `3b161a0bdb79` | Rails extension / view / controller (mutations.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/native_deletion.rb` | Implementation | 89 | `1663269c0afd` | Rails extension / view / controller (native_deletion.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/native_phase_receipt.rb` | Implementation | 94 | `b9ad2e9d2078` | Rails extension / view / controller (native_phase_receipt.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/qa_evidence_receipt.rb` | Implementation | 127 | `e181f48a0fff` | Rails extension / view / controller (qa_evidence_receipt.rb) |
| `openproject/ai/core/overlay/app/services/qldapm/test_receipt.rb` | Test / Verification | 25 | `9e00e3cc4e59` | Rails extension / view / controller (test_receipt.rb) |
| `openproject/ai/core/overlay/app/services/work_packages/create_service.rb` | Implementation | 120 | `e9e358fa7d6d` | Rails extension / view / controller (create_service.rb) |
| `openproject/ai/core/overlay/app/services/work_packages/set_attributes_service/derive_progress_values_status_based.rb` | Implementation | 83 | `91f7faeb19b9` | Rails extension / view / controller (derive_progress_values_status_based.rb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_control_center.html.erb` | Implementation | 53 | `daa9e75fe60b` | Rails extension / view / controller (_control_center.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_daily_brief.html.erb` | Implementation | 47 | `c19432aed814` | Rails extension / view / controller (_daily_brief.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_classic.html.erb` | Implementation | 851 | `1c5c8d0c3305` | Rails extension / view / controller (_engineering_classic.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb` | Implementation | 2495 | `65ac52349475` | Rails extension / view / controller (_engineering_command_center.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_execution_client.html.erb` | Implementation | 1273 | `0088a4244c85` | Rails extension / view / controller (_execution_client.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_execution_style.html.erb` | Implementation | 1346 | `79921472b417` | Rails extension / view / controller (_execution_style.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/_result.html.erb` | Implementation | 74 | `a3da01d66e82` | Rails extension / view / controller (_result.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/engineering.html.erb` | Implementation | 8 | `f50ebd3a8c79` | Rails extension / view / controller (engineering.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/execution.html.erb` | Implementation | 202 | `8e19937d67b8` | Rails extension / view / controller (execution.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/executions.html.erb` | Implementation | 147 | `b986b0f42dec` | Rails extension / view / controller (executions.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/insights.html.erb` | Implementation | 24 | `96ba8c18122f` | Rails extension / view / controller (insights.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/permissions.html.erb` | Implementation | 25 | `934dfc3b2872` | Rails extension / view / controller (permissions.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/phases.html.erb` | Implementation | 46 | `837b8af70395` | Rails extension / view / controller (phases.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/qa_evidence.html.erb` | Implementation | 113 | `24eabf1046f7` | Rails extension / view / controller (qa_evidence.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_ai/show.html.erb` | Implementation | 106 | `34ccae44941d` | Rails extension / view / controller (show.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_gates/index.html.erb` | Implementation | 7 | `0f0d84a338d5` | Rails extension / view / controller (index.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_gates/show.html.erb` | Implementation | 102 | `e0ed99f9cded` | Rails extension / view / controller (show.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_work_packages/_navigation.html.erb` | Implementation | 67 | `5c947a5a1fb3` | Rails extension / view / controller (_navigation.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_work_packages/_node.html.erb` | Implementation | 16 | `7539338e8334` | Rails extension / view / controller (_node.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_work_packages/_row.html.erb` | Implementation | 6 | `fcce5414b218` | Rails extension / view / controller (_row.html.erb) |
| `openproject/ai/core/overlay/app/views/qldapm_work_packages/index.html.erb` | Implementation | 57 | `b26620ea0b8d` | Rails extension / view / controller (index.html.erb) |
| `openproject/ai/core/overlay/app/workers/qldapm/insight_snapshot_job.rb` | Implementation | 7 | `5b9b077b197c` | Rails extension / view / controller (insight_snapshot_job.rb) |
| `openproject/ai/core/overlay/config/routes.rb` | Implementation | 1437 | `76b54436ad70` | Rails extension / view / controller (routes.rb) |
| `openproject/ai/core/overlay/config/initializers/qldapm_gates.rb` | Implementation | 41 | `7e71831e284e` | Rails extension / view / controller (qldapm_gates.rb) |
| `openproject/ai/core/overlay/config/initializers/zz_qldapm_inflections.rb` | Implementation | 2 | `f6c192fd7283` | Rails extension / view / controller (zz_qldapm_inflections.rb) |
| `openproject/ai/core/overlay/db/migrate/20261009160000_add_qldapm_gate_to_work_packages.rb` | Implementation | 5 | `0a93924c62db` | Rails extension / view / controller (20261009160000_add_qldapm_gate_to_work_packages.rb) |
| `openproject/ai/core/overlay/db/migrate/20261010180000_create_qldapm_insight_snapshots.rb` | Implementation | 19 | `954c3b6f1fb1` | Rails extension / view / controller (20261010180000_create_qldapm_insight_snapshots.rb) |
| `openproject/ai/core/overlay/db/migrate/20261010190000_create_qldapm_mutation_receipts.rb` | Implementation | 16 | `ff4675ae0362` | Rails extension / view / controller (20261010190000_create_qldapm_mutation_receipts.rb) |
| `openproject/ai/core/overlay/db/migrate/20261026000000_create_qldapm_native_deletion_events.rb` | Implementation | 25 | `14727aabc578` | Rails extension / view / controller (20261026000000_create_qldapm_native_deletion_events.rb) |
| `openproject/ai/core/overlay/lib/api/v3/root.rb` | Implementation | 121 | `f1a2ec3dbd3d` | Rails extension / view / controller (root.rb) |
| `openproject/ai/core/overlay/lib/api/v3/qldapm/gates_api.rb` | Implementation | 287 | `d6ea1792ab9a` | Rails extension / view / controller (gates_api.rb) |

---

## 4. CHI TIẾT PHÂN HỆ AUTOMATION & PIPELINES (`openproject/ai/automation/`)

| File Path | Category | Lines | SHA256 (12 chars) | Mục đích / Chức năng |
| :--- | :--- | :--- | :--- | :--- |
| `openproject/ai/automation/add_webhook_ids.py` | Implementation | 15 | `83f7a148a8dc` | Script tự động hóa & container definitions |
| `openproject/ai/automation/automation_stability_qualification.py` | Implementation | 226 | `d586f58a6786` | Script tự động hóa & container definitions |
| `openproject/ai/automation/backup_n8n_pre_prune.py` | Legacy / Maintenance | 28 | `f6f6b135324b` | Script tự động hóa & container definitions |
| `openproject/ai/automation/check_errors.py` | Test / Verification | 22 | `0e2d11aa45e5` | Script tự động hóa & container definitions |
| `openproject/ai/automation/check_n8n_executions.py` | Test / Verification | 19 | `ad4a4acba450` | Script tự động hóa & container definitions |
| `openproject/ai/automation/checkpoint.py` | Implementation | 52 | `326ea26ce6f7` | Script tự động hóa & container definitions |
| `openproject/ai/automation/clean_activate_workflows.py` | Implementation | 41 | `bfa7518a7d98` | Script tự động hóa & container definitions |
| `openproject/ai/automation/comment_sync_qualification.py` | Implementation | 90 | `9db1e95b7077` | Script tự động hóa & container definitions |
| `openproject/ai/automation/debug_n8n_webhook.py` | Implementation | 31 | `cb165dce61ca` | Script tự động hóa & container definitions |
| `openproject/ai/automation/dedup_workflows.py` | Implementation | 38 | `4990008272a6` | Script tự động hóa & container definitions |
| `openproject/ai/automation/deploy_real_n8n_workflows.py` | Build / Deployment | 1949 | `5dfbb7aeb0e0` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_acceptance.py` | Implementation | 35 | `4817cc796502` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_acceptance_crud.py` | Implementation | 68 | `c0b37ef7b1b4` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_bootstrap.py` | Build / Deployment | 65 | `fe30af2211aa` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_checkpoint.py` | Implementation | 35 | `4a8dcf649e95` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_delivery.py` | Implementation | 204 | `2ff538485cdb` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_demo.py` | Implementation | 138 | `f0f8376df39a` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_deploy.py` | Build / Deployment | 93 | `db7ef67eb570` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_deploy_continuation.py` | Test / Verification | 41 | `bad0b43d82f8` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_finalize_continuation.py` | Test / Verification | 230 | `fb84cb4d8a63` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_finalize_handoff.py` | Implementation | 266 | `64fa4c75e378` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_qualify_final.py` | Implementation | 80 | `5b4823467692` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_reconcile_usage.py` | Implementation | 74 | `c8fb8b6800e6` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_verify_continuation.py` | Test / Verification | 56 | `aef6c785e5b3` | Script tự động hóa & container definitions |
| `openproject/ai/automation/engineering_worker.py` | Implementation | 367 | `4e8a374fa5bb` | Script tự động hóa & container definitions |
| `openproject/ai/automation/fix_webhook_paths.py` | Implementation | 39 | `55544bd57a3b` | Script tự động hóa & container definitions |
| `openproject/ai/automation/gemini_16_workflow_qualification.py` | Implementation | 486 | `5f946f4c9c92` | Script tự động hóa & container definitions |
| `openproject/ai/automation/gemini_backup_recovery_drill.py` | Implementation | 649 | `d3e02636c5df` | Script tự động hóa & container definitions |
| `openproject/ai/automation/gemini_e2e_qualification_suite.py` | Implementation | 779 | `42a924b62b80` | Script tự động hóa & container definitions |
| `openproject/ai/automation/generate_n8n_main_workflows.py` | Implementation | 963 | `d3c4a4ea1beb` | Script tự động hóa & container definitions |
| `openproject/ai/automation/ingest_real_docs_corpus.py` | Implementation | 107 | `307658ddbabf` | Script tự động hóa & container definitions |
| `openproject/ai/automation/inspect_completeness_matrix.py` | Test / Verification | 17 | `a7b4b5e48ec9` | Script tự động hóa & container definitions |
| `openproject/ai/automation/inspect_gateway_proc.py` | Test / Verification | 18 | `28d0c5bab016` | Script tự động hóa & container definitions |
| `openproject/ai/automation/inspect_n8n_db.py` | Test / Verification | 23 | `e18d56dc5b8b` | Script tự động hóa & container definitions |
| `openproject/ai/automation/inspect_scan_status.py` | Test / Verification | 28 | `6dfe9fcbbeed` | Script tự động hóa & container definitions |
| `openproject/ai/automation/main_auxiliary_backup.py` | Implementation | 176 | `1899f491d968` | Script tự động hóa & container definitions |
| `openproject/ai/automation/main_backup_schedule.py` | Implementation | 68 | `98b430541331` | Script tự động hóa & container definitions |
| `openproject/ai/automation/main_native_clone.py` | Implementation | 126 | `bb7b21f5b835` | Script tự động hóa & container definitions |
| `openproject/ai/automation/main_operations.py` | Implementation | 155 | `95e786ee716d` | Script tự động hóa & container definitions |
| `openproject/ai/automation/natural_schedule_observation.py` | Implementation | 120 | `80b187f3a44b` | Script tự động hóa & container definitions |
| `openproject/ai/automation/openclaw_provider_gate.py` | Implementation | 100 | `8b90ff4aa283` | Script tự động hóa & container definitions |
| `openproject/ai/automation/operator_uat_preflight.py` | Test / Verification | 99 | `a3f7c3d826ed` | Script tự động hóa & container definitions |
| `openproject/ai/automation/patch_milestone1.py` | Implementation | 203 | `45327238a3fe` | Script tự động hóa & container definitions |
| `openproject/ai/automation/patch_single_wf11.py` | Implementation | 107 | `4ce9ec584664` | Script tự động hóa & container definitions |
| `openproject/ai/automation/patch_wf03.py` | Implementation | 134 | `0144d55535a9` | Script tự động hóa & container definitions |
| `openproject/ai/automation/reconcile_rag_corpus.py` | Implementation | 180 | `33ef41e23fdf` | Script tự động hóa & container definitions |
| `openproject/ai/automation/recreate_n8n_with_prune.py` | Legacy / Maintenance | 88 | `ef8dee28d1e1` | Script tự động hóa & container definitions |
| `openproject/ai/automation/rest_activate_all.py` | Implementation | 38 | `999c5cc25fe9` | Script tự động hóa & container definitions |
| `openproject/ai/automation/rotate_pm_token.py` | Implementation | 168 | `7de114a19ad2` | Script tự động hóa & container definitions |
| `openproject/ai/automation/rotate_webhook_secret.py` | Implementation | 151 | `0479b74e0a2d` | Script tự động hóa & container definitions |
| `openproject/ai/automation/run_full_e2e_acceptance.py` | Implementation | 619 | `ece108ffaefc` | Script tự động hóa & container definitions |
| `openproject/ai/automation/safe_postgres_restore.py` | Implementation | 116 | `062083d7929b` | Script tự động hóa & container definitions |
| `openproject/ai/automation/test_activate_wf05.py` | Test / Verification | 32 | `bdec63ae927c` | Script tự động hóa & container definitions |
| `openproject/ai/automation/test_activate_wf13.py` | Test / Verification | 27 | `3c159d85dcb8` | Script tự động hóa & container definitions |
| `openproject/ai/automation/test_live_gemini_agents.py` | Test / Verification | 83 | `5705084e2230` | Script tự động hóa & container definitions |
| `openproject/ai/automation/test_n8n_patch.py` | Test / Verification | 15 | `dc4fb739d34c` | Script tự động hóa & container definitions |
| `openproject/ai/automation/test_second_brain_multichannel_isolated.py` | Test / Verification | 357 | `7e29df4c5c0e` | Script tự động hóa & container definitions |
| `openproject/ai/automation/test_update_wf05.py` | Test / Verification | 30 | `1a99d67d4845` | Script tự động hóa & container definitions |
| `openproject/ai/automation/wbs_application_qualification.py` | Implementation | 228 | `6d6031e99db5` | Script tự động hóa & container definitions |
| `openproject/ai/automation/weekly_summary_qualification.py` | Implementation | 243 | `055d89fbe7a4` | Script tự động hóa & container definitions |
| `openproject/ai/automation/Backup.Dockerfile` | Build / Deployment | 8 | `c017973487d9` | Script tự động hóa & container definitions |
| `openproject/ai/automation/DailyCore.Dockerfile` | Build / Deployment | 11 | `5912f1a12ff3` | Script tự động hóa & container definitions |
| `openproject/ai/automation/EngineeringCore.Dockerfile` | Build / Deployment | 6 | `2bda020ba2c4` | Script tự động hóa & container definitions |
| `openproject/ai/automation/EngineeringGateway.Dockerfile` | Build / Deployment | 26 | `27e6d9e9720d` | Script tự động hóa & container definitions |
| `openproject/ai/automation/ExecutionMonitorCore.Dockerfile` | Build / Deployment | 6 | `015fe137abf1` | Script tự động hóa & container definitions |
| `openproject/ai/automation/FreeOnly.Dockerfile` | Build / Deployment | 5 | `c4571e216948` | Script tự động hóa & container definitions |
| `openproject/ai/automation/QuickTunnel.Dockerfile` | Build / Deployment | 22 | `d418df0cabcb` | Script tự động hóa & container definitions |
| `openproject/ai/automation/RemainingGateway.Dockerfile` | Build / Deployment | 6 | `191bd787431a` | Script tự động hóa & container definitions |
| `openproject/ai/automation/Quick.Caddyfile` | Build / Deployment | 14 | `c79386c44595` | Script tự động hóa & container definitions |
| `openproject/ai/automation/Radmin.Caddyfile` | Build / Deployment | 25 | `386352d24167` | Script tự động hóa & container definitions |
| `openproject/ai/automation/quick_tunnel_supervisor.sh` | Implementation | 56 | `fb409569f1af` | Script tự động hóa & container definitions |

---

## 5. CHI TIẾT PHÂN HỆ TOOLS & VERIFICATION SUITES (`tools/`)

| File Path | Category | Lines | SHA256 (12 chars) | Mục đích / Chức năng |
| :--- | :--- | :--- | :--- | :--- |
| `tools/apply_defect04_patches.py` | Implementation | 66 | `f6ad1c28469a` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/apply_defect06_07_patches.py` | Implementation | 351 | `153894680085` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/apply_epic_return_reason_2026_10_13.py` | Implementation | 8 | `7f178b8ca101` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/apply_subtask_history_2026_10_13.py` | Implementation | 18 | `41f62a89548e` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/apply_subtask_qa_freshness_2026_10_13.py` | Implementation | 14 | `af65ac037160` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/audit_project5_invariants.py` | Implementation | 54 | `4e418c8d17a8` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_and_deploy_r17.py` | Build / Deployment | 44 | `5848ed4f5d34` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_and_deploy_r18.py` | Build / Deployment | 44 | `c274613f5e95` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_and_deploy_r19.py` | Build / Deployment | 51 | `468f020b974d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_command_center_view.py` | Implementation | 2337 | `d7653cd38211` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_done_epic_review.py` | Implementation | 167 | `0c70580dd328` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_jira_handbook_2026_10_13.py` | Implementation | 638 | `705726077141` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_jira_learning_guide.py` | Implementation | 484 | `9df6140fb6b3` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/build_workflow_brief.py` | Implementation | 165 | `d3a11cf9a08d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/check_active_queue.py` | Test / Verification | 9 | `9196203915cc` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/check_project5_deep.py` | Test / Verification | 59 | `b796fcbebf4f` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/check_rails_runner.py` | Test / Verification | 16 | `f9b030b229b0` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/clean_test_run.py` | Test / Verification | 16 | `7ad4c8c1592b` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/compare_source_runtime.py` | Implementation | 59 | `7496e7c83e5f` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/deploy_r16.py` | Build / Deployment | 10 | `00733c25e8da` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/diagnose_epic_acceptance.py` | Test / Verification | 35 | `ec7dcc7961ce` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/diagnose_qa_current.py` | Test / Verification | 24 | `4edbe286a3d7` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/diagnose_qa_newest.py` | Test / Verification | 34 | `cabeee1a0224` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/diagnose_subtask_cost.py` | Test / Verification | 90 | `a43514a7018f` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/execute_milestone2_auto_e2e.py` | Implementation | 418 | `e6a575336db3` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/finish_run_clean.py` | Implementation | 146 | `e8f469447e6b` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/fix_state_checkpoint.py` | Implementation | 48 | `c18ba5a6092c` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/forensic_docker.py` | Implementation | 28 | `bc2ba6f758f5` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/generate_audit_m1.py` | Implementation | 377 | `29c095c77c81` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_control_state.py` | Test / Verification | 19 | `0824fc2ea2cf` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_db_tables.py` | Test / Verification | 14 | `91f09d9f6c6d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_engineering_plans.py` | Test / Verification | 15 | `980771d81542` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_gateway_backlog.py` | Test / Verification | 27 | `1ab76afe6630` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_openclaw_queue.py` | Test / Verification | 12 | `fe52e86a203d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_project6_wps.py` | Test / Verification | 18 | `d783d065c178` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_schema.py` | Contract / Interface | 12 | `3b4cee24a34a` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_sqlite.py` | Test / Verification | 26 | `ab927f8b037e` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_unit_definitions.py` | Test / Verification | 15 | `b4634152b9ee` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_wf04.py` | Test / Verification | 23 | `0a8785975dad` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_wf04_executions.py` | Test / Verification | 16 | `db9b140c2aef` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inspect_wp_priority.py` | Test / Verification | 16 | `42e3820f82f1` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/jira_admin_mcp.py` | Implementation | 1315 | `376000e6712c` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/jira_bot.py` | Implementation | 185 | `663cbc2e76ad` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/jira_gemini.py` | Implementation | 131 | `672bb065c78d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/jira_mcp.py` | Implementation | 112 | `977954d51d47` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/jira_monitor.py` | Implementation | 179 | `96ff90cf26c2` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/patch_controller_and_view.py` | Implementation | 498 | `71cd876635c1` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/patch_engineering_reporting_scheduler.py` | Implementation | 335 | `605bfe832e42` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/patch_engineering_view_schedule.py` | Implementation | 189 | `de2d24fcd118` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/patch_qldapm_ai_controller_schedule.py` | Implementation | 22 | `d8f34aafd4f2` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/patch_service_scheduler_tick.py` | Implementation | 39 | `033a65adc225` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/playwright_full_command_center_uat.py` | Test / Verification | 271 | `3aa0a838b2ee` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/preview_epic_return_reason.py` | Implementation | 7 | `970ac42ebb09` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/preview_qa_freshness.py` | Implementation | 7 | `da33e8e56e3b` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/preview_subtask_history.py` | Implementation | 5 | `df0ae945e9af` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/preview_subtask_qa_freshness.py` | Implementation | 4 | `72d0489aaeba` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/publish_health_check_commit.py` | Test / Verification | 123 | `ee75f2243612` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/reconcile_and_finish_run.py` | Implementation | 160 | `2edd422f5fec` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/reproduce_phase292_baseline.py` | Implementation | 129 | `0d45a9d5679d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/snapshot_automation_rollout.py` | Implementation | 19 | `04540d16fd3b` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_cancel_debug.py` | Test / Verification | 44 | `81d1f228fda7` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_create_wp_manual.py` | Test / Verification | 35 | `5888ab8e11e2` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_github_sync_5prs.py` | Test / Verification | 21 | `3d2963ea79e5` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_http_session.py` | Test / Verification | 24 | `bf51ca2a581c` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_live_http.py` | Test / Verification | 62 | `443ae06c6571` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_menu_items.py` | Test / Verification | 25 | `30d17bdc45df` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_owner_cross_actor_control.py` | Test / Verification | 68 | `e71394047e12` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_owner_full_capabilities.py` | Test / Verification | 132 | `942eca5632a0` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_owner_ui_playwright.py` | Test / Verification | 122 | `e0310054efe3` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_reporting_scheduler_live.py` | Test / Verification | 216 | `2d51036b378c` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_automation_qualification.py` | Test / Verification | 52 | `e072f52fae41` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_automation_rollout.py` | Test / Verification | 25 | `fb44dc3630f5` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_defect05_auto_mode.py` | Test / Verification | 72 | `28dc36860404` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_defect08_skills.py` | Test / Verification | 83 | `6cf643809874` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_defect12_m6.py` | Test / Verification | 69 | `00cbe862dba5` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_phase27_remediations.py` | Test / Verification | 284 | `85b3605694c1` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_phase292_full.py` | Test / Verification | 317 | `bce1dc962656` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_project5_invariants.py` | Test / Verification | 111 | `c8c0479dcdf9` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_qa_provenance.py` | Test / Verification | 28 | `0d0ea3fff54e` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_subtask_checklist_candidate.py` | Test / Verification | 37 | `0582b4a0811c` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_subtask_history_candidate.py` | Test / Verification | 22 | `49c13340396d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/verify_subtask_split_candidate.py` | Test / Verification | 37 | `83cb9ea18bba` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/check_pass.rb` | Test / Verification | 20 | `5e0a3c8cfd6e` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/generate_owner_cookie.rb` | Implementation | 29 | `2ec354a51d53` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/generate_owner_cookie2.rb` | Implementation | 13 | `e8ed1e45bcdc` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/inject_owner_session.rb` | Implementation | 20 | `695065b119e9` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/list_routes.rb` | Implementation | 3 | `239a67e7f37e` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_app_session.rb` | Test / Verification | 13 | `7695dcfe2b1d` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/test_app_session2.rb` | Test / Verification | 17 | `e24251c7c179` | Công cụ kiểm toán / Playwright / Invariant checker |
| `tools/update_s184.rb` | Implementation | 12 | `0e3ee4ce1825` | Công cụ kiểm toán / Playwright / Invariant checker |

---

## 6. RÀ SOÁT DEAD CODE & LEGACY ARTIFACTS

1. **Dead Code Check:**
   - Không có code thừa gây conflict trong `openproject/ai/gateway/` và `openproject/ai/core/overlay/`. Mọi route và action trong `qldapm_ai_controller.rb` đều map trực tiếp vào UI tabs và endpoints.
   - Các files có tiền tố `quick.stage.yml.bak`, `~$...docx` là file tạm/backup của hệ thống văn bản, không được import vào bất kỳ container runtime nào.
2. **Contract Preservation:**
   - Tất cả Pydantic models trong `agent_models.py` và `store.py` đều tuân thủ `extra="forbid"`, ngăn chặn triệt để silent field drift hoặc schema pollution.
