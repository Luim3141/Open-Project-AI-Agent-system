"""Operator-only, one-way QAG3 import. No Jira writes and no workflow bypass."""
import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

CLOUD_ID = "560ef0cc-d24b-4613-98d3-d541afe8f32b"
SITE = "https://luimjiraqldapm.atlassian.net"
FIELDS = ["summary", "description", "status", "issuetype", "parent", "assignee", "priority",
          "labels", "updated", "duedate", "customfield_10015", "project",
          "attachment", "comment", "worklog", "issuelinks", "timetracking"]


def source_id(issue):
    labels = issue["fields"].get("labels", [])
    values = [label[7:] for label in labels if label.startswith("source-")]
    if len(values) != 1 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,100}", values[0]):
        raise ValueError("EXACTLY_ONE_SOURCE_ID_REQUIRED")
    return values[0]


def inert_text(value):
    if isinstance(value, dict):
        if "text" in value:
            return inert_text(value["text"])
        content = "\n".join(inert_text(row) for row in value.get("content", []))
        return content or inert_text(value.get("attrs", {}).get("text", ""))
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > 250000:
        raise ValueError("SOURCE_TEXT_INVALID_OR_TOO_LARGE")
    value = re.sub(r"\]\(\s*(?:javascript|vbscript|data):[^)]*\)", "](blocked-source-link)", value, flags=re.I)
    return html.escape(value, quote=False)


def plan_item(issue, item, index, users, parents=None, local_description=None, dependent_ids=None):
    fields, links = issue["fields"], item["_links"]
    source = source_id(issue)
    kind = {"Sub-task": "Subtask", "Task": "Task", "Epic": "Epic"}.get(fields["issuetype"]["name"])
    if not kind or links["type"]["title"] != kind:
        raise ValueError("SOURCE_TYPE_MISMATCH_REVIEW_REQUIRED")
    payload, skipped = {}, []
    if "summary" in fields and fields["summary"] != item["subject"]:
        if not isinstance(fields["summary"], str) or not 1 <= len(fields["summary"]) <= 255:
            raise ValueError("SOURCE_SUBJECT_INVALID")
        payload["subject"] = fields["summary"]
    status = fields["status"]["name"].upper()
    if "description" in fields:
        old = item.get("description", {}).get("raw", "") if local_description is None else local_description
        simulation = "qag3-simulation" in fields.get("labels", [])
        warning = ("> JIRA IMPORT — SIMULATION ONLY. Không phải sản phẩm, kiểm thử hoặc hiệu suất thực.\n\n"
                   if simulation else "> JIRA IMPORT — DATA ONLY. Không phải xác nhận gate OpenProject.\n\n")
        description = warning + inert_text(fields["description"]) + "\n\n## Nguồn Jira\n\n" + (
            f"- Ticket: {SITE}/browse/{issue['key']}\n- Source ID: {source}\n"
            f"- Trạng thái Jira: {status}; không phải xác nhận gate OpenProject.\n"
            f"- Ưu tiên Jira: {inert_text(fields.get('priority', {}).get('name', 'unknown'))}\n"
            f"- Nhãn Jira: {inert_text(', '.join(fields.get('labels', [])))}\n"
            f"- Start Jira: {inert_text(str(fields.get('customFields', {}).get('Start date', {}).get('value', 'unknown')))}\n"
            f"- Due Jira: {inert_text(str(fields.get('duedate', 'unknown')))}\n"
            f"- Cập nhật nguồn: {inert_text(fields.get('updated', 'unknown'))}\n")
        description += "\n## OpenProject local — preserved\n\n" + old
        if description != item.get("description", {}).get("raw", ""):
            payload["description"] = {"format": "markdown", "raw": description}
    if "assignee" in fields:
        actor = fields["assignee"]
        if actor and actor.get("accountId") not in users:
            skipped.append("ASSIGNEE_NOT_MAPPED")
        else:
            href = f"/api/v3/users/{users[actor['accountId']]}" if actor else None
            if href != links.get("assignee", {}).get("href"):
                payload.setdefault("_links", {})["assignee"] = {"href": href}
    if "parent" in fields:
        parent = fields["parent"]
        parent_source = (parents or {}).get(parent["key"]) if parent else None
        if parent and (parent_source is None or parent_source not in index):
            skipped.append("PARENT_NOT_MAPPED")
        else:
            href = f"/api/v3/work_packages/{index[parent_source]['id']}" if parent else None
            if href != links.get("parent", {}).get("href"):
                payload.setdefault("_links", {})["parent"] = {"href": href}
    if "duedate" in fields and fields["duedate"] != item.get("dueDate"):
        payload["dueDate"] = fields["duedate"]
    start = fields.get("customFields", {}).get("Start date")
    if start is not None and start.get("value") != item.get("startDate"):
        payload["startDate"] = start["value"]
    for name in ("startDate", "dueDate"):
        if payload.get(name) is not None:
            from datetime import date
            date.fromisoformat(payload[name])
    if item.get('scheduleManually') is False and item['_links'].get('children') and any(name in payload for name in ('startDate', 'dueDate')):
        # Preserve local automatic roll-up; switching date mode is not a Jira field sync.
        skipped.append('NATIVE_AUTOMATIC_PARENT_DATES_NOT_DIRECTLY_WRITABLE')
        payload.pop('startDate', None)
        payload.pop('dueDate', None)
    if item['id'] in (dependent_ids or set()) and any(name in payload for name in ('startDate', 'dueDate')):
        # Changing even a manual predecessor reschedules automatic successors.
        skipped.append('NATIVE_DEPENDENCY_SCHEDULE_DATES_RETAINED')
        payload.pop('startDate', None)
        payload.pop('dueDate', None)
    return {"source_id": source, "jira_key": issue["key"], "id": item["id"], "version": item["lockVersion"],
            "payload": payload, "source_status": status, "skipped": skipped, "local_description":
            item.get("description", {}).get("raw", "") if local_description is None else local_description}


def read_issue_pages(call):
    arguments = {"cloudId": CLOUD_ID, "jql": "project = QAG3 AND labels = qag3-wbs ORDER BY key ASC",
                 "maxResults": 100, "view": "full", "fields": FIELDS, "responseContentFormat": "markdown"}
    issues, keys, sources, tokens = [], set(), set(), set()
    for _ in range(1000):
        page = call("searchJiraIssuesUsingJql", dict(arguments))
        if type(page.get("isLast")) is not bool or not isinstance(page.get("issues"), list):
            raise ValueError("INCOMPLETE_JIRA_PAGINATION")
        for issue in page["issues"]:
            key, source = issue.get("key", ""), source_id(issue)
            if not re.fullmatch(r"QAG3-[1-9]\d*", key) or key in keys or source in sources:
                raise ValueError("FOREIGN_OR_DUPLICATE_JIRA_SOURCE")
            keys.add(key); sources.add(source); issues.append(issue)
        if page["isLast"]:
            return issues
        token = page.get("nextPageToken")
        if not isinstance(token, str) or not token or token in tokens:
            raise ValueError("INCOMPLETE_JIRA_PAGINATION")
        tokens.add(token); arguments["nextPageToken"] = token
    raise ValueError("JIRA_PAGINATION_LIMIT")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def private_save(path, value, replace=False):
    path = Path(path)
    if path.exists() and not replace:
        raise ValueError("EXISTING_ARTIFACT_MUST_NOT_BE_OVERWRITTEN")
    from free_tier_staging import private_directory
    private_directory(path.parent)
    temporary = path.with_name(path.name + "." + str(uuid.uuid4()) + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(canonical(value))
    temporary.replace(path)


def read_children(call, operation, key, field, page_size=50):
    rows, ids, offset = [], set(), 0
    for _ in range(1000):
        page = call("executeRead", {"name": operation, "cloudId": CLOUD_ID,
            "inputs": {"issueIdOrKey": key, "startAt": offset, "maxResults": page_size}})
        elements = page.get(field)
        if not isinstance(elements, list) or type(page.get("total")) is not int:
            raise ValueError("INCOMPLETE_CHILD_COLLECTION:" + operation)
        for row in elements:
            identifier = str(row.get("id", ""))
            if not identifier or identifier in ids:
                raise ValueError("DUPLICATE_CHILD_ID")
            ids.add(identifier); rows.append(row)
        if len(rows) == page["total"]:
            return rows
        if not elements or len(rows) > page["total"]:
            raise ValueError("INCOMPLETE_CHILD_COLLECTION")
        offset += len(elements)
    raise ValueError("CHILD_PAGINATION_LIMIT")


def read_sprint_membership(call, sprints):
    result = {}
    for sprint in sprints:
        value = call('executeRead', {'name': 'getJiraBoardSprintData', 'cloudId': CLOUD_ID,
            'inputs': {'boardId': str(sprint['originBoardId']), 'sprintId': str(sprint['id']), 'includeIssues': True}})
        issues = value.get('issues')
        total = value.get('sprintMetrics', {}).get('totalIssues')
        if (value.get('resolvedSprint', {}).get('id') != sprint['id'] or not isinstance(issues, list) or
                type(total) is not int or len(issues) != total or len({row['key'] for row in issues}) != total):
            raise ValueError('INCOMPLETE_SPRINT_MEMBERSHIP')
        result[str(sprint['id'])] = sorted(row['key'] for row in issues)
    return result


def collect_snapshot(call, progress=lambda *args: None, checkpoint=None, resume=None):
    identity = call("atlassianUserInfo", {})
    if identity.get("accountId") != "712020:0d04982c-00bf-46af-b3a7-446d0f44edfb":
        raise ValueError("JIRA_OPERATOR_IDENTITY_MISMATCH")
    resources = call("getAccessibleAtlassianResources", {})
    if not any(row.get("cloudId") == CLOUD_ID and row.get("url") == SITE for row in resources.get("resources", [])):
        raise ValueError("JIRA_SITE_MISMATCH")
    for query, operation in [("list Jira projects", "listJiraProjects"),
                             ("list Jira issue comments", "listJiraIssueComments"),
                             ("list Jira issue worklogs", "listJiraIssueWorklogs"),
                             ("list Jira issue changelogs", "listJiraIssueChangelogs"),
                             ("list Jira boards", "listJiraBoards"),
                             ("list Jira board sprints", "listJiraBoardSprints"),
                             ("get Jira board sprint data", "getJiraBoardSprintData")]:
        result = call("discover", {"query": query})
        if not any(row.get("name") == operation and row.get("executeTool") == "executeRead"
                   for row in result.get("results", [])):
            raise ValueError("REQUIRED_OFFICIAL_READ_UNAVAILABLE:" + operation)
    projects = call("executeRead", {"name": "listJiraProjects", "cloudId": CLOUD_ID,
                                     "inputs": {"query": "QAG3", "maxResults": 100}})
    if projects.get("isLast") is not True or not any(row.get("key") == "QAG3" and row.get("id") == "10002"
                                                   for row in projects.get("values", [])):
        raise ValueError("JIRA_PROJECT_MISMATCH")
    issues = read_issue_pages(call)
    if len(issues) != 329:
        raise ValueError("SOURCE_SET_CHANGED_REVIEW_REQUIRED")
    children = {}
    previous = resume or {}
    previous_issues = {issue['key']: issue for issue in previous.get('issues', [])}
    if checkpoint:
        checkpoint({"issues": issues, "children": children, "complete": False})
    for number, issue in enumerate(issues, 1):
        key, fields = issue["key"], issue["fields"]
        if (key in previous.get('children', {}) and previous_issues.get(key) == issue):
            children[key] = previous['children'][key]
            if checkpoint:
                checkpoint({"issues": issues, "children": children, "complete": False})
            progress(number, len(issues))
            continue
        children[key] = {"comments": [], "worklogs": [], "changelogs": []}
        for property_name, operation in [("comments", "listJiraIssueComments"), ("worklogs", "listJiraIssueWorklogs")]:
            container = fields.get("comment" if property_name == "comments" else "worklog", {})
            # Counts absent from a search response cannot be treated as zero.
            if container.get("total") != 0:
                children[key][property_name] = read_children(call, operation, key, property_name)
        children[key]["changelogs"] = read_children(call, "listJiraIssueChangelogs", key, "values")
        if checkpoint:
            checkpoint({"issues": issues, "children": children, "complete": False})
        progress(number, len(issues))
    boards = call("executeRead", {"name": "listJiraBoards", "cloudId": CLOUD_ID,
                                   "inputs": {"projectKeyOrId": "QAG3", "maxResults": 100}})
    if boards.get("isLast") is not True:
        raise ValueError("INCOMPLETE_BOARD_COLLECTION")
    sprints = []
    for board in boards.get("values", []):
        if board.get("type") == "scrum":
            page = call("executeRead", {"name": "listJiraBoardSprints", "cloudId": CLOUD_ID,
                "inputs": {"boardId": board["id"], "state": "all", "maxResults": 100}})
            if page.get("isLast") is not True:
                raise ValueError("INCOMPLETE_SPRINT_COLLECTION")
            sprints.extend(page.get("values", []))
    memberships = read_sprint_membership(call, sprints)
    # Re-read fields after child pagination to reject a moving source rather than mixing versions.
    fresh = read_issue_pages(call)
    if fingerprint(issues) != fingerprint(fresh):
        raise ValueError("JIRA_CHANGED_DURING_SNAPSHOT_RETRY_MANUALLY")
    return {"schema": 1, "route": "official_atlassian_mcp", "read_complete": True, "at": time.time(),
            "project": "QAG3", "cloud_id": CLOUD_ID, "issues": issues, "children": children, "sprints": sprints,
            "sprint_memberships": memberships}


def load_snapshot(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("SNAPSHOT_PATH_OR_SIZE_DENIED")
    document = json.loads(path.read_text(encoding="utf-8"))
    snapshot = document["snapshot"]
    if (document["hash"] != fingerprint(snapshot) or snapshot.get("route") != "official_atlassian_mcp" or
            snapshot.get("read_complete") is not True or snapshot.get("project") != "QAG3" or
            snapshot.get("cloud_id") != CLOUD_ID or len(snapshot["issues"]) != 329):
        raise ValueError("SNAPSHOT_NOT_VERIFIED")
    return snapshot


def status_map(statuses, expected_ids):
    result = {}
    for status in statuses:
        if status['id'] not in expected_ids:
            continue
        name = status['name'].upper()
        if name in result:
            raise ValueError('AMBIGUOUS_NATIVE_STATUS')
        result[name] = status['id']
    if set(result.values()) != expected_ids:
        raise ValueError('PROJECT_STATUS_SET_CHANGED')
    return result


def make_preview(snapshot, target, team, only_sources=None):
    items = target.packages()
    relations = target.collection('/api/v3/relations')
    dependent_ids = set()
    for relation in relations:
        if relation.get('type') in {'follows', 'precedes'}:
            for endpoint in ('from', 'to'):
                href = relation.get('_links', {}).get(endpoint, {}).get('href', '')
                if not re.fullmatch(r'/api/v3/work_packages/[1-9]\d*', href):
                    raise ValueError('NATIVE_RELATION_ENDPOINT_INVALID')
                dependent_ids.add(int(href.rsplit('/', 1)[-1]))
    field = target.bootstrap["fields"]["Source ID"]
    index = {}
    for item in items:
        source = item.get(field)
        if source:
            if source in index:
                raise ValueError("NATIVE_DUPLICATE_SOURCE")
            index[source] = item
    users = {}
    for member in team["members"]:
        identifier = target.bootstrap["users"].get(member["email"].lower())
        if identifier:
            person = target.call(f"/api/v3/users/{identifier}")
            # OpenProject intentionally hides other users' status from non-admins.
            # Do not claim hidden status was verified; native write validation still applies.
            if person.get("id") != identifier or ("status" in person and person["status"] != "active") or person.get("admin"):
                raise ValueError("MAPPED_USER_INACTIVE_OR_ADMIN")
            users[member["accountId"]] = identifier
    parents = {issue["key"]: source_id(issue) for issue in snapshot["issues"]}
    statuses = target.collection("/api/v3/statuses")
    by_status = status_map(statuses, set(target.bootstrap['statuses'].values()))
    priorities = target.collection('/api/v3/priorities')
    by_priority = {}
    for priority in priorities:
        name = priority['name'].casefold()
        if name in by_priority:
            raise ValueError('AMBIGUOUS_NATIVE_PRIORITY')
        by_priority[name] = priority['id']
    planned, unmapped = [], []
    for issue in snapshot["issues"]:
        source = source_id(issue)
        if only_sources is not None and source not in only_sources:
            continue
        if source not in index:
            unmapped.append({"source": source, "reason": "NO_EXISTING_LOCAL_WORK_PACKAGE"})
            continue
        item = index[source]
        row = plan_item(issue, item, index, users, parents, dependent_ids=dependent_ids)
        row['kind'] = item['_links']['type']['title']
        from jira_sync_records import child_preview, source_history
        children = snapshot['children'][issue['key']]
        row['children'] = child_preview(issue['key'], item['id'], target.actor, children)
        row['skipped'].extend(row['children']['skipped'])
        if 'description' in row['payload']:
            row['payload']['description']['raw'] += source_history(children)
        if issue['fields'].get('attachment'):
            raise ValueError('NEW_ATTACHMENTS_REQUIRE_DOWNLOAD_ADAPTER_QUALIFICATION')
        source_priority = issue['fields'].get('priority')
        if source_priority is not None:
            priority = by_priority.get(source_priority['name'].casefold())
            if priority is None:
                row['skipped'].append('PRIORITY_NO_EXACT_EQUIVALENT')
            elif not item['_links'].get('priority', {}).get('href', '').endswith('/' + str(priority)):
                row['payload'].setdefault('_links', {})['priority'] = {'href': f'/api/v3/priorities/{priority}'}
        row["before"] = {key: item.get(key) for key in ("subject", "description", "startDate", "dueDate", "lockVersion")}
        row["before"]["_links"] = {key: {"href": item["_links"].get(key, {}).get("href")}
                                    for key in ("parent", "assignee", "type", "status", "priority", "sprint")}
        row["status_id"] = by_status.get(row["source_status"])
        row["native_status"] = item["_links"]["status"]["title"].upper()
        row["gate_errors"] = []
        if row["source_status"] != row["native_status"] and target.name == "staging":
            gate = target.call(f"/api/v3/qldapm/gates/{item['id']}")
            candidates = [edge for edge in gate["transitions"] if edge["to"] == row["source_status"]]
            row["gate_errors"] = candidates[0]["errors"] if candidates else ["TRANSITION_DENIED"]
        elif row['source_status'] != row['native_status']:
            row['gate_errors'] = ['LIVE_HARD_GATE_NOT_DEPLOYED_STATUS_RETAINED']
        # Never reinterpret Jira checklist/evidence as native gate records.
        planned.append(row)
    return {"schema": 1, "target": target.name, "project_id": target.project, "actor": target.actor,
            "snapshot_hash": fingerprint(snapshot), "at": time.time(), "rows": planned, "unmapped": unmapped,
            "native_relations_hash": fingerprint(relations), "native_relations_retained": len(relations),
            "source_count": len(snapshot["issues"]), "native_count": len(items), "users": users,
            "summary": {"content_changes": sum(bool(row["payload"]) for row in planned),
                "status_differences": sum(row["source_status"] != row["native_status"] for row in planned),
                "gate_blocked": sum(bool(row["gate_errors"]) for row in planned),
                "native_workflow_validation_pending": 0,
                "comments": sum(len(row["comments"]) for row in snapshot["children"].values()),
                "worklogs": sum(len(row["worklogs"]) for row in snapshot["children"].values()),
                "attachments": sum(len(issue["fields"].get("attachment", [])) for issue in snapshot["issues"]),
                "source_history": sum(len(row['changelogs']) for row in snapshot['children'].values())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["snapshot", "preview", "apply", "verify"])
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--target", choices=["live", "staging"])
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--resume", type=Path, help="Private partial.json from an interrupted read; never used as a complete snapshot")
    arguments = parser.parse_args()
    runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/operator/jira-sync"
    if arguments.action == "snapshot":
        from jira_sync_mcp import OfficialMCP
        directory = arguments.resume.parent if arguments.resume else runtime / str(uuid.uuid4())
        previous = json.loads(arguments.resume.read_text()) if arguments.resume else None
        with OfficialMCP() as client:
            value = collect_snapshot(client.call, lambda n, total: print(canonical({"read": n, "total": total}), flush=True),
                checkpoint=lambda part: private_save(directory / "partial.json", part, replace=True), resume=previous)
        destination = directory / "snapshot.json"
        private_save(destination, {"hash": fingerprint(value), "snapshot": value})
        print(canonical({"snapshot": str(destination), "hash": fingerprint(value), "source_count": len(value["issues"])}))
    elif arguments.action == "preview":
        if not arguments.snapshot or not arguments.target:
            parser.error("preview requires --snapshot and --target")
        from jira_sync_target import Target
        snapshot = load_snapshot(arguments.snapshot)
        team = json.loads((Path(__file__).resolve().parents[2] / "JIRA_TEAM_QAG3.json").read_text())
        from jira_sync_operator import configuration, script_hashes, backup_proof
        from jira_sync_backup import SPECS, inspect
        if not arguments.backup:
            parser.error('preview requires --backup with a full current native restore/import proof')
        target = Target(arguments.target)
        scripts = script_hashes()
        proof = backup_proof(arguments.backup, target)
        if proof['proof']['import_exercise']['snapshot_hash'] != fingerprint(snapshot):
            raise ValueError('SOURCE_SNAPSHOT_NOT_REHEARSED')
        value = make_preview(snapshot, target, team)
        value.update(configuration=configuration(target), scripts=scripts,
            core_image=inspect(SPECS[target.name]['web'])['Image'], expires_at=time.time() + 3600,
            snapshot_path=str(arguments.snapshot.resolve()), backup=proof)
        if scripts != script_hashes():
            raise ValueError('OPERATOR_CODE_CHANGED_DURING_PREVIEW')
        destination = arguments.snapshot.parent / (arguments.target + "-preview-" + str(uuid.uuid4()) + ".json")
        private_save(destination, {"hash": fingerprint(value), "preview": value})
        print(canonical({"preview": str(destination), "hash": fingerprint(value), "target": value["target"],
                         "summary": value["summary"], "unmapped": len(value["unmapped"])}))
    else:
        if not arguments.preview:
            parser.error('apply/verify require --preview')
        from jira_sync_cli import apply, verify
        (apply if arguments.action == 'apply' else verify)(arguments.preview)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, (ValueError, RuntimeError, PermissionError)) and re.fullmatch(r'[A-Z][A-Z_:]{0,150}', str(error)) else 'SYNC_FAILED'
        print(canonical({"failed": True, "error_type": type(error).__name__, "code": code,
                         "message": "Sync stopped; no retry or gate bypass."}))
        raise SystemExit(1)
