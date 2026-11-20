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

# Find WF05
wf5 = [w for w in workflows if "WF05" in w["name"]][0]
print("Found WF05:", wf5["id"], wf5["name"])

# Call POST /rest/workflows/:workflowId/activate with versionId
res = httpx.post(
    f"http://localhost:5679/rest/workflows/{wf5['id']}/activate",
    headers={"Cookie": client.cookie, "Content-Type": "application/json"},
    json={"versionId": wf5["versionId"]},
    timeout=10
)
print("Activate status:", res.status_code)
print("Activate response:", res.text[:200])
