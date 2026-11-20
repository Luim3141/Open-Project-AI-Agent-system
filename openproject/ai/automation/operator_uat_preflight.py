"""Current Main read-only preflight; live SQLite is read inside its owning container."""
import datetime
import json
import shutil
import sys
import time
import urllib.request

from automation.main_operations import PRIVATE_ROOT, capture, command, status

LEGACY_POINTS = {
    '2d5e7bdf-b4e0-52c6-b360-f45c1fbd74bf': 'op:wp:42',
    '59e1f1a4-b659-5c3d-ab23-ebb309481dc7': 'test:local:adr:0001',
    'b838195a-5afd-5f40-a70d-23c2ca9007bc': 'test:wp:999',
}

GATEWAY_PROBE = r"""import json,sqlite3,time
from pathlib import Path
from gateway.native import Native
from gateway.knowledge_integrity import reconcile
from gateway.vector_client import VectorClient
root=Path('/state');config=json.loads((root/'config.json').read_text())
assert config['project_id']==5 and config['gateway_mode']=='native'
keys=json.loads((root/'credentials.json').read_text())
native=Native(config['openproject_url'],keys['18'],5);native.identity(18)
packages=native.packages();items={x['id']:x for x in packages}
with sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True) as db:
 qa=db.execute('select state from qa_evidence where id=?',('fc0479a8-b30a-5e88-9e4a-10748cb30415',)).fetchone()
 expires=db.execute("select max(expires) from tokens where user_id=19 and role='PM' and revoked=0").fetchone()[0]
 quick=db.execute('pragma quick_check').fetchone()[0]
vector=VectorClient()
try:integrity=reconcile(root,5,packages,vector)
finally:vector.close()
integrity.pop('multiple_namespaces',None)
print(json.dumps({'integrity':integrity,'wp376':[items[376]['subject'],items[376]['lockVersion'],items[376]['_links']['status']['title']],
 'wp371':[items[371]['lockVersion'],items[371]['_links']['status']['title']],
 'qa':qa[0] if qa else None,'pm_token_remaining_seconds':(expires or 0)-time.time(),'gateway_quick_check':quick}))"""

N8N_PROBE = r"""const {DatabaseSync}=require('node:sqlite');
const db=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
const rows=db.prepare('SELECT name,active,activeVersionId FROM workflow_entity').all();
console.log(JSON.stringify(rows.map(x=>({code:x.name.match(/WF\d{2}/)?.[0],active:!!x.active,published:!!x.activeVersionId}))));db.close();"""


def assess(probe, workflows):
    integrity = probe['integrity']
    actual = {p['id']: p['source_id'] for p in integrity['unmatched_points']}
    return {
        'registered_knowledge': integrity['status'] in {'VERIFIED', 'PARTIAL_UNMATCHED_POINTS'},
        'protected_legacy_points': actual == LEGACY_POINTS,
        'wp376_preserved': probe['wp376'] == ['test2', 0, 'NEW'],
        'wp371_preserved': probe['wp371'] == [4, 'IN ANALYSIS'],
        'qa_pending': probe['qa'] == 'pending_qa',
        'gateway_sqlite': probe['gateway_quick_check'] == 'ok',
        'pm_token_valid': probe['pm_token_remaining_seconds'] > 0,
        'workflow_activation': len(workflows) == 16
            and {r['code'] for r in workflows} == {f'WF{i:02}' for i in range(1, 17)}
            and all(r['active'] and r['published'] for r in workflows),
    }


def main():
    checks = {}; details = {}; warnings = []
    try:
        manifest = capture(); runtime = status(manifest)
        checks['main_containers'] = all(r['state'] == 'running' and r['health'] in {'healthy', 'NOT_CONFIGURED'}
            for r in runtime['containers'].values())
        details['runtime'] = runtime; details['active_work'] = manifest['active']
        for port, path in [(18088, '/health_checks/default'), (18089, '/health'), (5679, '/healthz'),
                           (6333, '/healthz'), (11434, '/api/tags')]:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=5) as response:
                checks[f'port_{port}'] = response.status == 200
        probe = json.loads(command('exec', 'qldapm-ai-gateway-1', 'python', '-c', GATEWAY_PROBE))
        workflows = json.loads(command('exec', 'qldapm-n8n-main', 'node', '-e', N8N_PROBE))
        checks.update(assess(probe, workflows)); details['knowledge'] = probe['integrity']
        details['pm_token_remaining_days'] = round(probe['pm_token_remaining_seconds'] / 86400, 2)
        if probe['pm_token_remaining_seconds'] < 3 * 86400:
            warnings.append('PM token expires within three days; operator renewal required, no automatic rotation')
        if manifest['active']:
            warnings.append('Background work is active; inspect queues before any deployment or stop')
        backup = json.loads((PRIVATE_ROOT / 'main-scheduled-backups/last-success.json').read_text())
        checks['recent_backup'] = backup['status'] == 'PASS_MAIN_DAILY_SNAPSHOT' and 0 <= time.time()-backup['at'] < 26*3600
        checks['backup_disk'] = shutil.disk_usage(PRIVATE_ROOT).free >= 5*1024**3
        details['backup_status'] = backup['status']
    except Exception as error:
        checks['probe_completed'] = False
        details['error_type'] = type(error).__name__  # No raw credential, path or response in output.
    passed = bool(checks) and all(checks.values())
    print(json.dumps({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_READ_ONLY_PREFLIGHT' if passed else 'BLOCKED_PREFLIGHT',
        'checks': checks, 'details': details, 'warnings': warnings,
        'limits': ['Preflight is not business E2E or human UAT', 'No physical reboot or Qdrant restore qualification',
                   'Exact protected records reflect this takeover baseline; review legitimate later business changes'],
        'native_writes': 0, 'staging_operations': False}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
