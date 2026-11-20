"""Read schema/key names/aggregate receipt metadata only; no receipt contents."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

CODE=r'''import sqlite3,json
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
print(json.dumps({'schema':[list(r) for r in d.execute('PRAGMA table_info(gemini_call_receipts)')],
 'document_keys':[r[0] for r in d.execute('SELECT DISTINCT key FROM gemini_call_receipts,json_each(document) ORDER BY key')],
 'aggregates':[list(r) for r in d.execute("SELECT json_extract(document,'$.phase'),json_extract(document,'$.state'),count(*),sum(json_type(document,'$.usage.totalTokenCount')='integer') FROM gemini_call_receipts GROUP BY 1,2")] }))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=CODE,text=True,capture_output=True,timeout=20)
assert p.returncode==0,p.stderr
r=json.loads(p.stdout)
r.update(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         command='openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/workflows/inspect_receipt_schema.py',
         environment='MAIN SQLite mode=ro metadata only; no provider call or business writes',
         gateway_image=subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1','--format','{{.Image}}'],text=True).strip(),
         script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
Path(__file__).with_name('receipt-schema.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print('Saved schema/key names/aggregate phase counts only')
