"""Reconcile and finalize run 99dd5576-afff-47b3-b5d1-f80eb3a3eb2d.
Follows official QLDAPM lifecycle:
1. Resume via lifecycle.resume(service, actor, run_id, version=1).
2. Claim run into executing state.
3. Call publish_native to update WP #384 and comment on #379.
4. Call knowledge to index into Second Brain Qdrant and verify retrieval.
5. Call finish to transition run to succeeded.
6. Verify read-backs.
"""
import hashlib
import json
from pathlib import Path

RUN_ID = '99dd5576-afff-47b3-b5d1-f80eb3a3eb2d'
HEAD_SHA = '0e8d320a3459f26d01c88a3e8d4cb861e09808dd'
BASE_SHA = 'def9d0a8852af42a407bd42fb0051615a2de9331'
PR_URL = 'https://github.com/Luim3141/mini-task-manager/pull/5'
RUN_DIR = Path(r'D:\AI project\QLDAPM chat\docs\ai\engineering\runs\99dd5576-afff-47b3-b5d1-f80eb3a3eb2d')
DIFF_REVISION = '185c9fe90c967e114727b3008890e60f2c5daebe221d3b3c61fd80957d484811'

def main():
    print(f"=== Reconciling and Finalizing Run {RUN_ID} ===")
    import subprocess
    
    code = f"""
import json, hashlib, time
from pathlib import Path
from gateway.store import Store, canonical
from gateway.service import Service
from gateway.engineering import scoped_service
from gateway.engineering_operator import operation

store = Store(Path('/state'))
config = json.loads(Path('/state/config.json').read_text())
service = scoped_service(Service(store, config, '/workspaces'), 6)
actor = 20
run_id = '{RUN_ID}'

# Step 1: Resume from checkpoint version 1
print('1. Resuming run from checkpoint version 1...')
res_out = operation(service, 'resume', {{'run_id': run_id, 'checkpoint_version': 1}})
print('   Resume result:', json.dumps(res_out))

# Step 2: Claim run to transition to executing
print('2. Claiming run...')
claimed = operation(service, 'claim', {{}})
print('   Claimed:', claimed.get('id') if claimed else None)
assert claimed and claimed['id'] == run_id, f"Expected claimed {{run_id}}, got {{claimed}}"

# Step 3: Publish native
print('3. Publishing to OpenProject via publish_native...')
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
    'files_changed': ['task_manager/app.py', 'tests/test_tasks.py']
}}

pub = operation(service, 'publish_native', {{'run_id': run_id, 'result': delivery_result}})
print('   publish_native result:', json.dumps(pub))

# Step 4: Ingest knowledge into Second Brain
print('4. Ingesting knowledge into Second Brain...')
know = operation(service, 'knowledge', {{'run_id': run_id, 'child_id': pub['child_id']}})
print('   knowledge retrieval items count:', len(know.get('retrieval', {{}}).get('items', [])))

# Step 5: Finish run
print('5. Finishing run in Gateway...')
fin = operation(service, 'finish', {{'run_id': run_id, 'result': delivery_result}})
print('   finish result:', json.dumps(fin))

# Step 6: Save checkpoint succeeded
operation(service, 'checkpoint', {{'run_id': run_id, 'document': {{'stage': 'COMPLETE', 'terminal_known': True, 'resumable': False}}}})
print('6. Checkpoint updated to COMPLETE')

print(json.dumps({{
    'ok': True,
    'child_id': pub['child_id'],
    'child_version': pub['child_version'],
    'parent_version': pub['parent']['version'],
    'pr_url': pub['pr_url'],
    'retrieval_count': len(know.get('retrieval', {{}}).get('items', []))
}}))
"""

    cmd = ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-c', code]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", p.stdout)
    if p.returncode != 0:
        print("STDERR:\n", p.stderr)
        raise RuntimeError("Reconcile script failed")

    # Save result.json to run folder
    delivery_result = {
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
    }
    (RUN_DIR / "result.json").write_text(json.dumps(delivery_result, indent=2), encoding='utf-8')
    print("Saved result.json successfully.")

if __name__ == '__main__':
    main()
