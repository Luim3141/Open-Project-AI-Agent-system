const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.run("DELETE FROM webhook_entity WHERE workflowId NOT IN (SELECT id FROM workflow_entity)", (err) => {
    if (err) console.error(err);
    else console.log("Cleaned orphaned webhooks successfully");
});
