"""Verify the captured before/after evidence and private-file invariants; never modifies runtime."""
import hashlib
import json
from read_only_audit import OUT, RUNTIME

before=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
after=json.loads((OUT/'after.json').read_text(encoding='utf-8'))
details=json.loads((OUT/'details.json').read_text(encoding='utf-8'))
recovery=json.loads((OUT/'pm-recovery.json').read_text(encoding='utf-8'))
old={r['name']:r for r in before['containers'] if r['name'].startswith('qldapm-ai-stage-')}
new={r['name']:r for r in after['containers'] if r['name'].startswith('qldapm-ai-stage-')}
assert len(old)==len(new)==7
for row in [*old.values(),*new.values()]:
    row['mounts']=sorted(row['mounts'],key=lambda m:m['destination'])
    row['networks']=sorted(row['networks'])
assert old==new, 'Staging runtime identity/image/start/ports/networks/mounts changed'
assert all(r['running'] and r['health']=='healthy' and not r['oom'] for r in new.values())
assert before['url']==after['url'], 'Tunnel hostname changed'
assert before['stage_postgres']['business_fingerprints']==after['stage_postgres']['business_fingerprints']
kept=['ai_runs','agent_tasks','agent_runs','gemini_usage','gemini_call_receipts','execution_events','proposals','daily_briefs']
counts={}
for table in kept:
    a=before['stage_gateway']['gateway.sqlite']['tables'][table]['count']
    b=after['stage_gateway']['gateway.sqlite']['tables'][table]['count']
    assert a==b,table+' changed'
    counts[table]=b
assert before['stage_gateway']['knowledge.sqlite']['tables']['knowledge_documents']['count']==after['stage_gateway']['knowledge.sqlite']['tables']['knowledge_documents']['count']==5
for name,expected in details['private_hashes'].items():
    if name=='stage/accounts.json':
        continue  # Owner explicitly authorized PM7 password + TOTP recovery after the baseline.
    assert hashlib.sha256((RUNTIME/name).read_bytes()).hexdigest()==expected, 'Private file changed: '+name
assert recovery['protected_before']==recovery['protected_after']
result={'status':'PASS','stage_healthy_containers':7,'container_identity_start_ports_mounts_unchanged':True,
        'quick_tunnel_unchanged':True,'business_fingerprints_unchanged':True,'stage_counts':counts,
        'private_keys_config_unchanged':True,'authorized_exception':'PM7 password/TOTP reset; native enrollment pending',
        'main_business_fingerprints_unchanged':before['main_postgres']['business_fingerprints']==after['main_postgres']['business_fingerprints'],
        'evidence_window':[before['timestamp'],after['timestamp']]}
target=OUT/'preservation.json'
assert not target.exists(), 'Refuse evidence overwrite'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
