import subprocess

code = '''
import sqlite3
con = sqlite3.connect("/state/gateway.sqlite")
cur = con.cursor()
print("ai_runs cols:", [c[1] for c in cur.execute("PRAGMA table_info(ai_runs)").fetchall()])
print("ai_runs data:", cur.execute("SELECT * FROM ai_runs").fetchall())
print("agent_runs cols:", [c[1] for c in cur.execute("PRAGMA table_info(agent_runs)").fetchall()])
print("agent_runs data:", cur.execute("SELECT * FROM agent_runs").fetchall())
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=code,
    capture_output=True,
    text=True
)
print("stdout:", res.stdout)
print("stderr:", res.stderr)
