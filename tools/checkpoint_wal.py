import sqlite3

db = sqlite3.connect('C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/gateway.sqlite')
db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
db.close()
print("WAL checkpointed successfully")
