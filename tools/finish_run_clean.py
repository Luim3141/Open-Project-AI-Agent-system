"""Finish run 99dd5576-afff-47b3-b5d1-f80eb3a3eb2d with complete readbacks.
"""
import hashlib
import json
import subprocess
from pathlib import Path

RUN_ID = '99dd5576-afff-47b3-b5d1-f80eb3a3eb2d'
HEAD_SHA = '0e8d320a3459f26d01c88a3e8d4cb861e09808dd'
BASE_SHA = 'def9d0a8852af42a407bd42fb0051615a2de9331'
PR_URL = 'https://github.com/Luim3141/mini-task-manager/pull/5'
RUN_DIR = Path(r'D:\AI project\QLDAPM chat\docs\ai\engineering\runs\99dd5576-afff-47b3-b5d1-f80eb3a3eb2d')
DIFF_REVISION = '185c9fe90c967e114727b3008890e60f2c5daebe221d3b3c61fd80957d484811'

def main():
    print("=== Calling operator finish with complete readback evidence ===")
    
    code = f"""
import json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
from gateway.engineering_operator import operation

store = Store(Path('/state'))
config = json.loads(Path('/state/config.json').read_text())
service = scoped_service(Service(store, config, '/workspaces'), 6)
actor = 20
run_id = '{RUN_ID}'

# Retrieve native readback from receipt
with store.connect() as db:
    r_child = json.loads(db.execute("SELECT result FROM requests WHERE actor=20 AND key='engineering-{RUN_ID}-child'").fetchone()[0])
    p_379 = json.loads(db.execute("SELECT result FROM requests WHERE actor=20 AND key='engineering-{RUN_ID}-progress'").fetchone()[0])

from gateway.engineering import authorized
native, who = authorized(service, 20)
child_pkg = native.package(384)
parent_pkg = native.package(379)

native_readback = {{
    'child_id': 384,
    'child_version': child_pkg['lockVersion'],
    'parent': {{'id': 379, 'version': parent_pkg['lockVersion']}},
    'project_id': 6,
    'pr_url': '{PR_URL}'
}}

know = operation(service, 'knowledge', {{'run_id': run_id, 'child_id': 384}})
knowledge_readback = {{
    'project_id': 6,
    'child_id': 384,
    'retrieval_count': len(know.get('retrieval', {{}}).get('items', [])),
    'references': [{{'native_id': v.get('native_id'), 'citation': v.get('citation')}} for v in know.get('retrieval', {{}}).get('items', [])]
}}

delivery_result = {{
    'status': 'succeeded',
    'text': 'Them route GET /healthz delivered; WP379 chua Done. UAT deferred.',
    'base_sha': '{BASE_SHA}',
    'head_sha': '{HEAD_SHA}',
    'pr_url': '{PR_URL}',
    'delivery': {{
        'baseRefName': 'codex/openclaw-feedback-4d13e695555a8d44',
        'headRefName': 'codex/openclaw-health-check-v1',
        'headRefOid': '{HEAD_SHA}',
        'state': 'OPEN',
        'url': '{PR_URL}'
    }},
    'test_evidence': {{
        'exit_code': 0,
        'command': 'python -m pytest -q tests /opt/qldapm/acceptance/test_create_list.py /opt/qldapm/acceptance/test_crud_web.py',
        'artifact': '/app/docs/ai/engineering/runs/{RUN_ID}/acceptance-0.xml',
        'log_sha256': '{hashlib.sha256((RUN_DIR / "acceptance-0.log").read_bytes()).hexdigest()}'
    }},
    'review_evidence': {{
        'revision': '{DIFF_REVISION}',
        'verdict': 'PASS',
        'findings': [],
        'qa': {{
            'status': 'PASS',
            'exit_code': 0,
            'command': 'cd /home/openclaw/engineering/health-check-v1 && NODE_BINARY=/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node .venv/bin/python -m pytest -q tests /opt/qldapm/acceptance/test_create_list.py /opt/qldapm/acceptance/test_crud_web.py',
            'acceptance': ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9', 'F1', 'H1'],
            'failures': []
        }}
    }},
    'run_artifacts': '{str(RUN_DIR).replace(chr(92), "/")}',
    'files_changed': ['task_manager/app.py', 'tests/test_tasks.py'],
    'native_readback': native_readback,
    'knowledge_readback': knowledge_readback
}}

fin = operation(service, 'finish', {{'run_id': run_id, 'result': delivery_result}})
print('finish returned:', json.dumps(fin, indent=2))

operation(service, 'checkpoint', {{'run_id': run_id, 'document': {{'stage': 'COMPLETE', 'terminal_known': True, 'resumable': False}}}})
print('checkpoint updated to COMPLETE')
"""
    cmd = ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-c', code]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", p.stdout)
    if p.returncode != 0:
        print("STDERR:\n", p.stderr)
        raise RuntimeError("finish_run_clean failed")

    # Update result.json in RUN_DIR
    (RUN_DIR / "result.json").write_text(json.dumps({
        'status': 'succeeded',
        'text': 'Them route GET /healthz delivered; WP379 chua Done. UAT deferred.',
        'base_sha': BASE_SHA,
        'head_sha': HEAD_SHA,
        'pr_url': PR_URL,
        'delivery': {
            'baseRefName': 'codex/openclaw-feedback-4d13e695555a8d44',
            'headRefName': 'codex/openclaw-health-check-v1',
            'headRefOid': HEAD_SHA,
            'state': 'OPEN',
            'url': PR_URL
        },
        'test_evidence': {
            'exit_code': 0,
            'command': 'python -m pytest -q tests /opt/qldapm/acceptance/test_create_list.py /opt/qldapm/acceptance/test_crud_web.py',
            'artifact': str(RUN_DIR / 'acceptance-0.xml'),
            'log_sha256': hashlib.sha256((RUN_DIR / "acceptance-0.log").read_bytes()).hexdigest()
        },
        'review_evidence': {
            'revision': DIFF_REVISION,
            'verdict': 'PASS',
            'findings': [],
            'qa': {
                'status': 'PASS',
                'exit_code': 0,
                'command': 'cd /home/openclaw/engineering/health-check-v1 && NODE_BINARY=/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node .venv/bin/python -m pytest -q tests /opt/qldapm/acceptance/test_create_list.py /opt/qldapm/acceptance/test_crud_web.py',
                'acceptance': ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9', 'F1', 'H1'],
                'failures': []
            }
        },
        'run_artifacts': str(RUN_DIR),
        'files_changed': ['task_manager/app.py', 'tests/test_tasks.py']
    }, indent=2), encoding='utf-8')
    print("result.json written successfully.")

if __name__ == '__main__':
    main()
