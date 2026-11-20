import subprocess

script = """
import sqlite3
with sqlite3.connect('/state/gateway.sqlite') as d:
    r = d.execute("SELECT payload FROM ai_queue WHERE json_extract(payload, '$.engine') = 'openclaw' ORDER BY rowid DESC LIMIT 1").fetchone()
    if r: print(r[0])
    else: print("NONE_FOUND")
"""

res = subprocess.run(['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', script], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
