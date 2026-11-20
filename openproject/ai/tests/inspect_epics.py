import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-access-gantt-boards"
data = json.loads((OUTPUT_DIR / "wp_audit_raw.json").read_text(encoding="utf-8"))
wps = data["work_packages"]

epics = [w for w in wps if w["type_name"] == "Epic"]
print(f"Total Epics: {len(epics)}")
for e in epics:
    child_tasks = [w for w in wps if w["parent_id"] == e["id"]]
    total_subtasks = sum(len([s for s in wps if s["parent_id"] == t["id"]]) for t in child_tasks)
    print(f"Epic #{e['id']}: {e['subject']} -> {len(child_tasks)} Tasks, {total_subtasks} Subtasks")
    for t in child_tasks[:3]:
        print(f"   Task #{t['id']}: {t['subject']}")
    if len(child_tasks) > 3:
        print(f"   ... and {len(child_tasks) - 3} more tasks")
