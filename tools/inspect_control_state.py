import sqlite3, json

db = sqlite3.connect('C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/gateway.sqlite')
cur = db.cursor()

cur.execute("SELECT * FROM engineering_control")
col_names = [d[0] for d in cur.description]
for row in cur.fetchall():
    print("engineering_control:", dict(zip(col_names, row)))

cur.execute("SELECT * FROM engineering_worker_state")
col_names = [d[0] for d in cur.description]
for row in cur.fetchall():
    print("engineering_worker_state:", dict(zip(col_names, row)))

cur.execute("SELECT * FROM engineering_report_schedules")
col_names = [d[0] for d in cur.description]
for row in cur.fetchall():
    print("engineering_report_schedules:", dict(zip(col_names, row)))
