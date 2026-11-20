import sqlite3
import os

for a in ['dev', 'reviewer', 'qa']:
    db_p = os.path.expanduser(f'~/.openclaw/agents/{a}/agent/openclaw-agent.sqlite')
    if os.path.exists(db_p):
        conn = sqlite3.connect(db_p)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        print(f"=== Agent: {a} ({db_p}) ===")
        for t in tables:
            cnt = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  Table: {t} -> {cnt} rows")
        conn.close()
