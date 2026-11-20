import subprocess
import json

code = """
import json, sqlite3
d = sqlite3.connect('/state/gateway.sqlite')
rows = d.execute("SELECT plan_id, document, updated FROM engineering_plans WHERE project=6").fetchall()
for r in rows:
    print('PLAN:', r[0], 'UPDATED:', r[2])
    print(r[1])
"""

cmd = ['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code]
p = subprocess.run(cmd, capture_output=True, text=True)
print(p.stdout)
