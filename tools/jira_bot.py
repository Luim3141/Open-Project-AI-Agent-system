"""Read-only QAG3 collection through the existing official Atlassian MCP client."""

import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://luimjiraqldapm.atlassian.net"
CLOUD_ID = "560ef0cc-d24b-4613-98d3-d541afe8f32b"
ACCOUNT_ID = "712020:0d04982c-00bf-46af-b3a7-446d0f44edfb"
PROJECT = "QAG3"
PROJECT_ID = "10002"


def unwrap(value):
    for _ in range(8):
        if not isinstance(value, dict) or value.get("isError") or value.get("error"):
            raise ValueError("Invalid or failed MCP response")
        if "content" in value:
            texts = [x["text"] for x in value["content"] if x.get("type") == "text"]
            if len(texts) != 1:
                raise ValueError("Expected one MCP JSON text payload")
            value = json.JSONDecoder().raw_decode(texts[0].lstrip())[0]
        elif "data" in value:
            value = value["data"]
        else:
            return value
    raise ValueError("MCP response nesting exceeds limit")


def call_mcp(tool, arguments):
    if tool not in {"atlassianUserInfo", "getAccessibleAtlassianResources", "discover",
                    "executeRead", "searchJiraIssuesUsingJql"}:
        raise ValueError("Collector only permits read tools")
    if tool == "executeRead" and arguments.get("name") != "listJiraProjects":
        raise ValueError("Collector only permits project metadata execution")
    # The existing helper owns timeout/cleanup and uses Codex's credential store.
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "jira_mcp.py"), tool],
        input=json.dumps(arguments), capture_output=True, text=True, encoding="utf-8",
        cwd=ROOT, env={**{k: v for k, v in os.environ.items()
                         if k.upper() not in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}},
                       "PYTHONIOENCODING": "utf-8"},
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if result.returncode:
        raise RuntimeError(f"MCP client failed for {tool}; no snapshot is complete")
    return unwrap(json.loads(result.stdout))


def read_all_issues(call):
    issues, keys, tokens = [], set(), set()
    arguments = {
        "cloudId": CLOUD_ID, "jql": f"project = {PROJECT} ORDER BY key ASC",
        "fields": ["summary", "issuetype", "status", "assignee", "duedate",
                   "updated", "parent", "labels"],
        "view": "full", "maxResults": 100,
    }
    while True:
        page = call("searchJiraIssuesUsingJql", arguments.copy())
        if not isinstance(page.get("issues"), list) or type(page.get("isLast")) is not bool:
            raise ValueError("Missing issues or pagination completeness")
        for issue in page["issues"]:
            key = issue.get("key", "")
            if not re.fullmatch(r"QAG3-[1-9]\d*", key) or key in keys:
                raise ValueError("Foreign or duplicate work item in snapshot")
            keys.add(key)
            issues.append(issue)
        if page["isLast"]:
            return issues
        token = page.get("nextPageToken")
        if not isinstance(token, str) or not token or token in tokens:
            raise ValueError("Missing or repeated pagination token")
        tokens.add(token)
        arguments["nextPageToken"] = token


def summarize(issues, issue_types, today):
    types = {x["id"]: x for x in issue_types}
    normalized = []
    for issue in issues:
        fields = issue["fields"]
        work_type = fields["issuetype"]
        metadata = types[work_type["id"]]
        kind = "Subtask" if metadata["subtask"] else metadata["name"]
        if kind not in {"Epic", "Task", "Story", "Subtask"}:
            raise ValueError("Unclassified work item type")
        status = fields["status"]
        category = status["statusCategory"]["key"]
        if category not in {"new", "indeterminate", "done"}:
            raise ValueError("Unclassified status category")
        if "updated" not in fields or not isinstance(fields.get("labels"), list):
            raise ValueError("Full updated/labels fields required")
        updated = datetime.fromisoformat(fields["updated"])
        if updated.tzinfo is None:
            raise ValueError("Updated timestamp needs timezone")
        due = fields.get("duedate")
        if due is not None:
            date.fromisoformat(due)
        assignee = fields.get("assignee")
        if assignee is not None and not assignee.get("accountId"):
            raise ValueError("Assignee identity missing")
        normalized.append({
            "key": issue["key"], "summary": fields.get("summary"), "kind": kind,
            "typeId": work_type["id"], "statusId": status["id"],
            "status": status["name"], "category": category,
            "updated": fields["updated"], "labels": fields["labels"],
            "assigneeKnown": "assignee" in fields,
            "assigneeAccountId": assignee["accountId"] if assignee else None,
            "dueDateKnown": "duedate" in fields, "dueDate": due,
            "parentKnown": "parent" in fields,
            "parentKey": fields["parent"].get("key") if fields.get("parent") else None,
            "cancelled": status["name"].strip().upper() in {"CANCELLED", "CANCELED"},
        })
    normalized.sort(key=lambda x: int(x["key"].split("-")[1]))
    functional = [x for x in normalized if x["kind"] in {"Task", "Story"}]
    done = [x for x in functional if x["category"] == "done" and not x["cancelled"]]
    return {
        "issues": normalized,
        "countsByType": {k: sum(x["kind"] == k for x in normalized)
                         for k in ("Epic", "Task", "Story", "Subtask")},
        "countsByStatus": dict(Counter(x["status"] for x in functional)),
        "functionalTotal": len(functional), "functionalDone": len(done),
        "cancelledFunctional": sum(x["cancelled"] for x in functional),
        "completionPercent": round(100 * len(done) / len(functional), 2) if functional else None,
        "scopeState": "CURRENT_SCOPE" if functional else "NO_FUNCTIONAL_SCOPE",
        "functionalWip": [x["key"] for x in functional if x["category"] == "indeterminate"],
        "unassignedFunctional": [x["key"] for x in functional
                                 if x["assigneeKnown"] and x["assigneeAccountId"] is None],
        "unknownAssigneeField": [x["key"] for x in functional if not x["assigneeKnown"]],
        "overdueFunctional": [x["key"] for x in functional if x["category"] != "done"
                              and x["dueDate"] and date.fromisoformat(x["dueDate"]) < today],
        "unknownDueDateField": [x["key"] for x in functional if not x["dueDateKnown"]],
    }


def collect(call=call_mcp, now=None):
    identity = call("atlassianUserInfo", {})
    if identity.get("accountId") != ACCOUNT_ID:
        raise ValueError("Unexpected authenticated account")
    resources = call("getAccessibleAtlassianResources", {})
    if not any(x.get("cloudId") == CLOUD_ID and x.get("url") == SITE
               for x in resources.get("resources", [])):
        raise ValueError("Expected Jira site is not accessible")
    discovery = call("discover", {"query": "list Jira projects"})
    if not any(x.get("name") == "listJiraProjects" and x.get("executeTool") == "executeRead"
               for x in discovery.get("results", [])):
        raise ValueError("Project metadata operation is not available")
    projects = call("executeRead", {
        "name": "listJiraProjects", "cloudId": CLOUD_ID,
        "inputs": {"query": PROJECT, "expand": "issueTypes", "maxResults": 100},
    })
    matches = [x for x in projects.get("values", [])
               if x.get("key") == PROJECT and x.get("id") == PROJECT_ID]
    if projects.get("isLast") is not True or len(matches) != 1:
        raise ValueError("Project metadata incomplete or target changed")
    issues = read_all_issues(call)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Snapshot timestamp needs timezone")
    return {
        "schemaVersion": 1, "site": SITE, "cloudId": CLOUD_ID,
        "projectKey": PROJECT, "projectId": PROJECT_ID,
        "observedAtUtc": now.astimezone(timezone.utc).isoformat(),
        "route": "official_atlassian_mcp", "readComplete": True, "isLast": True,
        "execution": "collector_invocation_not_proof_of_scheduled_run",
        "scheduledExecutionVerified": False,
        **summarize(issues, matches[0]["issueTypes"], now.astimezone(timezone(timedelta(hours=7))).date()),
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(collect(), ensure_ascii=False))
    except Exception as error:
        # Do not echo credential-bearing subprocess/server errors into reports.
        print(json.dumps({"readComplete": False, "errorType": type(error).__name__,
                          "message": "Collector failed; preserve the last successful snapshot."}))
        sys.exit(1)
