import subprocess

code = """import sqlite3
db = sqlite3.connect('/state/gateway.sqlite')
cnt = db.execute("SELECT count(1) FROM ai_queue WHERE state != 'finished'").fetchone()[0]
print(cnt)
"""

out = subprocess.check_output(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=code, text=True
)
print('Active runs count:', out.strip())
