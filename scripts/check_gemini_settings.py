import subprocess
import json

code = '''
import json
from pathlib import Path
from gateway.gemini import Gemini
from gateway.store import Store

g = Gemini(Path("/state"))
p = g.settings(require_enabled=False)
print("SETTINGS:", json.dumps({k: str(v) for k, v in p.items()}))
readiness = g.readiness(p)
print("READINESS:", json.dumps(readiness))
multi = g.multi_agent_settings()
print("MULTI_AGENT_SETTINGS:", multi)
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=code,
    capture_output=True,
    text=True
)
print("Returncode:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
