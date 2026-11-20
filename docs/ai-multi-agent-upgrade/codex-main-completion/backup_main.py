"""Online Main backup for qualification; no stop/restart, no pruning or restore."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'openproject/ai'))
from free_tier_staging import private_directory
from jira_sync_backup import command, inspect, database_state, asset_command


def main():
    runtime = Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
    root = runtime/'openproject-ai/operator/codex-main-completion'
    private_directory(root)
    directory = root/datetime.now().strftime('backup-%Y%m%d-%H%M%S')
    directory.mkdir()
    web, gateway = inspect('qldapm-openproject-web-1'), inspect('qldapm-ai-gateway-1')
    assert web['Config']['Labels']['com.docker.compose.project'] == 'qldapm-openproject'
    assert gateway['Config']['Labels']['com.docker.compose.project'] == 'qldapm-ai'
    assert shutil.disk_usage(root).free > 5*1024**3, 'BACKUP_FREE_DISK_GUARD'
    state = database_state('qldapm-openproject-db-1')
    with (directory/'database.dump').open('xb') as stream:
        result = subprocess.run(['docker','exec','qldapm-openproject-db-1','pg_dump','-U','postgres','-Fc','openproject'],
                                stdout=stream,stderr=subprocess.PIPE,timeout=180)
        assert result.returncode == 0, 'MAIN_DUMP_FAILED_OUTPUT_WITHHELD'
    code = r'''
import sqlite3,tempfile,os,sys
s=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
busy=s.execute("SELECT count(*) FROM ai_runs WHERE state IN ('running','queued')").fetchone()[0]
busy+=s.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running','failed_or_unknown')").fetchone()[0]
assert busy==0,'ACTIVE_OR_UNKNOWN_MAIN_WORK'
with tempfile.TemporaryDirectory() as t:
 p=t+'/backup.sqlite';d=sqlite3.connect(p);s.backup(d);d.close();s.close()
 d=sqlite3.connect('file:'+p+'?immutable=1',uri=True);assert d.execute('PRAGMA integrity_check').fetchone()[0]=='ok';d.close()
 sys.stdout.buffer.write(open(p,'rb').read())
'''
    (directory/'gateway.sqlite').write_bytes(command(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],code.encode()))
    mounts = [m for m in web['Mounts'] if m['Destination']=='/var/openproject/assets']
    assert len(mounts)==1 and mounts[0]['Type']=='volume'
    (directory/'assets.tar').write_bytes(asset_command(web['Image'],mounts[0]['Name'],['tar','-cf','-','-C','/assets','.']))
    with tarfile.open(directory/'assets.tar') as archive:
        assert all(not (r.issym() or r.islnk() or r.isdev() or Path(r.name).is_absolute() or '..' in Path(r.name).parts) for r in archive)
    config=directory/'config';config.mkdir()
    for folder, filenames, prefix in [(runtime/'openproject',('.env','ui-bridge.yml','active-volumes.yml'),'core-'),
                                     (runtime/'openproject-ai',('.env','image-lock.json'),'gateway-'),
                                     (runtime/'openproject-ai/gateway',('config.json','credentials.json','ui.key'),'state-')]:
        for filename in filenames:
            source=folder/filename
            if source.is_file(): shutil.copy2(source,config/(prefix+filename.lstrip('.')))
    assert database_state('qldapm-openproject-db-1') == state, 'MAIN_CHANGED_DURING_BACKUP_RECONCILE'
    (directory/'database-state.json').write_text(json.dumps(state,indent=2))
    hashes={p.relative_to(directory).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
    receipt={'at':datetime.now(timezone.utc).isoformat(),'directory':str(directory),'target':'main','project_id':5,
             'core_image':web['Image'],'gateway_image':gateway['Image'],'hashes':hashes,
             'pg_tables':len(state),'online_backup':True,'writers_stopped':False,'restore_verified':False}
    (directory/'receipt.json').write_text(json.dumps(receipt,indent=2))
    (Path(__file__).parent/'backup-receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({k:receipt[k] for k in ('directory','target','pg_tables','online_backup','restore_verified')}))


if __name__=='__main__':main()
