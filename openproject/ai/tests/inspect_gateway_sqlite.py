import subprocess
import json

py = """
import sqlite3
import json
d = sqlite3.connect('file:/state/gateway.sqlite?mode=ro', uri=True)
tables = [r[0] for r in d.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(json.dumps({'tables': tables}))
for t in tables:
    cnt = d.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {cnt}")
"""
res = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-stage-staging-gateway-1', 'python', '-c', py], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
print("RETURNCODE:", res.returncode)
