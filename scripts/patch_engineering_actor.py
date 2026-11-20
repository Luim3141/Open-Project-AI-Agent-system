from pathlib import Path

p = Path('openproject/ai/gateway/engineering.py')
text = p.read_text(encoding='utf-8')

target = "now = time.time()\n        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=actor, project_id=PROJECT,"
replacement = "now = time.time()\n        run_actor = 20 if actor == 18 else actor\n        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=run_actor, project_id=PROJECT,"

assert target in text, "Target 1 not found"
text = text.replace(target, replacement)

target2 = "run = AgentRun(run_id=run_id,task_id=task.task_id,actor_id=actor,project_id=PROJECT,"
replacement2 = "run = AgentRun(run_id=run_id,task_id=task.task_id,actor_id=run_actor,project_id=PROJECT,"
assert target2 in text, "Target 2 not found"
text = text.replace(target2, replacement2)

target3 = """        db.execute('INSERT INTO agent_tasks VALUES(?,?,?,?,?,?)',(task.task_id,actor,PROJECT,task.conversation_id,task.model_dump_json(),task.expires_at))
        db.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?)',(run_id,task.task_id,actor,PROJECT,run.model_dump_json()))
        db.execute("INSERT INTO ai_runs VALUES(?,?,'running',?,?)",(run_id,actor,canonical({'status':'waiting','stage':'ADMITTED','text':'OpenClaw engineering unit đã được nhận; chờ worker.'}),now))
        db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'queued',?,'agent')",(run_id,actor,canonical(payload),now))"""

replacement3 = """        db.execute('INSERT INTO agent_tasks VALUES(?,?,?,?,?,?)',(task.task_id,run_actor,PROJECT,task.conversation_id,task.model_dump_json(),task.expires_at))
        db.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?)',(run_id,task.task_id,run_actor,PROJECT,run.model_dump_json()))
        db.execute("INSERT INTO ai_runs VALUES(?,?,'running',?,?)",(run_id,run_actor,canonical({'status':'waiting','stage':'ADMITTED','text':'OpenClaw engineering unit đã được nhận; chờ worker.'}),now))
        db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'queued',?,'agent')",(run_id,run_actor,canonical(payload),now))"""

assert target3 in text, "Target 3 not found"
text = text.replace(target3, replacement3)

p.write_text(text, encoding='utf-8')
print("PATCHED openproject/ai/gateway/engineering.py successfully!")
