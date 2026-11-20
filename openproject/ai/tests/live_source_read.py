"""GET-only source/role reconciliation using the existing personal PM credential."""
import csv
import importlib.util
import json
import os
from pathlib import Path

from provision_member_tokens import BackendNative

root = Path(__file__).resolve().parents[1]
runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject"
ai = runtime.parent / "openproject-ai"
config = json.loads((ai / "gateway/config.json").read_text())
credentials = json.loads((ai / "gateway/credentials.json").read_text())
native = BackendNative(config["openproject_url"], credentials["19"], config["project_id"])
assert native.identity(19)["role"] == "PM"
assert BackendNative(config["openproject_url"], credentials["20"], config["project_id"]).identity(20)["role"] == "BA"
bootstrap = json.loads((runtime / "bootstrap.json").read_text())
spec = importlib.util.spec_from_file_location("source_import", root.parent / "scripts/import_wbs.py")
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
items = native.packages()
index = source.source_index(items, bootstrap["fields"]["Source ID"])
with (runtime / "wbs-snapshot.csv").open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))
assert len(items) == len(index) == len(rows) == 329
by_key = {row["Issue ID"]: row["Source ID"] for row in rows}
counts = {}
ac = 0
for row in rows:
    item = index[row["Source ID"]]
    assert item["subject"] == row["Summary"]
    assert item["description"]["raw"] == source.description(row)
    kind = "Subtask" if row["Issue Type"] == "Sub-task" else row["Issue Type"]
    assert item["_links"]["type"]["href"] == f"/api/v3/types/{bootstrap['types'][kind]}"
    assert item["_links"]["assignee"]["href"].endswith("/" + str(bootstrap["users"][row["Proposed Assignee Email"].lower()]))
    parent = item["_links"].get("parent", {}).get("href")
    expected = index[by_key[row["Parent"]]]["id"] if row["Parent"] else None
    assert (int(parent.rsplit("/", 1)[-1]) if parent else None) == expected
    counts[row["Issue Type"]] = counts.get(row["Issue Type"], 0) + 1
    if row["Issue Type"] == "Task":
        ac += len([line for line in row["Acceptance Criteria"].splitlines() if line.strip()])
assert ac == 106
print(json.dumps({"passed": True, "read_only": True, "work_packages": len(items), "types": counts,
    "source_ids_parent_assignee_description": True, "task_ac": ac, "roles": {"19": "PM", "20": "BA"}}))
