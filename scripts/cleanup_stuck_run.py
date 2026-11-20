import sqlite3

con = sqlite3.connect('/state/gateway.sqlite')
with con:
    con.execute("DELETE FROM ai_queue WHERE id='b1789cc5-0210-4828-9f52-c5546f39023f'")
    con.execute("DELETE FROM ai_runs WHERE id='b1789cc5-0210-4828-9f52-c5546f39023f'")
    con.execute("DELETE FROM agent_runs WHERE id='b1789cc5-0210-4828-9f52-c5546f39023f'")
    con.execute("UPDATE engineering_control SET mode='OFF' WHERE project=6")
print("Cleaned up stuck run successfully!")
