import subprocess

script = """
import sqlite3
with sqlite3.connect('/state/gateway.sqlite') as d:
    for row in d.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name IN ('agent_runs', 'agent_tasks', 'ai_queue', 'ai_runs')"):
        print(row[0], ':', row[1])
"""

res = subprocess.run(['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', script], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
