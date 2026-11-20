import json
import subprocess

node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.get('SELECT * FROM workflow_published_version WHERE workflowId="k1nRLXMdmVTuo2U8"', (err, row) => {
    if (err) { console.error(err); return; }
    const wf = JSON.parse(row.workflowData);
    for (const node of wf.nodes) {
        if (node.type.includes('webhook')) {
            node.webhookId = 'qldapm-approval';
        }
    }
    const updatedData = JSON.stringify(wf);
    db.run('UPDATE workflow_published_version SET workflowData=? WHERE workflowId="k1nRLXMdmVTuo2U8"', [updatedData], (err2) => {
        if (err2) console.error(err2);
        else console.log('Updated workflow_published_version with webhookId');
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
