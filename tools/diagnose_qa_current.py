"""Read-only evaluation of the fixed QAG3-332 QA qualification fixture."""
import json
import jira_admin_mcp as admin

admin.preflight()
_, expressions = admin.pinned_expressions()
expression = dict(expressions)["qag3-qa-current"]
candidate = expression.replace("let history = originalIssue.changelogs;",
                               "let history = originalIssue.changelogs.slice(0, 2);")
for old, new in [("pass.author", "passAuthor"), ("issue.project", "project"),
                 ("originalIssue.parent", "oldParent"), ("issue.parent", "parent"),
                 ("originalIssue.assignee", "oldAssignee"), ("issue.assignee", "assignee"),
                 ("originalIssue.description", "oldDescription"), ("issue.description", "description")]:
    candidate = candidate.replace(old, new)
candidate = "let project = issue.project; let parent = issue.parent; let oldParent = originalIssue.parent; " + \
    "let assignee = issue.assignee; let oldAssignee = originalIssue.assignee; " + \
    "let description = issue.description; let oldDescription = originalIssue.description; " + candidate
candidate = candidate.replace("let newer =", "let passAuthor = pass == null ? null : pass.author; let newer =")
for label, candidate in [("cached-bounded2", candidate)]:
    response = admin.request("POST", "/expression/evaluate", body={"expression": candidate,
        "context": {"issue": {"key": "QAG3-332"}, "custom": {
            "originalIssue": {"type": "issue", "key": "QAG3-332"}}}}, expected=(200, 400))
    print(json.dumps({"case": label, "value": response.get("value"),
                      "errors": response.get("errorMessages")}))
