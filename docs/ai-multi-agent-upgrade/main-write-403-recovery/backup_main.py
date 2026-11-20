"""Fresh private online backup + restore into a new database on the owned clone, never Main restore."""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from inspect_runtime import ROOT,OUT,run
from qualify import inspect
sys.path.insert(0,str(ROOT/'openproject/ai'))
from jira_sync_backup import database_state,read_database_state
from free_tier_staging import private_directory

def main():
    assert not (OUT/'backup.json').exists(),'BACKUP_ALREADY_EXISTS_RECONCILE'
    q=json.loads((OUT/'qualification.json').read_text());private=Path(q['private'])
    directory=private/datetime.now().strftime('backup-%Y%m%d-%H%M%S');private_directory(directory)
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM';ai=runtime/'openproject-ai'
    before=database_state('qldapm-openproject-db-1')
    code="import sqlite3;s=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);assert s.execute(\"select count(*) from ai_runs where state in ('running','queued')\").fetchone()[0]==0;assert s.execute(\"select count(*) from jobs where state in ('queued','running','failed_or_unknown')\").fetchone()[0]==0;print('IDLE')"
    assert run('docker','exec','qldapm-ai-gateway-1','python','-c',code).strip()=='IDLE'
    assert shutil.disk_usage(directory).free>5*1024**3
    with (directory/'database.dump').open('xb') as stream:
        p=subprocess.run(['docker','exec','qldapm-openproject-db-1','pg_dump','-U','postgres','-Fc','openproject'],stdout=stream,stderr=subprocess.PIPE,timeout=180)
    assert p.returncode==0,'MAIN_BACKUP_FAILED_OUTPUT_WITHHELD'
    (directory/'database-state.json').write_text(json.dumps(before))
    for path in (ai/'gateway').glob('*.sqlite'):
        source=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
        dest=sqlite3.connect(directory/path.name);source.backup(dest);source.close()
        assert dest.execute('pragma integrity_check').fetchone()[0]=='ok';dest.close()
    for folder,names,prefix in ((ai,('.env','image-lock.json'),'ai-'),(runtime/'openproject',('.env','ui-bridge.yml','active-volumes.yml'),'core-'),
                                (ai/'gateway',('config.json','credentials.json','ui.key','gemini.key','gemini.json'),'state-')):
        for name in names:
            if (folder/name).is_file():shutil.copy2(folder/name,directory/(prefix+name.lstrip('.')))
    proof=ai/'operator/gemini-main/free-tier-proof.json'
    if proof.is_file():shutil.copy2(proof,directory/'free-tier-proof.json')
    # Dump contains account and TOTP data; keep it inside private storage and owned clone only.
    clone=q['names']['db'];assert inspect(clone)['Config']['Labels']['qldapm.qualification']=='main-write403-20261021'
    validation='verify_write403_'+datetime.now().strftime('%H%M%S')
    run('docker','cp',str(directory/'database.dump'),clone+':/tmp/'+validation+'.dump')
    run('docker','exec',clone,'createdb','-U','postgres',validation)
    p=subprocess.run(['docker','exec',clone,'pg_restore','-U','postgres','--exit-on-error','--no-owner','-d',validation,'/tmp/'+validation+'.dump'],capture_output=True,timeout=180)
    assert p.returncode==0,'ISOLATED_RESTORE_FAILED_OUTPUT_WITHHELD'
    def query(sql):
        p=subprocess.run(['docker','exec','-i',clone,'psql','-X','-v','ON_ERROR_STOP=1','-U','postgres','-d',validation,'-qAt'],input=sql.encode(),capture_output=True,timeout=60)
        assert p.returncode==0,'RESTORE_READBACK_FAILED_OUTPUT_WITHHELD'
        return p.stdout
    restored=read_database_state(query)
    protected=('work_packages','relations','sprints','versions','members','member_roles','roles','role_permissions','two_factor_authentication_devices')
    assert all(before[t]==restored[t] for t in protected),'BACKUP_PROTECTED_RESTORE_MISMATCH'
    after=database_state('qldapm-openproject-db-1');assert all(before[t]==after[t] for t in protected),'MAIN_CHANGED_DURING_BACKUP'
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}
    result={'directory':str(directory),'hashes':hashes,'restored_tables':len(restored),'restored_all_tables_equal':restored==before,
            'protected_tables_verified':list(protected),'validation_database':validation,'validation_container':clone,
            'sqlite_integrity':'PASS','online':True,'main_restore':False,'passed':True}
    (OUT/'backup.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='hashes'}))

if __name__=='__main__':main()
