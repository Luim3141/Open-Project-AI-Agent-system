import sqlite3

db = sqlite3.connect('C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/gateway.sqlite')
cur = db.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tables in gateway.sqlite: {len(tables)}")
for t in sorted(tables):
    try:
        cur.execute(f"SELECT count(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f" - {t}: {cnt} rows")
    except Exception as e:
        print(f" - {t}: error {e}")
