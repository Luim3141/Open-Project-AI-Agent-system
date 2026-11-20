import os
import subprocess

backup_dest = r"C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\pre_prune_n8n_backup.sqlite"
node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run("VACUUM INTO '/home/node/.n8n/backup_pre_prune.sqlite';", (err) => {
    if (err) {
        console.error('VACUUM INTO err:', err);
        process.exit(1);
    }
    console.log('VACUUM INTO OK');
});
"""

res = subprocess.run(
    ["docker", "exec", "qldapm-n8n-main", "node", "-e", node_script],
    capture_output=True,
    text=True
)
print("STDOUT:", res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)

subprocess.run(["docker", "cp", "qldapm-n8n-main:/home/node/.n8n/backup_pre_prune.sqlite", backup_dest], check=True)
subprocess.run(["docker", "exec", "qldapm-n8n-main", "rm", "-f", "/home/node/.n8n/backup_pre_prune.sqlite"])
print(f"Backup copied to host: {os.path.exists(backup_dest)}, size: {os.path.getsize(backup_dest):,} bytes")
