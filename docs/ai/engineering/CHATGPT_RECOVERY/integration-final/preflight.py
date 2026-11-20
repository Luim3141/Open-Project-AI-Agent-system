"""Fresh MAIN snapshot and backup; raw configuration remains private."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation import main_operations as ops

private=ops.PRIVATE_ROOT/('integration-final-prechange-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
private.mkdir(parents=True,exist_ok=False)
manifest=ops.capture()
code="""import sqlite3,json,hashlib
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
print(json.dumps({'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],
'active':d.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0],
'provider_receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0],
'run391':[{ 'state':r[0], 'recovery_count':json.loads(r[1]).get('recovery_count'), 'payload_sha256':hashlib.sha256(r[1].encode()).hexdigest()} for r in d.execute('select state,payload from ai_queue where id=?',('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6',))]}))
"""
engineering=json.loads(ops.command('exec','qldapm-ai-gateway-1','python','-c',code))
assert engineering['mode']=='OFF' and engineering['active']==0
backup=ops.backup(manifest,private/'backup')
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest':manifest,
    'engineering':engineering,'backup':backup,'private_root':str(private),
    'authority':'Owner4b7b8932 FullIntegration; no391resume; Project5read-only; noDR; ComputerUsePhaseDonly; noPRmerge/paid'}
(OUT/'M0.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['utc','engineering','private_root','authority']}))
