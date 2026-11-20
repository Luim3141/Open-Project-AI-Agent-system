import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-access-gantt-boards"
raw_data = json.loads((OUTPUT_DIR / "wp_audit_raw.json").read_text(encoding="utf-8"))
wps = raw_data["work_packages"]

print(f"Loaded {len(wps)} work packages from raw audit data.")

# 1. Generate GANTT_DATE_AUDIT.csv
audit_csv_path = OUTPUT_DIR / "GANTT_DATE_AUDIT.csv"
with open(audit_csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "ID", "Subject", "Type", "Status", "Parent ID", "Parent Subject",
        "Assignee", "Start Date", "Due Date", "Schedule Manually", "Audit Finding"
    ])
    for w in wps:
        finding = "MISSING_DATES" if not w["start_date"] and not w["due_date"] else "HAS_DATES"
        writer.writerow([
            w["id"],
            w["subject"],
            w["type_name"],
            w["status_name"],
            w["parent_id"] or "",
            w["parent_subject"] or "",
            w["assignee"] or "Unassigned",
            w["start_date"] or "",
            w["due_date"] or "",
            w["schedule_manually"],
            finding
        ])

print(f"Generated {audit_csv_path} with {len(wps)} rows.")

# 2. Plan Schedule Proposal
# Define 4 Sprints across an 8-week timeline:
# Sprint 1: 2026-10-05 (Mon) to 2026-10-16 (Fri) - 10 working days
# Sprint 2: 2026-10-19 (Mon) to 2026-10-30 (Fri) - 10 working days
# Sprint 3: 2026-11-02 (Mon) to 2026-11-13 (Fri) - 10 working days
# Sprint 4: 2026-11-16 (Mon) to 2026-11-27 (Fri) - 10 working days

sprint_map = {
    # Epic ID: (Sprint Name, Start Date, End Date)
    38: ("Sprint 1: Auth & Account Setup", date(2026, 10, 5), date(2026, 10, 16)),
    39: ("Sprint 1: Project Management", date(2026, 10, 5), date(2026, 10, 16)),
    40: ("Sprint 2: Backlog Management", date(2026, 10, 19), date(2026, 10, 30)),
    41: ("Sprint 2: Sprint & Planning", date(2026, 10, 19), date(2026, 10, 30)),
    42: ("Sprint 2: Task & User Story Tracking", date(2026, 10, 19), date(2026, 10, 30)),
    43: ("Sprint 3: Kanban Visual Board", date(2026, 11, 2), date(2026, 11, 13)),
    44: ("Sprint 3: Gantt & Timeline Engine", date(2026, 11, 2), date(2026, 11, 13)),
    45: ("Sprint 3: Issue & Bug Tracking", date(2026, 11, 2), date(2026, 11, 13)),
    46: ("Sprint 4: Team Communication & Comments", date(2026, 11, 16), date(2026, 11, 27)),
    47: ("Sprint 4: Progress Dashboard & Metrics", date(2026, 11, 16), date(2026, 11, 27)),
    48: ("Sprint 4: Notifications & Alerts", date(2026, 11, 16), date(2026, 11, 27)),
}

# Organize hierarchy
epics = {w["id"]: w for w in wps if w["type_name"] == "Epic"}
tasks_by_epic = {}
subtasks_by_task = {}

for w in wps:
    if w["type_name"] == "Task":
        pid = w["parent_id"]
        tasks_by_epic.setdefault(pid, []).append(w)
    elif w["type_name"] == "Subtask":
        pid = w["parent_id"]
        subtasks_by_task.setdefault(pid, []).append(w)

def add_business_days(start_d, n_days):
    cur = start_d
    added = 0
    while added < n_days:
        cur += timedelta(days=1)
        if cur.weekday() < 5:  # Mon-Fri
            added += 1
    return cur

# For each Epic:
# Distribute its Tasks sequentially/staggered within the Sprint
# For each Task:
# Distribute its Subtasks across BA -> Dev (BE/FE) -> QA/Review -> PM Acceptance
proposals = {}  # id -> dict of proposed dates

for epic_id, epic in epics.items():
    sprint_name, epic_start, epic_end = sprint_map[epic_id]
    tasks = tasks_by_epic.get(epic_id, [])
    n_tasks = len(tasks)
    
    # Calculate task offsets
    for t_idx, t in enumerate(tasks):
        # Stagger task start by business days
        task_start = add_business_days(epic_start, min(t_idx * 1, 4))
        subtasks = subtasks_by_task.get(t["id"], [])
        n_subs = len(subtasks)
        
        task_sub_dates = []
        for s_idx, s in enumerate(subtasks):
            sub_subject = s["subject"].lower()
            # Stagger subtasks according to role workflow:
            # 0: BA/Analysis (days 0-1)
            # 1: Backend/Architecture (days 1-3)
            # 2: Frontend/UI (days 2-4)
            # 3: QA/Testing (days 3-5)
            # 4: PM/Review/Docs (days 4-5)
            stage_offset = min(s_idx, 4)
            s_start = add_business_days(task_start, stage_offset)
            s_due = add_business_days(s_start, 1)  # 2 business days per subtask
            if s_due > epic_end:
                s_due = epic_end
            if s_start > s_due:
                s_start = s_due
            
            proposals[s["id"]] = {
                "id": s["id"],
                "subject": s["subject"],
                "type": "Subtask",
                "parent_id": t["id"],
                "sprint": sprint_name,
                "proposed_start": s_start.isoformat(),
                "proposed_due": s_due.isoformat(),
                "duration_days": (s_due - s_start).days + 1,
                "schedule_mode": "MANUAL",
                "rationale": f"Role stage {s_idx+1}/{n_subs} in {t['subject'][:25]}"
            }
            task_sub_dates.append((s_start, s_due))
        
        # Task date is derived from its subtasks
        if task_sub_dates:
            t_start = min(sd[0] for sd in task_sub_dates)
            t_due = max(sd[1] for sd in task_sub_dates)
        else:
            t_start = task_start
            t_due = add_business_days(task_start, 3)
            
        proposals[t["id"]] = {
            "id": t["id"],
            "subject": t["subject"],
            "type": "Task",
            "parent_id": epic_id,
            "sprint": sprint_name,
            "proposed_start": t_start.isoformat(),
            "proposed_due": t_due.isoformat(),
            "duration_days": (t_due - t_start).days + 1,
            "schedule_mode": "DERIVED (from Subtasks)",
            "rationale": f"Parent task rollup of {len(subtasks)} subtasks"
        }
        
    # Epic date is derived from all tasks
    epic_task_proposals = [proposals[t["id"]] for t in tasks if t["id"] in proposals]
    if epic_task_proposals:
        e_start = min(datetime.fromisoformat(p["proposed_start"]).date() for p in epic_task_proposals)
        e_due = max(datetime.fromisoformat(p["proposed_due"]).date() for p in epic_task_proposals)
    else:
        e_start = epic_start
        e_due = epic_end
        
    proposals[epic_id] = {
        "id": epic_id,
        "subject": epic["subject"],
        "type": "Epic",
        "parent_id": "",
        "sprint": sprint_name,
        "proposed_start": e_start.isoformat(),
        "proposed_due": e_due.isoformat(),
        "duration_days": (e_due - e_start).days + 1,
        "schedule_mode": "DERIVED (from Tasks)",
        "rationale": f"Top-level Epic milestone rollup of {len(tasks)} tasks"
    }

# 3. Generate GANTT_SCHEDULE_PROPOSAL.csv
proposal_csv_path = OUTPUT_DIR / "GANTT_SCHEDULE_PROPOSAL.csv"
with open(proposal_csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "ID", "Subject", "Type", "Parent ID", "Sprint / Milestone",
        "Proposed Start Date", "Proposed Due Date", "Duration (Calendar Days)",
        "OpenProject Scheduling Mode", "Rationale"
    ])
    for w in wps:
        p = proposals[w["id"]]
        writer.writerow([
            p["id"],
            p["subject"],
            p["type"],
            p["parent_id"],
            p["sprint"],
            p["proposed_start"],
            p["proposed_due"],
            p["duration_days"],
            p["schedule_mode"],
            p["rationale"]
        ])

print(f"Generated {proposal_csv_path} with {len(proposals)} proposed work packages.")

# Save proposal json for further processing if needed
(OUTPUT_DIR / "gantt_proposal.json").write_text(json.dumps(proposals, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved gantt_proposal.json successfully.")
