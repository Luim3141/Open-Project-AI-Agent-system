path = 'openproject/ai/gateway/service.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if "run=self.store.agent_run(actor,self.config['project_id'],args['id'])" in line:
        # Check if the preceding line was business
        if "if business is not None:return monitor" in lines[i-1]:
            # Insert the engineering_scope check before this line
            eng_block = [
                "            if self.config.get('_engineering_scope') or self.config.get('project_id') == 6:\n",
                "                with self.store.connect() as db:row=db.execute(\"SELECT q.actor, q.payload FROM ai_queue q WHERE q.id=? AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw'\",(args['id'],)).fetchone()\n",
                "                if row:\n",
                "                    run_owner = row['actor']\n",
                "                    run = self.store.agent_run(run_owner, 6, args['id'])\n",
                "                    task = self.store.agent_task(run_owner, 6, run.task_id)\n",
                "                    events, receipts = self.store.execution_records(run_owner, 6, args['id'])\n",
                "                    from .engineering_monitor import project\n",
                "                    return project(self,who,authorized,task,run,json.loads(row['payload']),receipts,events)\n",
            ]
            new_lines.extend(eng_block)
            new_lines.append(line)
            i += 1
            continue
    elif "if self.config.get('_engineering_scope'):" in line and "row=db.execute" in lines[i+1]:
        # Skip the old block
        i += 9
        continue
    new_lines.append(line)
    i += 1

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully patched service.py")
