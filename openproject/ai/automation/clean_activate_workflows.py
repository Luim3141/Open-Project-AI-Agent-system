import subprocess
import time

# Step 1: Clear old webhooks table to avoid unique constraint collision
clear_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run("DELETE FROM webhook_entity", (err) => {
    if (err) console.error("Error clearing webhooks:", err);
    else console.log("Cleared webhook_entity table cleanly");
});
"""
subprocess.run(["docker", "exec", "qldapm-n8n-main", "node", "-e", clear_script], check=True)

# Step 2: Get all workflow IDs
res = subprocess.run(["docker", "exec", "qldapm-n8n-main", "n8n", "list:workflow"], capture_output=True, text=True, check=True)
lines = [l.strip() for l in res.stdout.splitlines() if '|' in l]
print(f"Publishing {len(lines)} workflows...")

for line in lines:
    w_id, w_name = line.split('|', 1)
    pub = subprocess.run(["docker", "exec", "qldapm-n8n-main", "n8n", "publish:workflow", f"--id={w_id}"], capture_output=True, text=True)
    status = "OK" if pub.returncode == 0 else f"FAILED: {pub.stderr.strip()[:60]}"
    print(f" - {w_id}: {w_name} -> {status}")

# Step 3: Inspect registered webhooks
inspect_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.all("SELECT workflowId, webhookPath, method, node FROM webhook_entity", (err, rows) => {
    if (err) console.error(err);
    else {
        console.log(`Registered ${rows.length} webhooks:`);
        for (const r of rows) {
            console.log(` * [${r.method}] /webhook/${r.webhookPath} -> Node: ${r.node}`);
        }
    }
});
"""
res2 = subprocess.run(["docker", "exec", "qldapm-n8n-main", "node", "-e", inspect_script], capture_output=True, text=True, check=True)
print("\n" + res2.stdout)
