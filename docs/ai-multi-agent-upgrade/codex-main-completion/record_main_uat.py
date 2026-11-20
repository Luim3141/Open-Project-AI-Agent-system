"""Read-back Main UAT invariants without touching auth sessions or business data."""
import json
import sys
from pathlib import Path
OUT = Path(__file__).parent
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'openproject/ai'))
from jira_sync_backup import command, database_state

def main():
    backup = json.loads((OUT / 'backup-receipt.json').read_text())
    before = json.loads((Path(backup['directory']) / 'database-state.json').read_text())
    actual = database_state('qldapm-openproject-db-1')
    protected = ['work_packages', 'members', 'member_roles', 'roles', 'role_permissions', 'relations']
    assert all(before[t] == actual[t] for t in protected), 'MAIN_BUSINESS_OR_RBAC_DRIFT_REQUIRES_REVIEW'
    code = '''import sqlite3,json
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
identifier='87803ca8-72a1-4643-b00f-8fda05a06266'
r=d.execute('SELECT actor,state FROM ai_runs WHERE id=?',(identifier,)).fetchone()
assert r==(19,'done'),r
print(json.dumps({'actor':r[0],'state':r[1],'run_id':identifier,'tables':{t:d.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('ai_runs','agent_runs','execution_events','proposals','gemini_usage','gemini_call_receipts')}}))
'''
    state = json.loads(command(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], code.encode()))
    assert state['tables']['gemini_usage'] == state['tables']['gemini_call_receipts'] == state['tables']['proposals'] == 0
    evidence = ['main-identity-post-verified.txt', 'main-identity-post-verified.png', 'main-supervisor-result.txt',
                'main-supervisor-result.png', 'main-monitor-detail.txt', 'main-monitor-detail.png', 'main-execution-history-filtered.txt', 'main-execution-history-filtered.png']
    assert all((OUT / p).is_file() for p in evidence)
    result = {'scope': 'REAL_MAIN_OWNER_NATIVE_SESSION', 'passed': True, 'protected_tables_unchanged': protected,
              'comparison_backup': backup['directory'], 'readonly_runtime': state, 'browser_evidence': evidence,
              'other_roles_main_browser': 'NOT_RUN', 'live_gemini': 'NOT_RUN_AWAITING_APPROVAL'}
    (OUT / 'main-browser-uat-readback.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()
