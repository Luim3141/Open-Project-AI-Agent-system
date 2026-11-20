import base64
import json
import re
import time
from urllib.parse import urlencode, urlsplit

import httpx
from .agent_trace import trace_event
from .permissions import AI_SYSTEM_OWNER


class NativeError(Exception):
    def __init__(self, status, message, details=None):
        self.status = status
        self.source = "openproject" if message.startswith("OPENPROJECT_") else "gateway"
        self.details = details
        super().__init__(message)


class Native:
    def __init__(self, base, token, project_id):
        self.base, self.token, self.project_id = base.rstrip("/"), token, int(project_id)
        self.deadline = time.monotonic() + 90
        parsed = urlsplit(self.base)
        if parsed.scheme != "http" or parsed.hostname not in ("web", "localhost", "127.0.0.1", "staging-web"):
            raise ValueError("UNTRUSTED_OPENPROJECT_ORIGIN")

    def call(self, path, method="GET", payload=None, *, binary=False):
        if not path.startswith("/api/v3/") or ".." in path or "\\" in path or "#" in path:
            raise ValueError("NATIVE_PATH_DENIED")
        if binary and (method != 'GET' or not re.fullmatch(r'/api/v3/attachments/[1-9][0-9]*/content', path)):
            raise ValueError('NATIVE_BINARY_PATH_DENIED')
        auth = base64.b64encode(("apikey:" + self.token).encode()).decode()
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise NativeError(503, "REQUEST_DEADLINE_EXCEEDED")
        trace_event("native", method)
        try:
            # Native scheduling may finish CREATE after 30s; keep its existing 90s overall deadline, never retry POST.
            timeout = remaining if method == 'POST' and path == '/api/v3/work_packages' else min(30, remaining)
            with httpx.stream(method, self.base + path, json=payload, timeout=timeout, follow_redirects=False,
                                     trust_env=False, headers={"Authorization": "Basic " + auth, "Host": "localhost:8088",
                                                              "X-Forwarded-Proto": "https", **getattr(self, "mutation_headers", {})}) as response:
                if response.is_redirect:
                    raise NativeError(502, "OPENPROJECT_REDIRECT_REFUSED")
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > (1048576 if binary else 8388608):
                        raise NativeError(502, "OPENPROJECT_RESPONSE_TOO_LARGE")
                    if time.monotonic() > self.deadline:
                        raise NativeError(503, "REQUEST_DEADLINE_EXCEEDED_OUTCOME_MAY_BE_UNKNOWN")
                status = response.status_code
                is_json = "json" in response.headers.get("content-type", "")
        except httpx.HTTPError:
            raise NativeError(503, "OPENPROJECT_UNAVAILABLE_OUTCOME_MAY_BE_UNKNOWN") from None
        try:
            document = json.loads(content) if content and is_json and (not binary or status >= 400) else {}
        except ValueError:
            raise NativeError(502, "OPENPROJECT_MALFORMED_RESPONSE") from None
        if status >= 400:
            detail = document.get("message") or document.get("error", "")
            raise NativeError(status, f"OPENPROJECT_{status}: {str(detail)[:300]}")
        if binary:
            return bytes(content)
        if content and not is_json:
            raise NativeError(502, "OPENPROJECT_NON_JSON_RESPONSE")
        return document

    def collection(self, path):
        items = []
        for page in range(1, 1001):
            result = self.call(path + ("&" if "?" in path else "?") + urlencode({"pageSize": 100, "offset": page}))
            elements = result.get("_embedded", {}).get("elements", [])
            items.extend(elements)
            if len(items) >= result.get("total", len(items)):
                return items
            if not elements:
                break
        raise NativeError(502, "INCOMPLETE_COLLECTION")

    def identity(self, expected):
        user = self.call("/api/v3/users/me")
        if user["id"] != expected:
            raise PermissionError("IDENTITY_MISMATCH_OR_ADMIN_TOKEN")
        project = self.call(f"/api/v3/projects/{self.project_id}")
        expected_identifier = "ai-dev-demo" if self.project_id == 6 else "qldapm-local"
        if project["identifier"] != expected_identifier:
            raise PermissionError("PROJECT_MISMATCH")
        if user.get("admin"):
            if not (expected == 18 and self.project_id in (5, 6) and user.get("login") == "op-owner" and user.get("status") == "active"):
                raise PermissionError("IDENTITY_MISMATCH_OR_ADMIN_TOKEN")
            proof = self.call(f"/api/v3/qldapm/permissions?project_id={self.project_id}" if self.project_id == 6 else "/api/v3/qldapm/permissions")
            if not (proof.get("actor") == expected and proof.get("project_id") == self.project_id
                    and proof.get("role") == AI_SYSTEM_OWNER and AI_SYSTEM_OWNER in proof.get("capabilities", [])):
                raise PermissionError("AI_SYSTEM_OWNER_CAPABILITY_REQUIRED")
            return {"user_id": expected, "name": user.get("name"), "role": AI_SYSTEM_OWNER,
                    "project_id": self.project_id, "capabilities": [AI_SYSTEM_OWNER]}
        members = self.collection(f"/api/v3/memberships?" + urlencode({"filters": json.dumps([
            {"project": {"operator": "=", "values": [str(self.project_id)]}},
            {"principal": {"operator": "=", "values": [str(expected)]}}])}))
        role_names = []
        for member in members:
            if member.get("_links", {}).get("principal", {}).get("href") != f"/api/v3/users/{expected}":
                continue
            for link in member.get("_links", {}).get("roles", []):
                role_names.append(link.get("title", "").removeprefix("QLDAPM "))
        roles = {"BA" if role == "BA-PM" else role for role in role_names} & {"PM", "BA", "BE", "FE", "QA"}
        if not roles:
            raise PermissionError("ACTIVE_PROJECT_ROLE_REQUIRED")
        role = next(role for role in ("PM", "BA", "BE", "FE", "QA") if role in roles)
        # Keep the registry's historical BA alias compatible; both mean read/comment only.
        if role == "BA" and "BA-PM" in role_names and "BA" not in role_names:
            role = "BA-PM"
        return {"user_id": expected, "name": user.get("name"), "role": role, "project_id": self.project_id}

    def packages(self):
        return self.collection(f"/api/v3/projects/{self.project_id}/work_packages")

    def relations(self, packages):
        visible = {p['id'] for p in packages}
        rows = {}
        identifiers = sorted(visible)
        for start in range(0, len(identifiers), 50):
            filters = [{'involved': {'operator': '=', 'values': [str(i) for i in identifiers[start:start+50]]}}]
            for row in self.collection('/api/v3/relations?' + urlencode({'filters': json.dumps(filters)})):
                endpoints = [re.fullmatch(r'/api/v3/work_packages/(\d+)',
                    (row.get('_links', {}).get(key) or {}).get('href') or '') for key in ('from', 'to')]
                if all(endpoints) and all(int(match[1]) in visible for match in endpoints):
                    rows[row['id']] = row
        return [rows[key] for key in sorted(rows)]

    def sprints(self):
        # Native project endpoint applies view_sprints/visibility; no direct database context.
        return [{key: row.get(key) for key in ('id','name','startDate','finishDate','startedAt','completedAt')}
                | {'status':row.get('_links',{}).get('status',{}).get('title')}
                for row in self.collection(f'/api/v3/projects/{self.project_id}/sprints')[:20]]

    def summary(self, expected_actor):
        result = self.call('/api/v3/qldapm/daily_summary')
        if result.get('actor') != expected_actor or result.get('project_id') != self.project_id:
            raise PermissionError('SUMMARY_SCOPE_MISMATCH')
        count, statuses, overdue = (result.get(key) for key in ('count', 'by_status', 'overdue_ids'))
        if (type(count) is not int or count < 0 or not isinstance(statuses, dict)
                or any(not isinstance(key, str) or type(value) is not int or value < 0 for key, value in statuses.items())
                or sum(statuses.values()) != count or not isinstance(overdue, list)
                or any(type(value) is not int or value <= 0 for value in overdue)
                or len(set(overdue)) != len(overdue) or len(overdue) > count):
            raise NativeError(502, 'OPENPROJECT_SUMMARY_INVALID')
        return {'count': count, 'by_status': statuses, 'overdue_ids': sorted(overdue)}

    def observer_packages(self, identifiers):
        return self.call('/api/v3/qldapm/observer_packages?' + urlencode({'project_id':self.project_id,'ids':','.join(map(str,identifiers))}))

    def observer_task_list(self, query, limit=200):
        return self.call('/api/v3/qldapm/observer_packages?' + urlencode({'project_id':self.project_id,'query':query,'limit':limit}))

    def package(self, identifier):
        item = self.call(f"/api/v3/work_packages/{int(identifier)}")
        if item["_links"]["project"]["href"] != f"/api/v3/projects/{self.project_id}":
            raise PermissionError("OTHER_PROJECT_DENIED")
        return item
