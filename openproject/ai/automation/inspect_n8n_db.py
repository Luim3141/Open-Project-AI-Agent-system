import subprocess

node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, tables) => {
    if (err) { console.error(err); return; }
    console.log("Tables:", tables.map(t => t.name));
    
    db.all("SELECT * FROM webhook_entity", (err2, webhooks) => {
        if (err2) console.error("Webhooks err:", err2);
        else console.log("Webhooks count:", webhooks.length, JSON.stringify(webhooks));
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
