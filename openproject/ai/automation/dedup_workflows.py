import subprocess

cleanup_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.serialize(() => {
  // Keep the latest 16 workflows
  db.run(`
    DELETE FROM workflow_entity 
    WHERE id NOT IN (
      SELECT id FROM workflow_entity ORDER BY id DESC LIMIT 16
    )
  `);
  
  // Clean published version and webhooks
  db.run(`
    DELETE FROM workflow_published_version 
    WHERE workflowId NOT IN (SELECT id FROM workflow_entity)
  `);
  
  db.run(`
    DELETE FROM webhook_entity 
    WHERE workflowId NOT IN (SELECT id FROM workflow_entity)
  `);
  
  db.all("SELECT id, name FROM workflow_entity", (err, rows) => {
    if (err) console.error(err);
    else {
      console.log(`Remaining active ${rows.length} workflows:`);
      for (const r of rows) console.log(` - ${r.id}: ${r.name}`);
    }
  });
});
"""

res = subprocess.run(["docker", "exec", "qldapm-n8n-main", "node", "-e", cleanup_script], capture_output=True, text=True, check=True)
print(res.stdout)
