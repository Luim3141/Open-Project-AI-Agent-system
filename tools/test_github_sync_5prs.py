import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'openproject' / 'ai'))

import json
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service, authorized
from gateway.engineering_github_sync import reconcile_github_with_openproject

store = Store(Path('C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway'))
config = json.loads(Path('C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/config.json').read_text())

service = scoped_service(Service(store, config, 'C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/workspaces'), 6)
native, who = authorized(service, actor=18)

res = reconcile_github_with_openproject(service, native, actor=18, repo='Luim3141/mini-task-manager')
print("GitHub Sync Output:")
print(json.dumps(res, indent=2))
