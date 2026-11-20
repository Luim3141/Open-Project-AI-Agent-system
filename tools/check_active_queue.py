import subprocess
import json

cmd = [
    'docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c',
    'import sqlite3; d = sqlite3.connect("/state/gateway.sqlite"); print(d.execute("SELECT count(id) FROM ai_queue WHERE state != \'finished\'").fetchone()[0])'
]
r = subprocess.run(cmd, capture_output=True, text=True)
print("Active queue items:", r.stdout.strip())
