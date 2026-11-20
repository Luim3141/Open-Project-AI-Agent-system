"""Verify durable staging state and private configuration without resetting any quota."""
import hashlib
import json
from rbac_stage import RUNTIME, BACKUP, ROOT, GW, docker, command, report, save, check


def ledger():
    script="""import sqlite3,json,hashlib
c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert c.execute("select count(*) from ai_runs where state='running'").fetchone()[0]==0
assert c.execute("select count(*) from jobs where state in ('running','queued')").fetchone()[0]==0
print(json.dumps({t:hashlib.sha256(json.dumps(c.execute('select * from '+t+' order by rowid').fetchall(),sort_keys=True).encode()).hexdigest() for t in ['tokens','requests','gemini_usage','gemini_blocks','gemini_recovery','ai_runs','proposals']}))
"""
    return json.loads(docker('exec',GW,'python','-c',script))


before=ledger()
for name in ('config.json','credentials.json','gemini.json','gemini.key','ui.key'):
    assert (RUNTIME/'stage-ai'/name).read_bytes()==(BACKUP/'gateway'/name).read_bytes(), name+' changed'
docker('restart',GW)
import time
for attempt in range(30):
    try:
        status=command('BE','get_assistant_status')
        break
    except Exception:
        if attempt==29: raise
        time.sleep(1)
assert before==ledger(), 'Durable state changed across restart'
assert status['gemini']['state']=='authorized'
assert status['gateway_mode']=='native'
for role in ('PM','BA-PM','BE','FE','QA'):
    state=command(role,'get_permissions')
    assert next(t['allowed'] for t in state['tools'] if t['name']=='update_work_package')==(role=='PM')
report['restart_passed']=True
report['final_images']={name:docker('inspect','--format','{{.Image}}',name).decode().strip() for name in (GW,'qldapm-ai-stage-staging-web-1')}
check('Gateway restart preserves tokens/receipts/runs/proposals/quota ledger; provider/key/config unchanged; five-role permissions reverified')
