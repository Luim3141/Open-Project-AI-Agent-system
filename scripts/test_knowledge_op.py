import subprocess

script = """
import json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway import engineering
from gateway.engineering_operator import operation, ACTOR

root = Path('/state')
store = Store(root)
config = json.loads((root / 'config.json').read_text())
service = engineering.scoped_service(Service(store, config, '/workspaces'), 6)

try:
    res = operation(service, 'knowledge', {'run_id': 'b1cca031-81f5-4df1-870b-cbeb23d51e66', 'child_id': 380})
    print('SUCCESS:', res.keys())
except Exception as e:
    import traceback
    traceback.print_exc()
"""

out = subprocess.check_output(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=script, text=True
)
print(out)
