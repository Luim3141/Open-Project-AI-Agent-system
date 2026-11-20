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

# Activate WF13
wf13_id = "2tr0jpqaaAiq9IOU"
wf13 = httpx.get(f"http://localhost:5679/rest/workflows/{wf13_id}", headers={"Cookie": client.cookie}).json()["data"]

res = httpx.post(
    f"http://localhost:5679/rest/workflows/{wf13_id}/activate",
    headers={"Cookie": client.cookie, "Content-Type": "application/json"},
    json={"versionId": wf13["versionId"]},
    timeout=10
)
print("WF13 Activate status:", res.status_code)
print("WF13 Activate response:", res.text[:200])
