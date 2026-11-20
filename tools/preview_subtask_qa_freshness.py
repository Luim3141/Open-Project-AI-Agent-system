"""Prepare the fixed additive Subtask companion preview; never apply or deploy."""
import json
import jira_admin_mcp as admin
print(json.dumps(admin.preview_subtask_qa_freshness()))
