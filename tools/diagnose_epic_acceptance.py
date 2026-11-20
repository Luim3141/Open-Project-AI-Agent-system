"""Read-only diagnosis of the fixed QAG3-1 pending academic acceptance."""
import json
import jira_admin_mcp as admin

admin.preflight()
_, expressions = admin.pinned_expressions()
expression = dict(expressions)["qag3-epic-acceptance"]
lines = ["Scope version: SIMULATION-timeline-2026-10-12-QAG3-1",
         "Scope tasks: QAG3-2,QAG3-8,QAG3-14,QAG3-20,QAG3-26",
         "Integration result: PASS", "Handover result: COMPLETE",
         "Evidence: SIMULATION ONLY - no real QA or delivery asserted.",
         "Retest: NOT REQUIRED", "Bug references / retest rationale: Academic simulation only."]
evidence = {"type": "doc", "version": 1, "content": [
    {"type": "paragraph", "content": [{"type": "text", "text": r"\n".join(lines)}]}]}
expression = expression.replace("issue.customfield_10045", "pendingEvidence").replace(
    "issue.customfield_10044", "pendingChoices")
declarations, _, final = expression.rpartition("; ")
diagnostic = declarations + "; {allowed: (" + final + "), lines: lines, scope: scope}"
response = admin.request("POST", "/expression/evaluate", body={"expression": diagnostic,
    "context": {"issue": {"key": "QAG3-1"}, "custom": {
        "originalIssue": {"type": "issue", "key": "QAG3-1"},
        "pendingEvidence": {"type": "json", "value": evidence},
        "pendingChoices": {"type": "json", "value": [{"id": str(i)} for i in
            [10020, 10022, 10024, 10025, 10026, 10027]]}}}}, expected=(200, 400))
print(json.dumps({"allowed": response.get("value", {}).get("allowed"),
                  "lines": response.get("value", {}).get("lines"),
                  "scope": response.get("value", {}).get("scope"), "errorMessages": response.get("errorMessages"),
                  "errors": response.get("errors")}))
print(json.dumps(admin.request("POST", "/expression/analyse", params={"check": "complexity"},
    body={"expressions": [dict(expressions)["qag3-epic-acceptance"]],
          "contextVariables": {"originalIssue": "Issue"}})))
children_result = admin.request("POST", "/expression/evaluate", body={
    "expression": dict(expressions)["qag3-epic-children-done"],
    "context": {"issue": {"key": "QAG3-1"}}}, expected=(200, 400))
print(json.dumps({"childrenGate": children_result}))
