import subprocess
import json

node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.all("SELECT id, name, active, createdAt, updatedAt, nodes FROM workflow_entity ORDER BY id", (err, rows) => {
    if (err) {
        console.error(JSON.stringify({error: err.message}));
        return;
    }
    
    // Also get execution counts and latest execution per workflow
    db.all("SELECT workflowId, count(*) as total_execs, max(startedAt) as last_exec, max(status) as last_status FROM execution_entity GROUP BY workflowId", (err2, execRows) => {
        const execMap = {};
        if (!err2 && execRows) {
            execRows.forEach(e => {
                execMap[e.workflowId] = e;
            });
        }
        
        const summary = rows.map(r => {
            let nodesList = [];
            try {
                const parsed = JSON.parse(r.nodes);
                nodesList = parsed.map(n => ({name: n.name, type: n.type}));
            } catch(e) {}
            
            const ex = execMap[r.id] || {total_execs: 0, last_exec: null, last_status: null};
            return {
                id: r.id,
                name: r.name,
                active: Boolean(r.active),
                createdAt: r.createdAt,
                updatedAt: r.updatedAt,
                nodeCount: nodesList.length,
                nodes: nodesList,
                total_execs: ex.total_execs,
                last_exec: ex.last_exec,
                last_status: ex.last_status
            };
        });
        console.log("WORKFLOW_SUMMARY_START");
        console.log(JSON.stringify(summary, null, 2));
        console.log("WORKFLOW_SUMMARY_END");
    });
});
"""

res = subprocess.run(
    ["docker", "exec", "qldapm-n8n-main", "node", "-e", node_script],
    capture_output=True,
    text=True,
    timeout=30
)

if "WORKFLOW_SUMMARY_START" in res.stdout:
    part = res.stdout.split("WORKFLOW_SUMMARY_START")[1].split("WORKFLOW_SUMMARY_END")[0].strip()
    data = json.loads(part)
    print(f"Found {len(data)} workflows in n8n-main:")
    for w in data:
        print(f"- ID {w['id']}: [{('ACTIVE' if w['active'] else 'INACTIVE')}] {w['name']} | Nodes: {w['nodeCount']} | Execs: {w['total_execs']} | Last: {w['last_exec']} ({w['last_status']})")
    
    with open("docs/ai/engineering/n8n_live_workflows.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
else:
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
