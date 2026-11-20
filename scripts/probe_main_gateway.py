import subprocess
import json

code = '''
import json, uuid, time
from gateway.planner import plan_request, resolve_target_agents
from gateway.agent_models import AgentTask

prompt = "BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49."
target_agents = resolve_target_agents(prompt, "supervisor")
print("TARGET_AGENTS:" + json.dumps(target_agents))

now = time.time()
task = AgentTask(
    task_id=str(uuid.uuid4()),
    actor_id=19,
    project_id=5,
    conversation_id=str(uuid.uuid4()),
    created_at=now,
    expires_at=now + 300,
    instruction=prompt,
    agent="supervisor"
)
plan = plan_request(task, actor_role="PM")
agent_sequence = [s.agent for s in plan.steps]
print("AGENT_SEQUENCE:" + json.dumps(agent_sequence))
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=code.encode('utf-8'),
    capture_output=True
)
print("Returncode:", res.returncode)
print("Stdout:", res.stdout.decode('utf-8', errors='replace'))
print("Stderr:", res.stderr.decode('utf-8', errors='replace'))
