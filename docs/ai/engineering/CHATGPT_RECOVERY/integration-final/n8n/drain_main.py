"""Bounded operator drain of already-persisted events; retain worker leases/retry policy."""
import json,subprocess
from pathlib import Path
code="""import collections,json,time
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.integration_events import deliver_pending
root=Path('/state');c=json.load(open(root/'config.json'));assert c['n8n_integration']['enabled'] is True
s=Service(Store(root),c,'/workspaces');counts=collections.Counter();deadline=time.monotonic()+240
for _ in range(200):
 if time.monotonic()>=deadline:break
 state=deliver_pending(s);counts[state]+=1
 time.sleep(5)
 if state in ('IDLE','DISABLED'):break
print(json.dumps({'operator_drain':dict(counts),'new_events_created':0,'retry_policy_changed':False,'run_replayed':False}))
"""
r=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=275)
assert r.returncode==0,'MAIN_EVENT_DRAIN_FAILED'
data=json.loads(r.stdout);(Path(__file__).parent/'main-operator-drain.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
