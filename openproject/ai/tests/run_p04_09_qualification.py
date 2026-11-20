import os
import subprocess
import sys
from pathlib import Path

localappdata = Path(os.environ['LOCALAPPDATA'])
backup = localappdata / 'QLDAPM/openproject-ai/operator/local-backups/af2be0f4-f03f-4e69-9553-310ea50da148'
output = Path('docs/ai-multi-agent-upgrade/artifacts/P04-errors-clone.json').resolve()
if output.exists():
    output.unlink()

gateway_image = 'sha256:006b9c6cd8cec7f5e41cf7ae4fe9abae762475b7fd685d8dde66191f10554233'
core_image = 'sha256:8a42c7efe65d799dd2b4a259a8cacc567149a336a4dc366a830eb7c0f48bdfe8'

cmd = [
    sys.executable,
    'openproject/ai/tests/accept_n8n_owner.py',
    str(backup),
    str(output),
    '--persistence',
    '--workflow',
    '--daily-image', gateway_image,
    '--daily-core', core_image,
    '--errors'
]

print("Running command:", " ".join(cmd))
res = subprocess.run(cmd)
sys.exit(res.returncode)
