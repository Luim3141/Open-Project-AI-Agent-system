"""Prepare only the additive Approve4 history companion; no apply or deploy."""
import json
import jira_admin_mcp as admin
result = admin.preview_subtask_history()
print(json.dumps({key: result[key] for key in ('previewId', 'createdAtEpoch', 'fingerprint', 'diff', 'blockers', 'validation', 'rollback')}))
