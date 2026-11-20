import os
import sqlite3
import json

db_path = os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gateway.sqlite")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Get latest daily_brief run
cur = conn.execute("SELECT * FROM automation_runs WHERE json_extract(receipt, '$.kind') = 'daily_brief' ORDER BY created DESC LIMIT 1")
run = cur.fetchone()
rec_id = run["id"]
req_key = run["request_key"]
report_day = req_key.replace("daily:", "")

print(f"Latest automation_runs receipt:")
print(f"  ID: {rec_id}")
print(f"  Request Key: {req_key}")
print(f"  Report Day: {report_day}")

# Query daily_briefs for this run_id
rows = conn.execute("SELECT actor, project, day, document FROM daily_briefs WHERE json_extract(document, '$.run_id') = ? ORDER BY actor", (rec_id,)).fetchall()
print(f"\nSnapshots matching run_id ({rec_id}): {len(rows)}")
for r in rows:
    doc = json.loads(r["document"])
    match = (doc.get("run_id") == rec_id)
    print(f"  Actor {r['actor']:2} | Role: {doc.get('role'):5} | Day: {r['day']} | WP Count: {doc.get('snapshot', {}).get('count')} | Match Run ID: {match}")

# Also check by day = report_day
rows_day = conn.execute("SELECT actor, project, day, document FROM daily_briefs WHERE day = ? ORDER BY actor", (report_day,)).fetchall()
print(f"\nSnapshots matching day ({report_day}): {len(rows_day)}")
for r in rows_day:
    doc = json.loads(r["document"])
    match = (doc.get("run_id") == rec_id)
    print(f"  Actor {r['actor']:2} | Role: {doc.get('role'):5} | Day: {r['day']} | Run ID: {doc.get('run_id')} | Match: {match}")
