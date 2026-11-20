"""Fixed additive Return7 preview only; no Jira writes or automation enable."""
import json
import jira_admin_mcp as admin

plan = admin.preview_epic_return_reason()
print(json.dumps({key: plan[key] for key in
                 ('previewId', 'fingerprint', 'diff', 'blockers', 'validation', 'rollback')}))
