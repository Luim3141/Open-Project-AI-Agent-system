import subprocess
import json

script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.all("SELECT id, workflowId, status, startedAt, stoppedAt FROM execution_entity WHERE workflowId = 'elfapV5D2PTnLiHW' ORDER BY id DESC LIMIT 5", [], (err, rows) => {
    if (err) { console.error(err); process.exit(1); }
    console.log(JSON.stringify(rows, null, 2));
});
"""

res = subprocess.run(['docker', 'exec', 'qldapm-n8n-main', 'node', '-e', script], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
