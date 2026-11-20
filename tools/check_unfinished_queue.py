import sqlite3
import json
import time

db = sqlite3.connect('C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/gateway.sqlite')
run_id = '3ab443f1-6ceb-46aa-a374-b852a2979d94'

result = {'status': 'cancelled', 'error': 'ENGINEERING_CANCELLED', 'text': 'Phien lap ke hoach cu da huy de trien khai revision moi.'}
result_str = json.dumps(result, ensure_ascii=False)

db.execute("UPDATE ai_queue SET state='finished' WHERE id=?", (run_id,))
db.execute("UPDATE ai_runs SET state='failed_or_unknown', result=? WHERE id=?", (result_str, run_id))

# Update agent_runs document state to FAILED
row = db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()
if row:
    doc = json.loads(row[0])
    doc['state'] = 'CANCELLED'
    doc['updated_at'] = time.time()
    doc['result'] = result
    db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(doc), run_id))

db.commit()

# Check unfinished
count = db.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]
print(f"Unfinished count: {count}")
