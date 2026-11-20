# BÁO CÁO AUDIT ĐỐI SOÁT HỆ THỐNG — PHASE 2.6 M0 BASELINE AUDIT
**Thời điểm thực hiện:** 2026-10-30T16:15:00+07:00  
**Người thực hiện:** Gemini (Principal Software Architect & Reliability Engineer)  
**Mục tiêu:** Xác minh tính toàn vẹn hệ thống, đối soát mâu thuẫn số lượng kiểm thử, kiểm tra trạng thái 7 dịch vụ, phân tích chuỗi GitHub PRs và chuẩn bị lộ trình Phase 2.6.

---

## 1. Trạng Thái Hoạt Động Của 7 Dịch Vụ Hệ Sinh Thái (Service Endpoints Health)

Toàn bộ 7 dịch vụ vật lý/container trong hệ thống đều đang hoạt động (ONLINE) và phản hồi mã HTTP hợp lệ:

| STT | Tên Dịch Vụ | URL Kiểm Tra | Trạng Thái HTTP | Ghi Chú |
|---|---|---|---|---|
| 1 | **OpenProject** | `http://127.0.0.1:18088/health_checks/default` | **200 OK** | Container `qldapm-openproject-web-1`, image `qldapm-core:engineering-continuation-r14-20261030` |
| 2 | **QLDAPM AI Gateway** | `http://127.0.0.1:18089/health` | **200 OK** | Container `qldapm-ai-gateway-1`, image `qldapm-ai:engineering-continuation-r14-20261030` |
| 3 | **n8n Workflow Engine** | `http://127.0.0.1:5679/healthz` | **200 OK** | 16/16 workflows active và published |
| 4 | **Qdrant Vector DB** | `http://127.0.0.1:6333/healthz` | **200 OK** | Second Brain vector store, indexed 5 WPs (#379–#383) |
| 5 | **Ollama Daemon** | `http://127.0.0.1:11434/api/version` | **200 OK** | Model `bge-m3:latest` phục vụ hybrid embeddings |
| 6 | **OpenClaw Gateway** | `http://127.0.0.1:18789/health` | **200 OK** | WSL2 Ubuntu 24.04 (`OpenClawGateway`), Node 24.22.2 |
| 7 | **Mini Task Manager (Demo)** | `http://127.0.0.1:18791/` và `/tasks` | **200 OK** | Serving release `def9d0a8...` (Lưu ý: đường dẫn `/health` không được định nghĩa, ứng dụng phục vụ trực tiếp tại root `/` và `/tasks`) |

---

## 2. Giải Trình Tuyệt Đối Về Mâu Thuẫn Số Lượng Kiểm Thử (Test Count Reconciliation)

### 2.1. Nguồn gốc của sự chênh lệch (30 vs 37 vs 51 tests)
Trong tài liệu và báo cáo bàn giao trước đây có sự khác biệt giữa các con số **30**, **37** và **51**. Qua quá trình phát hiện kiểm thử (test discovery) và chạy thực tế chi tiết, nguồn gốc con số đã được làm sáng tỏ hoàn toàn:

1. **Bộ kiểm thử Engineering Core nguyên bản gồm 2 files:**
   - `openproject/ai/tests/test_engineering.py`: **16 test methods**
   - `openproject/ai/tests/test_engineering_continuation.py`: **14 test methods**
   - **Tổng cộng Core:** 16 + 14 = **30 tests** (Đây chính là con số 30 tests được báo cáo ban đầu).
2. **Các module kiểm thử mở rộng được bổ sung ở các Milestones:**
   - `openproject/ai/tests/test_engineering_state_sync.py`: **7 test methods** (Milestone 2)
   - `openproject/ai/tests/test_engineering_github_sync.py`: **6 test methods** (Milestone 3)
   - `openproject/ai/tests/test_engineering_auto_mode.py`: **8 test methods** (Milestone 6)
3. **Khi tác giả chạy lệnh trong Phase 2.5:**
   ```bash
   python -m unittest openproject/ai/tests/test_engineering.py openproject/ai/tests/test_engineering_state_sync.py openproject/ai/tests/test_engineering_github_sync.py openproject/ai/tests/test_engineering_auto_mode.py
   ```
   Lệnh trên chỉ truyền 4 file (bỏ quên `test_engineering_continuation.py`), dẫn đến:
   - 16 + 7 + 6 + 8 = **37 tests** được runner thực thi và báo cáo là `37/37 PASS`.
4. **Tổng số thực tế đầy đủ của toàn bộ 5 files Engineering:**
   - 16 + 14 + 7 + 6 + 8 = **51 tests**!

### 2.2. Kết quả thực thi thực tế toàn bộ 51 tests (Verifiable Evidence)
- **Lệnh thực thi:**
  ```python
  python -c "import unittest, os, sys; sys.path.insert(0, os.path.abspath('openproject/ai')); ..."
  ```
- **Số lượng tests phát hiện (Discovered):** 51
- **Số lượng tests thực thi (Executed):** 51
- **Passed:** **51 / 51** (100%)
- **Failed:** 0
- **Errors:** 0
- **Skipped:** 0
- **Thời gian chạy (Duration):** 28.38 giây
- **Chi tiết danh sách 51 test methods:**
  - `EngineeringTests` (16):
    - `test_cancel_before_claim_can_reactivate_but_started_job_cannot_and_pause_survives_finish`
    - `test_finished_lease_recovery_cannot_leave_mode_running_forever`
    - `test_finished_or_unclaimed_run_cannot_accept_late_success`
    - `test_owner_authorized_in_project6_and_shares_history_with_pm20_without_duplication`
    - `test_pause_prevents_claim_and_incomplete_proof_cannot_complete`
    - `test_project6_native_artifact_links_index_as_opaque_references_without_weakening_main_classifier`
    - `test_project_scope_policy_is_opt_in_and_never_falls_back_to_main`
    - `test_project_specific_role_does_not_change_main_and_scope_cannot_enable_generic_writes`
    - `test_reconciled_terminal_failure_resumes_same_unit_with_bounded_repairs_and_unknown_cannot_replay`
    - `test_rest_trace_used_by_wf04_resolves_owned_project6_and_rechecks_membership`
    - `test_rpm_recovery_preserves_actual_rework_feedback_and_same_unit`
    - `test_second_unit_requires_verified_first_head_and_legacy_wait_does_not_rewrite_engineering_queue`
    - `test_signed_bridge_requires_opt_in_correct_project_actor_and_single_use_nonce`
    - `test_source_stale_non_pm_other_project_and_wrong_unit_are_denied`
    - `test_two_sources_claim_one_unit_and_legacy_worker_cannot_execute_it`
    - `test_usage_ids_are_session_scoped_so_rework_does_not_overwrite_previous_attempt`
  - `ContinuationTests` (14):
    - `test_cancel_is_distinct_and_resume_preserves_same_unit_and_completed_stage`
    - `test_delivery_journal_skips_completed_steps_after_host_restart`
    - `test_engineering_projection_uses_actual_role_receipts_in_existing_monitor_schema`
    - `test_incomplete_planning_handoff_cannot_dispatch_defined_feedback_unit`
    - `test_knowledge_retry_never_replays_unknown_outcome`
    - `test_native_recovery_preserves_rejected_receipt_and_reuses_known_success`
    - `test_new_feedback_uses_latest_verified_delivery_and_blocks_parallel_stale_work`
    - `test_own_published_version_can_resume_but_later_external_edit_cannot`
    - `test_plan_cannot_invent_units_or_cyclic_dependencies`
    - `test_planning_feedback_deduplicates_on_requirement_and_is_queued_without_model_call`
    - `test_recovered_finish_keeps_both_failure_and_success_events`
    - `test_resume_denies_unknown_checkpoint_changed_revision_and_pending_native_writes`
    - `test_role_bootstrap_evidence_rejects_advertised_but_unloaded_persona`
    - `test_worker_heartbeat_is_durable_without_admission_or_model_call`
  - `EngineeringStateSyncTests` (7):
    - `test_find_transition_path`
    - `test_map_engineering_to_op`
    - `test_reconcile_engineering_project_updates_children_and_parent`
    - `test_state_groups_definitions_and_ssot`
    - `test_transition_work_package_safely_no_op_when_already_target`
    - `test_transition_work_package_safely_rejects_lock_version_mismatch`
    - `test_transition_work_package_safely_step_by_step_and_comment`
  - `EngineeringGitHubSyncTests` (6):
    - `test_fetch_pull_requests_parses_response`
    - `test_get_github_token_from_config_file`
    - `test_get_github_token_from_credential_helper`
    - `test_get_github_token_from_env`
    - `test_reconcile_github_with_openproject_network_error_handled_gracefully`
    - `test_reconcile_github_with_openproject_success_and_idempotency`
  - `TestEngineeringAutoMode` (8):
    - `test_auto_mode_concurrency_lock`
    - `test_auto_mode_schedules_ready_unit`
    - `test_auto_mode_shutoff_on_failure`
    - `test_auto_mode_shutoff_on_quota_unavailable`
    - `test_auto_mode_shutoff_when_all_delivered`
    - `test_control_auto_mode_accepted_for_pm_and_owner`
    - `test_control_invalid_mode_rejected`
    - `test_control_unauthorized_rejected`

---

## 3. Đối Soát Toàn Diện Chuỗi GitHub Pull Requests (Stacked PR Chain)

Kiểm tra trực tiếp qua GitHub CLI (`gh pr view`):

| PR # | Base Branch | Head Branch | Trạng Thái | Mergeable | MergeStateStatus | Ghi Chú Kỹ Thuật |
|---|---|---|---|---|---|---|
| **#1** | `main` | `codex/openclaw-create-list-persistence-v1` | **OPEN** | **MERGEABLE** | **CLEAN** | Gốc của PR chain. Đã sẵn sàng merge vào `main` khi UAT hoàn tất. |
| **#2** | `codex/openclaw-create-list-persistence-v1` | `codex/openclaw-crud-search-web-v1` | **MERGED** | N/A | N/A | **Đã merge vào branch feature #1**, CHƯA merge vào `main`. Head commit đã tích hợp vào branch #1. |
| **#3** | `codex/openclaw-crud-search-web-v1` | `codex/openclaw-feedback-283138e910432528` | **OPEN** | **MERGEABLE** | **CLEAN** | Stacked trên branch của PR #2. |
| **#4** | `codex/openclaw-feedback-283138e910432528` | `codex/openclaw-feedback-4d13e695555a8d44` | **OPEN** | **MERGEABLE** | **CLEAN** | Stacked trên branch của PR #3. Chứa commit đầu mới nhất `def9d0a8...` đang được phục vụ tại Mini Task Manager. |

**Nhận định kiến trúc:**
- Cả 3 PR đang mở (#1, #3, #4) đều ở trạng thái `MERGEABLE` và `CLEAN` (không có merge conflict).
- Không được tự động merge bất kỳ PR nào mà không có phê duyệt UAT của người dùng.
- Khi PR #1 được merge vào `main`, các branch base của PR #3 và #4 cần được rebase hoặc merge theo thứ tự chuỗi.

---

## 4. Đối Soát Trạng Thái Git & Docker Runtime

1. **Git Repository QLDAPM:**
   - Branch: `codex/local-multi-agent-upgrade`
   - Head commit: `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`
   - Tracked files: Hoàn toàn sạch (`clean`).
   - Untracked files: Được bảo toàn nguyên vẹn (theo nguyên tắc không xóa tệp dự án).
2. **Docker Containers Deployed:**
   - `qldapm-openproject-web-1`: Image `qldapm-core:engineering-continuation-r14-20261030` (`sha256:9edbaac624c8778bb733725051bf49fb57e71feca4a90fab13da0c3c7ef619ec`), status `healthy`.
   - `qldapm-ai-gateway-1`: Image `qldapm-ai:engineering-continuation-r14-20261030` (`sha256:aed8a6a605c5d473678aa537b548d3449a7076a14ea132d59d6772f2908618e3`), status `healthy`.
3. **Quyền Owner (User 18) vs PM (User 20):**
   - User 18 (Owner): Nhận diện đúng vai trò `AI_SYSTEM_OWNER`, có capability `['AI_SYSTEM_OWNER']`, toàn quyền kiểm soát và điều hành Project 6.
   - User 20 (PM): Nhận diện đúng vai trò `PM`.
   - User 19 (Non-member): Bị từ chối an toàn với mã `403` / `IDENTITY_MISMATCH_OR_ADMIN_TOKEN`.
   - Project 5: Bảo toàn tuyệt đối 341 Work Packages, 0 lượt ghi trái phép.

---

## 5. Kết Luận Giai Đoạn M0 Baseline Audit
Hệ thống QLDAPM MAIN hiện tại đạt trạng thái ổn định vững chắc, không có lỗi tiềm ẩn che giấu, mâu thuẫn số lượng kiểm thử đã được giải quyết minh bạch và toàn diện với bằng chứng thực tế 51/51 tests PASS. Sẵn sàng bước vào **Stage 1 (M1 Owner Capability Matrix & Authority)** và **Stage 2 (M2/M3 Deep Research Upstream)**.
