import subprocess

node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

const mapping = {
  '1VoYHaHG274yXhhB': 'qldapm-ingest',
  'QPga4gCAvWLYmMXI': 'qldapm-op-sync',
  '7UOM7O7HKgQN7mBa': 'qldapm-agent-request',
  'ze2m4G9WNuCSnUSP': 'qldapm-agent-trace',
  'k1nRLXMdmVTuo2U8': 'qldapm-approval',
  'ucMfWrwg7OlJGwCL': 'qldapm-execute-mutation',
  'lKCPDbtBkNROifTB': 'qldapm-bug-triage',
  'evOeZv4b43EGMaxL': 'qldapm-wbs-breakdown',
  'S9FdtDCElBAjabmO': 'qldapm-qa-gate',
  'Y8GVd8joOVf3Dgc3': 'qldapm-knowledge-feedback'
};

db.serialize(() => {
  for (const [wfId, path] of Object.entries(mapping)) {
    db.run("UPDATE webhook_entity SET webhookPath = ? WHERE workflowId = ?", [path, wfId]);
  }
  console.log("All webhook paths updated cleanly!");
  
  db.all("SELECT workflowId, webhookPath, method FROM webhook_entity", (err, rows) => {
    if (err) console.error(err);
    else console.log("New webhooks in DB:", rows);
  });
});
"""

res = subprocess.run(
    ["docker", "exec", "qldapm-n8n-main", "node", "-e", node_script],
    capture_output=True,
    text=True
)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
