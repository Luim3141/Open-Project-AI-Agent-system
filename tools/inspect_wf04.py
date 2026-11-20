import subprocess
import json

script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.get("SELECT id, name, nodes, connections FROM workflow_entity WHERE id = 'elfapV5D2PTnLiHW'", (err, row) => {
    if (err) { console.error(err); process.exit(1); }
    const nodes = JSON.parse(row.nodes);
    console.log('Nodes count:', nodes.length);
    for (const n of nodes) {
        console.log(' - ' + n.name + ' (' + n.type + ')');
        if (n.type.includes('webhook') || (n.parameters && n.parameters.path)) {
            console.log('   parameters:', JSON.stringify(n.parameters));
        }
    }
});
"""

res = subprocess.run(['docker', 'exec', 'qldapm-n8n-main', 'node', '-e', script], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
