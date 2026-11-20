import subprocess
import json

code = '''
import sqlite3
con = sqlite3.connect("/state/gateway.sqlite")
cur = con.cursor()
run = cur.execute("SELECT id, actor, state, result, created FROM ai_runs WHERE id='ca0c3b3f-c01d-4291-a327-9c06b98e4f63'").fetchone()
print("AI_RUN:", run)
jobs = cur.execute("SELECT id, state, result, created FROM jobs WHERE id LIKE '%ca0c3b3f%' OR payload LIKE '%ca0c3b3f%'").fetchall()
print("JOBS:", jobs)
all_jobs = cur.execute("SELECT id, state, result, error, created FROM jobs ORDER BY created DESC LIMIT 5").fetchall()
print("LATEST JOBS:", all_jobs)
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=code,
    capture_output=True,
    text=True
)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
