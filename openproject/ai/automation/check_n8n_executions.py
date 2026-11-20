import subprocess

node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.get("SELECT count(*) as total, sum(case when status = 'running' then 1 else 0 end) as running FROM execution_entity;", (err, row) => {
    if (err) console.error(err);
    else console.log("EXEC_SUMMARY:" + JSON.stringify(row));
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
