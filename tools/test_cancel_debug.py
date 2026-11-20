import subprocess

script = """
import sys, json, time, uuid
from gateway.service import Service
from gateway.store import Store
from gateway.engineering import scoped_service

store = Store('/state')
with open('/state/config.json', 'r') as f:
    cfg = json.loads(f.read())
svc = Service(store, cfg, '/workspaces')
scoped = scoped_service(svc, 6)

fid = str(uuid.uuid4())
tid = str(uuid.uuid4())
trid = str(uuid.uuid4())
payload = {'project_id': 6, 'unit': 'test', 'engine': 'openclaw', 'native_id': 379, 'source_version': 1, 'spec_sha256': '0'*64}

with store.connect() as d:
    d.execute("INSERT INTO ai_queue (id, actor, payload, state, created) VALUES (?, 20, ?, 'queued', ?)", (fid, json.dumps(payload), time.time()))
    task_doc = json.dumps({'schema_version': 1, 'task_id': tid, 'actor_id': 20, 'project_id': 6, 'agent': 'dev', 'instruction': 'test', 'references': [], 'run_class': 'development', 'conversation_id': str(uuid.uuid4()), 'created_at': time.time(), 'expires_at': time.time()+1000})
    d.execute("INSERT INTO agent_tasks (id, actor, project, conversation, document, expires) VALUES (?, 20, 6, 'conv', ?, ?)", (tid, task_doc, time.time()+1000))
    run_doc = json.dumps({'schema_version': 1, 'run_id': fid, 'task_id': tid, 'actor_id': 20, 'project_id': 6, 'trace_id': trid, 'state': 'QUEUED', 'created_at': time.time(), 'updated_at': time.time(), 'result': None})
    d.execute("INSERT INTO agent_runs (id, task_id, actor, project, document) VALUES (?, ?, 20, 6, ?)", (fid, tid, run_doc))
    d.execute("INSERT INTO ai_runs (id, actor, state, result, created) VALUES (?, 20, 'running', ?, ?)", (fid, json.dumps({'status': 'running'}), time.time()))

try:
    res = scoped.execute_actor(18, {'action': 'engineering_cancel', 'arguments': {'run_id': fid}, 'project_id': 6})
    print('CANCEL SUCCESS:', json.dumps(res))
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    with store.connect() as d:
        d.execute("DELETE FROM ai_queue WHERE id=?", (fid,))
        d.execute("DELETE FROM agent_runs WHERE id=?", (fid,))
        d.execute("DELETE FROM agent_tasks WHERE id=?", (fid,))
        d.execute("DELETE FROM ai_runs WHERE id=?", (fid,))
"""

res = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], input=script, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
