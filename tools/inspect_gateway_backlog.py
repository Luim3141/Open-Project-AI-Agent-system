import subprocess
import json

code = """
import json
from gateway.service import Service
from gateway.store import Store
from gateway.engineering import scoped_service, status
from pathlib import Path

store = Store(Path('/state'))
config = json.loads(Path('/state/config.json').read_text())
service = scoped_service(Service(store, config, '/workspaces'), 6)
st = status(service, actor=20)
print(json.dumps({'mode': st['mode'], 'backlog': st['backlog']}))
"""

cmd = ['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code]
p = subprocess.run(cmd, capture_output=True, text=True)
if p.returncode != 0:
    print("STDERR:", p.stderr)
else:
    doc = json.loads(p.stdout.strip())
    print("MODE:", doc['mode'])
    print("BACKLOG:")
    for b in doc['backlog']:
        print(b)
