import subprocess

node_script = """
const { Container } = require('/usr/local/lib/node_modules/n8n/node_modules/typedi');
const { WebhookService } = require('/usr/local/lib/node_modules/n8n/dist/webhooks/webhook.service');
const { Workflow } = require('/usr/local/lib/node_modules/n8n/node_modules/n8n-workflow');
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.get('SELECT * FROM workflow_published_version WHERE workflowId="k1nRLXMdmVTuo2U8"', (err, row) => {
    if (err) { console.error(err); return; }
    const wfData = JSON.parse(row.workflowData);
    const workflow = new Workflow({
        id: 'k1nRLXMdmVTuo2U8',
        name: 'test',
        nodes: wfData.nodes,
        connections: wfData.connections,
        active: true,
        nodeTypes: { getByNameAndVersion: () => ({ description: { webhooks: [{ name: 'default', httpMethod: '={{$parameter["httpMethod"]}}', responseCode: '={{$parameter["responseCode"]}}', responseMode: '={{$parameter["responseMode"]}}', path: '={{$parameter["path"]}}' }] } }) }
    });
    console.log('Webhook node parameters:', wfData.nodes.find(n => n.type.includes('webhook'))?.parameters);
});
"""

res = subprocess.run(
    ["docker", "exec", "qldapm-n8n-main", "node", "-e", node_script],
    capture_output=True,
    text=True
)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
