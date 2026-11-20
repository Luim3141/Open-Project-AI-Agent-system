import sqlite3
import json

with sqlite3.connect('/state/gateway.sqlite') as d:
    cur = d.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("TABLES:", tables)
    
    for t in ['agent_runs', 'ai_runs', 'agent_tasks', 'engineering_reports', 'engineering_report_schedules', 'engineering_notifications']:
        if t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            print(f"  {t}: {cnt} rows")

    # Inspect the latest completed run in agent_runs
    cur.execute("SELECT id, task_id, document FROM agent_runs ORDER BY rowid DESC LIMIT 3")
    for r in cur.fetchall():
        run_id, task_id, doc_str = r
        try:
            doc = json.loads(doc_str)
            state = doc.get('state')
            has_result = bool(doc.get('result'))
            print(f"AgentRun: {run_id} | State: {state} | HasResult: {has_result}")
        except:
            pass
