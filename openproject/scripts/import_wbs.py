"""API v3 import with source reconciliation; never resets existing work-package state."""
import argparse
import base64
import csv
import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8088"


class API:
    def __init__(self, token):
        self.auth = "Basic " + base64.b64encode(("apikey:" + token).encode()).decode()

    def call(self, path, method="GET", payload=None, auth=True):
        parsed = urllib.parse.urlsplit(path)
        if parsed.netloc and parsed.hostname not in ("127.0.0.1", "localhost"):
            # HAL may use the current public host. Only its API path is consumed locally.
            if not parsed.path.startswith("/api/v3/"):
                raise ValueError("Unexpected API link")
        path = parsed.path + ("?" + parsed.query if parsed.query else "")
        if not path.startswith("/api/v3/"):
            raise ValueError("Not an API v3 path")
        headers = {"Content-Type": "application/json", "Host": "localhost:8088"}
        if auth:
            headers["Authorization"] = self.auth
        request = urllib.request.Request(BASE + path, data=None if payload is None else json.dumps(payload).encode(),
                                         headers=headers, method=method)
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"API {method} {path}: HTTP {error.code}: {detail[:800]}") from None

    def collection(self, path):
        items, page = [], 1
        while True:
            separator = "&" if "?" in path else "?"
            result = self.call(f"{path}{separator}pageSize=100&offset={page}")
            elements = result.get("_embedded", {}).get("elements", [])
            items.extend(elements)
            if len(items) >= result.get("total", len(items)):
                return items
            if not elements:
                raise RuntimeError("Incomplete paginated collection")
            page += 1


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        raise RuntimeError("API redirect refused: credentials must remain on loopback")


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def source_index(packages, field):
    result = {}
    for package in packages:
        source = package.get(field)
        if source:
            if source in result:
                raise RuntimeError(f"Duplicate Source ID on instance: {source}")
            result[source] = package
    return result


def description(row):
    parts = [row["Description"], "## Acceptance Criteria", row["Acceptance Criteria"],
             "## Checklist (manual gate)", "\n".join("- [ ] " + line for line in row["Checklist"].splitlines() if line)]
    for key in ("Source ID", "Reviewer Requirement", "Proposed Role", "Proposed Sprint",
                "Simulation Estimate Hours", "Simulation Points", "Depends On Source IDs",
                "Integration With Source IDs", "Labels", "Approval", "Proposed Priority"):
        parts.extend(["### " + key, row[key] or "—"])
    parts.append("Dữ liệu nguồn v7. Estimate/point là MÔ PHỎNG; Sprint chưa chốt lịch. "
                 "Việc tạo ticket không chứng minh chức năng đã được triển khai. "
                 "Checklist/child-completion/concurrency gate chưa cưỡng chế native.")
    return "\n\n".join(parts)


def import_snapshot(runtime, verify_only=False):
    config = json.loads((runtime / "bootstrap.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((runtime / "wbs-snapshot.csv").open(encoding="utf-8-sig", newline="")))
    assert len(rows) == 329 and len({r["Source ID"] for r in rows}) == 329
    by_id = {r["Issue ID"]: r["Source ID"] for r in rows}
    fields = config["fields"]
    api = API(config["api_token"])
    project_id = config["project_id"]
    path = f"/api/v3/projects/{project_id}/work_packages"
    index = source_index(api.collection(path), fields["Source ID"])
    before = len(index)
    schemas = {}
    for row in sorted(rows, key=lambda r: {"Epic": 0, "Task": 1, "Sub-task": 2}[r["Issue Type"]]):
        source = row["Source ID"]
        if source in index:
            continue
        if verify_only:
            raise RuntimeError(f"Missing work package: {source}")
        type_name = "Subtask" if row["Issue Type"] == "Sub-task" else row["Issue Type"]
        links = {"type": {"href": f"/api/v3/types/{config['types'][type_name]}"},
                 "status": {"href": f"/api/v3/statuses/{config['statuses']['NEW']}"},
                 "assignee": {"href": f"/api/v3/users/{config['users'][row['Proposed Assignee Email'].lower()]}"}}
        if row["Parent"]:
            links["parent"] = {"href": f"/api/v3/work_packages/{index[by_id[row['Parent']]]['id']}"}
        payload = {"subject": row["Summary"], "description": {"format": "markdown", "raw": description(row)},
                   "_links": links, fields["Source ID"]: source, fields["Proposed Sprint"]: row["Proposed Sprint"]}
        for source_key, target_key in (("Simulation Estimate Hours", "Simulation Hours"), ("Simulation Points", "Simulation Points")):
            if row[source_key]:
                payload[fields[target_key]] = float(row[source_key])
        if type_name not in schemas:
            form = api.call(path + "/form", "POST", payload)
            errors = form.get("_embedded", {}).get("validationErrors", {})
            if errors:
                raise RuntimeError(f"Form rejected {source}: {json.dumps(errors)[:800]}")
            schemas[type_name] = form["_embedded"]["schema"]
        schema = schemas[type_name]
        if fields["Source ID"] not in schema:
            raise RuntimeError("Source ID not enabled in instance schema")
        sprint_name = row["Proposed Sprint"].split(" ")[0]
        if sprint_name in config["sprints"] and "sprint" in schema:
            links["sprint"] = {"href": f"/api/v3/sprints/{config['sprints'][sprint_name]}"}
        triage = schema.get(fields["Triage"], {}).get("_embedded", {}).get("allowedValues", [])
        if not triage:
            raise RuntimeError("Triage options unavailable in actual schema")
        selected = next(o for o in triage if o["value"] == "needs-triage")
        links[fields["Triage"]] = {"href": selected["_links"]["self"]["href"]}
        try:
            package = api.call(path, "POST", payload)
        except (TimeoutError, socket.timeout, urllib.error.URLError, RuntimeError):
            # A timed-out POST may already have committed. Reconcile, never blindly retry it.
            for attempt in range(3):
                index = source_index(api.collection(path), fields["Source ID"])
                if source in index:
                    break
                time.sleep(2)
            else:
                raise
            package = index[source]
        index[source] = package
        save(runtime / "source-mapping.json", {s: p["id"] for s, p in index.items()})
        if len(index) % 25 == 0:
            print(f"Imported {len(index)}/329", flush=True)

    relations_path = "/api/v3/relations?filters=" + urllib.parse.quote(json.dumps([{ "from": {"operator": "=", "values": [str(p["id"]) for p in index.values()]}}]))
    relations = api.collection(relations_path)
    existing = {(r["_links"]["from"]["href"].split("/")[-1], r["_links"]["to"]["href"].split("/")[-1], r["type"]) for r in relations}
    expected_relations = set()
    relation_gaps = []
    # OpenProject permits only one relation per pair: schedule dependencies take precedence.
    for column, kind in (("Depends On Source IDs", "follows"), ("Integration With Source IDs", "relates")):
        for row in rows:
            for target in row[column].split():
                if target not in index:
                    raise RuntimeError(f"Unresolved relation: {row['Source ID']} -> {target}")
                from_id, to_id = str(index[row["Source ID"]]["id"]), str(index[target]["id"])
                key = (from_id, to_id, kind)
                expected_relations.add(key)
                reverse_kind = {"follows": "precedes", "relates": "relates"}[kind]
                if key in existing or (to_id, from_id, reverse_kind) in existing:
                    continue
                pair = next((r for r in relations if {
                    r["_links"]["from"]["href"].split("/")[-1],
                    r["_links"]["to"]["href"].split("/")[-1]} == {from_id, to_id}), None)
                if pair and kind == "relates":
                    relation_gaps.append({"source": row["Source ID"], "target": target, "kind": kind,
                                          "reason": "single relation per pair; native dependency retained, integration in description"})
                    continue
                if verify_only:
                    saved = json.loads((runtime / "relation-gaps.json").read_text())
                    if any(g["source"] == row["Source ID"] and g["target"] == target and g["kind"] == kind for g in saved):
                        relation_gaps.extend(g for g in saved if g["source"] == row["Source ID"] and g["target"] == target and g["kind"] == kind)
                        continue
                    raise RuntimeError(f"Missing relation: {key}")
                try:
                    if pair and pair["type"] == "relates" and kind == "follows":
                        existing.discard((pair["_links"]["from"]["href"].split("/")[-1], pair["_links"]["to"]["href"].split("/")[-1], "relates"))
                        new_kind = "follows" if pair["_links"]["from"]["href"].endswith("/" + from_id) else "precedes"
                        api.call(f"/api/v3/relations/{pair['id']}", "PATCH", {"type": new_kind})
                        pair["type"] = new_kind
                    else:
                        created = api.call(f"/api/v3/work_packages/{from_id}/relations", "POST",
                            {"type": kind, "_links": {"to": {"href": f"/api/v3/work_packages/{to_id}"}}})
                        relations.append(created)
                    existing.add(key)
                except RuntimeError as error:
                    if "HTTP 422" not in str(error) or "circular dependency" not in str(error):
                        raise
                    relation_gaps.append({"source": row["Source ID"], "target": target, "kind": kind,
                                          "reason": "native cycle/hierarchy restriction; exact source preserved in description"})
    if not verify_only:
        save(runtime / "relation-gaps.json", relation_gaps)
    packages = api.collection(path)
    index = source_index(packages, fields["Source ID"])
    assert len(packages) == len(index) == 329
    ac_count = 0
    for row in rows:
        p = index[row["Source ID"]]
        assert p["subject"] == row["Summary"]
        assert p["description"]["raw"] == description(row)
        type_name = "Subtask" if row["Issue Type"] == "Sub-task" else row["Issue Type"]
        assert p["_links"]["type"]["href"].endswith("/" + str(config["types"][type_name]))
        assert (p[fields["Proposed Sprint"]] or "") == row["Proposed Sprint"]
        assert p["_links"][fields["Triage"]]["title"] == "needs-triage"
        for source_key, target_key in (("Simulation Estimate Hours", "Simulation Hours"), ("Simulation Points", "Simulation Points")):
            value = p.get(fields[target_key])
            assert (float(value) if value is not None else None) == (float(row[source_key]) if row[source_key] else None)
        sprint_name = row["Proposed Sprint"].split(" ")[0]
        if sprint_name in config["sprints"]:
            assert p["_links"]["sprint"]["href"].endswith("/" + str(config["sprints"][sprint_name]))
        assert p["_links"]["assignee"]["href"].endswith("/" + str(config["users"][row["Proposed Assignee Email"].lower()]))
        parent = p["_links"].get("parent", {}).get("href")
        expected_parent = index[by_id[row["Parent"]]]["id"] if row["Parent"] else None
        assert (int(parent.split("/")[-1]) if parent else None) == expected_parent
        assert p["_links"]["status"]["href"].endswith("/" + str(config["statuses"]["NEW"]))
        if row["Issue Type"] == "Task":
            ac_count += len([line for line in row["Acceptance Criteria"].splitlines() if line.strip()])
    assert ac_count == 106
    report = {"work_packages": len(index), "created": len(index) - before, "task_ac": ac_count,
              "source_sha256": hashlib.sha256((runtime / "wbs-snapshot.csv").read_bytes()).hexdigest(),
              "expected_relations": len(expected_relations), "verified_parent_assignee_description": True}
    report["relation_gaps"] = len(relation_gaps)
    save(runtime / "import-report.json", report)
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    import_snapshot(args.runtime, args.verify_only)
