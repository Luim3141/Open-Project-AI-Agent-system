import sqlite3
import os

p = os.path.expandvars(r'%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gateway.sqlite')
print("Path:", p, "Exists:", os.path.exists(p))
if os.path.exists(p):
    conn = sqlite3.connect(p)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables:", tables)
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count} rows")
