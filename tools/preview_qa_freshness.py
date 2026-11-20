"""Fixed active-QAG3 Task additive preview only; never apply a change."""
import json
import jira_admin_mcp as admin

plan = admin.preview_task_qa_freshness()
print(json.dumps({key: plan[key] for key in
    ('previewId', 'fingerprint', 'diff', 'blockers', 'validation', 'rollback')}))
