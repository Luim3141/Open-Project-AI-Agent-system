import subprocess
import json

code = """
import json, sqlite3
d = sqlite3.connect('/state/gateway.sqlite')
rows = d.execute("SELECT id, actor, native_id, document FROM engineering_unit_definitions").fetchall()
for r in rows:
    print('ID:', r[0], 'NATIVE_ID:', r[2])
    print(r[3])
"""

cmd = ['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code]
p = subprocess.run(cmd, capture_output=True, text=True)
print(p.stdout)
