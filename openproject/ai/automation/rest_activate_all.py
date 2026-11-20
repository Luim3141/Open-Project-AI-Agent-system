import os
import pathlib
import sys
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from n8n_owner import LocalN8n, provision

operator = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "operator"
owner_dir = operator / "n8n-main-owner"

client = LocalN8n("http://localhost:5679")
provision(owner_dir, client)

# Fetch all workflows
r = httpx.get("http://localhost:5679/rest/workflows", headers={"Cookie": client.cookie}, timeout=10)
workflows = r.json().get("data", [])
print(f"Activating {len(workflows)} workflows...")

for wf in workflows:
    wf_id = wf["id"]
    wf_name = wf["name"]
    version_id = wf["versionId"]
    try:
        res = httpx.post(
            f"http://localhost:5679/rest/workflows/{wf_id}/activate",
            headers={"Cookie": client.cookie, "Content-Type": "application/json"},
            json={"versionId": version_id},
            timeout=10
        )
        data = res.json().get("data", {})
        active = data.get("active", False)
        print(f" - [{active}] {wf_id}: {wf_name}")
    except Exception as e:
        print(f" - [ERROR] {wf_id}: {wf_name} -> {e}")

print("Activation completed for all workflows!")
