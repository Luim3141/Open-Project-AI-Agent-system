"""Read-only fixed QAG3-332 Task provenance/freshness candidate checks."""
import json
import jira_admin_mcp as admin

admin.preflight()
fingerprint, expressions = admin.pinned_expressions()
workflow = admin.workflow("task")["workflows"][0]
for transition_id in ("13", "14"):
    transition = next(t for t in workflow["transitions"] if t["id"] == transition_id)
    for key in ("qag3-qa-current", "qag3-qa-freshness"):
        assert any(v.get("parameters", {}).get("key") == admin.FORGE_EXTENSION + key and
                   v["parameters"].get("disabled") == "false" for v in transition["validators"]), key
source = dict(expressions)["qag3-qa-current"]
declarations = source.rsplit("; ", 1)[0] + "; "
forced = declarations + "{sameParent: parent == null ? originalParent == null : originalParent != null && parent.id == originalParent.id, sameAssignee: assignee == null ? originalAssignee == null : originalAssignee != null && assignee.accountId == originalAssignee.accountId, sameDescription: (description == null ? null : description.plainText) == (originalDescription == null ? null : originalDescription.plainText), sameSummary: issue.summary == originalIssue.summary, sameEvidence: evidence == previous, activeAuthor: author != null && author.active, signedMatch: pass != null && pass.items.some(item => item.fieldId == 'customfield_10045' && item.fromString != item.toString && item.toString == evidence), lineCount: lines.length, structured: ['Revision:', 'Environment:', 'Test scope:', 'Result:', 'Evidence:', 'Retest:', 'Bug references / retest rationale:'].every(prefix => value(prefix).length == 1 && value(prefix)[0].length > 0), checklist: checked('10022') && checked('10023') != checked('10024'), project: project.id == 10002 && project.key == 'QAG3'}"
forced = forced.replace("pass != null && pass.items.some", "signature != null && pass != null && signature.id == pass.id && signature.items.some")
cases = [("provenance", source), ("force-all-paths", forced),
         ("freshness", dict(expressions)["qag3-qa-freshness"]),
         ("signed-item-shape", declarations + "{passId: pass == null ? null : pass.id, signatureId: signature == null ? null : signature.id, items: signature == null ? [] : signature.items.map(item => ({fieldId: item.fieldId, toLength: item.toString == null ? null : item.toString.length, evidenceLength: evidence == null ? null : evidence.length, exact: item.toString == evidence, trimmed: item.toString == null ? false : item.toString.trim() == evidence.trim()}))}" )]
print(json.dumps({"sourceSha256": fingerprint, "workflowVersion": workflow.get("version")}))
for label, expression in cases:
    response = admin.request("POST", "/expression/evaluate", body={"expression": expression,
        "context": {"issue": {"key": "QAG3-332"}, "custom": {
            "originalIssue": {"type": "issue", "key": "QAG3-332"}}}}, expected=(200, 400))
    print(json.dumps({"case": label, "value": response.get("value"),
                      "errors": response.get("errorMessages"), "meta": response.get("meta")}))
validation = admin.inspect_expression_validation()
print(json.dumps({"allValid": validation["allValid"], "results": validation["results"]}))
