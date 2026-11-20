"""Hash-only read-back for protected WP391 execution records and Native package."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).parent
RUN = 'b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
label = sys.argv[1]
assert label in ('before', 'after', 'after-final', 'after-identity')
target = OUT / ('wp391-' + label + '.json')
assert not target.exists()
code = """import hashlib,json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
out={}
for table,key in [('ai_queue','id'),('ai_runs','id'),('engineering_checkpoints','run_id')]:
 rows=d.execute('select * from '+table+' where '+key+'=?',('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6',)).fetchall()
 assert len(rows)==1
 out[table]=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
out['provider_receipts']=d.execute('select count(*) from gemini_call_receipts').fetchone()[0]
print(json.dumps(out))
"""
result = json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=30))
native = subprocess.check_output(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',
    "SELECT row_to_json(t) FROM (SELECT * FROM work_packages WHERE id=391 AND project_id=6) t"],timeout=30)
assert native.strip().startswith(b'{')
result.update(native_sha256=hashlib.sha256(native).hexdigest(),run_id=RUN,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
if label.startswith('after'):
    before = json.loads((OUT/'wp391-before.json').read_text())
    assert {k:v for k,v in result.items() if k!='utc'} == {k:v for k,v in before.items() if k!='utc'}, 'PROTECTED_EXECUTION_OR_NATIVE_CHANGED'
    result['comparison'] = 'PASS; exact run/queue/checkpoint/Native and provider count unchanged'
target.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
