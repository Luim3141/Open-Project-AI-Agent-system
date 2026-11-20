import sqlite3
import json
import time

con = sqlite3.connect(r"C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\gateway.sqlite")
cur = con.cursor()
cur.execute("SELECT actor, project, generation, document FROM native_index_scans;")
rows = cur.fetchall()
print(f"Total scan records: {len(rows)}\n")

for row in rows:
    doc = json.loads(row[3])
    observed = doc.get("observed_at", 0)
    diff = round(time.time() - observed, 1)
    print(f"Actor: {row[0]}, Project: {row[1]}, Generation: {row[2]}")
    print(f"  Observed at timestamp: {observed} (approx {diff}s ago)")
    print(f"  Visible packages: {doc.get('visible')}")
    print(f"  Changed packages: {doc.get('changed')}")
    print(f"  Authority: {doc.get('authority')}")
    print(f"  Inventory SHA256: {doc.get('inventory_sha256')[:16]}...")
    print()

cur.execute("SELECT count(*) FROM native_index_cursor WHERE visible = 1;")
print(f"Active visible items in cursor: {cur.fetchone()[0]}")
cur.execute("SELECT count(*) FROM knowledge_sync;")
print(f"Total knowledge_sync jobs: {cur.fetchone()[0]}")
cur.execute("SELECT state, count(*) FROM knowledge_sync GROUP BY state;")
print(f"Knowledge sync states: {cur.fetchall()}")
