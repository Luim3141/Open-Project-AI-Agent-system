"""Host policy; model arguments and stored token role claims never grant authority."""

AI_SYSTEM_OWNER = "AI_SYSTEM_OWNER"
ROLES = {"PM", "BA", "BA-PM", "BE", "FE", "QA", AI_SYSTEM_OWNER}
OWNER_ONLY = {"delegated_control", "owner_inspect", "qa_application_proof_verify", "qa_application_proof_admit"}
QA_ONLY = {'qa_evidence_capture'}
QA_MANAGER_ONLY = {'qa_transition_prepare','phase_transition_prepare'}
PHASE_SOURCE = {'phase_draft','phase_get','phase_list'}
QA_RUN = {'qa_test_run', 'qa_test_get', 'qa_evidence_from_run', 'qa_evidence_list'}
PM_ONLY = {"delegated_status", "delegated_preview", "engineering_report_schedule_get", "engineering_report_schedule_update", "engineering_notifications_list", "engineering_notifications_dismiss", "engineering_report_generate", "engineering_report_list", "engineering_report_get", "engineering_github_sync", "engineering_plan", "engineering_cancel", "engineering_resume", "engineering_status", "engineering_run_once", "engineering_control", "delete_work_package", "update_dependency", "delete_dependency", "create_dependency", "create_work_package", "update_work_package", "transition", "change_gate", "propose_operation",
           "write_code", "request_test", "get_configuration", "knowledge_integrity", "knowledge_file_ingest", "knowledge_incremental_sync", "knowledge_feedback_apply", "bug_propose", "wbs_adopt", "wbs_next"}
NATIVE_PERMISSIONS = {"delete_work_package":"delete_work_packages", "update_dependency":"manage_work_package_relations", "delete_dependency":"manage_work_package_relations", "create_dependency": "manage_work_package_relations", "create_work_package": "add_work_packages", "update_work_package": "edit_work_packages",
    "transition": "edit_work_packages", "comment": "add_work_package_comments", "change_gate": "edit_work_packages"}
SANDBOX_ONLY = {"list_code", "read_code", "write_code", "request_test", "propose_operation"}


def business_manager(role):
    return role in {"PM", AI_SYSTEM_OWNER}


def allowed(role, action, mode=None):
    return (role in ROLES and (action not in OWNER_ONLY or role == AI_SYSTEM_OWNER)
            and (action not in QA_ONLY or role == 'QA')
            and (action not in QA_RUN or business_manager(role) or role == 'QA')
            and (action not in PHASE_SOURCE or business_manager(role) or role in {'BA','BA-PM'})
            and (business_manager(role) or action not in PM_ONLY | QA_MANAGER_ONLY)
            and not (mode == "native" and action in SANDBOX_ONLY))


def require(role, action, mode=None):
    if action in QA_ONLY and role != 'QA':
        raise PermissionError('QA_NATIVE_AUTHOR_REQUIRED')
    if not allowed(role, action):
        raise PermissionError(f"PM_REQUIRED: role {role or 'unknown'} không có quyền {action}; chỉ được đọc, phân tích và bình luận")
    if mode == "native" and action in SANDBOX_ONLY:
        raise PermissionError("NATIVE_BUSINESS_OPERATOR_TOOL_DENIED")
