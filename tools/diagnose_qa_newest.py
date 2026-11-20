"""Read-only candidate evaluation against the fixed QAG3-332 test fixture."""
import json
import re
from pathlib import Path
import jira_admin_mcp as admin

admin.preflight()
_, pinned = admin.pinned_expressions()
# Keep the failed combined-cost experiment reproducible after the deployed split fix.
baseline = Path(__file__).resolve().parents[1] / "forge/qag3-validator/manifest.before-qa-split-2026-10-12.yml"
matches = re.findall(r"    - key: ([a-z0-9-]+)\r?\n.*?      expression: >-\r?\n(.*?)      errorMessage:", baseline.read_text(encoding="utf-8"), re.S)
assert len(matches) == 10
source = " ".join(line.strip() for line in dict(matches)["qag3-qa-current"].splitlines())
start = source.index("let history =")
end = source.index("let lines =", start)
prefix = "let pass = originalIssue.getNewestChangelog('status', {from: '10018', to: '10012'}); "
prefix += "let lastStatus = originalIssue.getNewestChangelog('status'); "
prefix += "let edits = ['summary', 'description', 'parent', 'assignee', 'customfield_10045'].map(field => originalIssue.getNewestChangelog(field)); "
candidate = source[:start] + prefix + source[end:]
start = candidate.index("newer.every(")
candidate = candidate[:start] + "edits.every(change => change == null || change.id == pass.id || change.created < pass.created) && "
candidate += "lastStatus != null && (lastStatus.id == pass.id || (issue.issueType.id == 10011 && lastStatus.created > pass.created && lastStatus.items.some(item => item.fieldId == 'status' && item.from == '10012' && item.to == '10019')))"
declarations = candidate.rsplit('; ', 1)[0] + '; '
forced = declarations + "{sameParent: issue.parent == originalIssue.parent, sameAssignee: issue.assignee == originalIssue.assignee, sameEvidence: evidence == plain(originalIssue.customfield_10045), activeAuthor: pass != null && pass.author != null && pass.author.active, checklist: choices != null, project: issue.project.id == 10002, fresh: edits.every(change => change == null || change.id == pass.id || change.created < pass.created), status: lastStatus != null}"
freshness = dict(pinned)["qag3-qa-freshness"]
for label, expression in [("candidate", candidate), ("force-all-read-paths", forced), ("freshness-companion", freshness), ("latest-status-probe", "originalIssue.getNewestChangelog('status', {from: '10018', to: '10012'}) != null")]:
    response = admin.request("POST", "/expression/evaluate", body={"expression": expression,
        "context": {"issue": {"key": "QAG3-332"}, "custom": {
            "originalIssue": {"type": "issue", "key": "QAG3-332"}}}}, expected=(200, 400))
    print(json.dumps({"case": label, "value": response.get("value"),
                      "errors": response.get("errorMessages"), "meta": response.get("meta")}))
analysis = admin.request("POST", "/expression/analyse", params={"check": "type"}, body={
    "expressions": [candidate, freshness], "contextVariables": {"originalIssue": "Issue"}})
print(json.dumps({"case": "candidate-type", "results": analysis.get("results")}))
