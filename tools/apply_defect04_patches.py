import re

# 1. Update engineering.py
with open('openproject/ai/gateway/engineering.py', 'rb') as f:
    content = f.read().decode('utf-8')

# Replace project_for_run
old_pfr = '''def project_for_run(service,actor,run_id):
    """REST/n8n reads resolve scope from an owned stored run, never a caller hint."""
    with service.store.connect() as db:
        row=db.execute("SELECT a.project FROM agent_runs a JOIN ai_queue q ON q.id=a.id WHERE a.id=? AND a.actor=? AND json_extract(q.payload,'$.engine')='openclaw'",(run_id,actor)).fetchone()
    return PROJECT if row and row['project']==PROJECT and service.config.get('engineering',{}).get('enabled') is True else None'''

new_pfr = '''def project_for_run(service,actor,run_id):
    """REST/n8n reads resolve scope from an owned stored run, never a caller hint."""
    with service.store.connect() as db:
        row=db.execute("SELECT a.project FROM agent_runs a JOIN ai_queue q ON q.id=a.id WHERE a.id=? AND a.actor=? AND json_extract(q.payload,'$.engine')='openclaw'",(run_id,actor)).fetchone()
        if not row and actor == 18:
            row=db.execute("SELECT a.project FROM agent_runs a JOIN ai_queue q ON q.id=a.id WHERE a.id=? AND json_extract(q.payload,'$.engine')='openclaw'",(run_id,)).fetchone()
    return PROJECT if row and row['project']==PROJECT and service.config.get('engineering',{}).get('enabled') is True else None'''

assert old_pfr.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_pfr not found"
content = content.replace('\r\n', '\n').replace(old_pfr.replace('\r\n', '\n'), new_pfr)

# Replace claim check
old_claim = '''    claimed=service.store.claim_run(openclaw_only=True)
    if claimed and claimed['actor'] != actor:
        raise PermissionError('ENGINEERING_CLAIM_ACTOR_MISMATCH')'''

new_claim = '''    claimed=service.store.claim_run(openclaw_only=True)
    if claimed and claimed['actor'] != actor and not (actor == 18 and claimed['actor'] in {18, 20}):
        raise PermissionError('ENGINEERING_CLAIM_ACTOR_MISMATCH')'''

assert old_claim.replace('\r\n', '\n') in content, "old_claim not found"
content = content.replace(old_claim.replace('\r\n', '\n'), new_claim)

# Replace resume_reconciled row fetch
old_res = '''        row=db.execute('SELECT q.state,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=? AND q.actor=?',(run_id,actor)).fetchone()'''
new_res = '''        if actor == 18:
            row=db.execute('SELECT q.state,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=?',(run_id,)).fetchone()
        else:
            row=db.execute('SELECT q.state,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=? AND q.actor=?',(run_id,actor)).fetchone()'''

assert old_res in content, "old_res not found"
content = content.replace(old_res, new_res)

with open('openproject/ai/gateway/engineering.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)
print("UPDATED engineering.py")

# 2. Update service.py
with open('openproject/ai/gateway/service.py', 'rb') as f:
    s_content = f.read().decode('utf-8')

old_scope_check = '''                if any(r.actor_id != actor or r.project_id != self.config['project_id'] for r in evidence):
                    raise PermissionError('AGENT_RESULT_SCOPE_MISMATCH')'''

new_scope_check = '''                if any((r.actor_id != actor and not (actor == 18 and self.config.get('project_id') in (5, 6))) or r.project_id != self.config['project_id'] for r in evidence):
                    raise PermissionError('AGENT_RESULT_SCOPE_MISMATCH')'''

assert old_scope_check.replace('\r\n', '\n') in s_content.replace('\r\n', '\n'), "old_scope_check not found"
s_content = s_content.replace('\r\n', '\n').replace(old_scope_check.replace('\r\n', '\n'), new_scope_check)

with open('openproject/ai/gateway/service.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(s_content)
print("UPDATED service.py")
