"""Read-only release evidence; no raw rows or credentials leave private storage."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'openproject/ai'))
from automation import main_operations as ops

def main():
    label = sys.argv[1]
    assert label in ('before', 'after')
    target = OUT / ('runtime-' + label + '.json')
    assert not target.exists(), 'Preserve existing snapshot'
    manifest = ops.capture()
    result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'manifest': manifest, 'runtime': ops.status(manifest), 'route': 'CLI/read-only'}
    result['engineering'] = json.loads(ops.command('exec', 'qldapm-ai-gateway-1', 'python', '-c',
        "import sqlite3,json,time;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);"
        "print(json.dumps({'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],"
        "'executing':d.execute(\"select count(*) from ai_queue where state not in ('finished','queued')\").fetchone()[0],"
        "'provider_receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0]}))"))
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
