"""Restore the fresh Main dump into a NEW database in the owned clone; never drop data."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

OUT=Path(__file__).parent
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from jira_sync_backup import command,read_database_state,verify_archive

def main():
    receipt=json.loads((OUT/'backup-receipt.json').read_text());backup=Path(receipt['directory'])
    verify_archive(backup,receipt['hashes'])
    clone=json.loads((OUT/'clone.json').read_text());container=clone['names']['db']
    info=json.loads(command(['docker','inspect',container]))[0]
    assert info['Config']['Labels'].get('qldapm.qualification')=='codex-main-20261020'
    name='backup_verify_'+time.strftime('%Y%m%d_%H%M%S')
    command(['docker','exec',container,'createdb','-U','postgres',name])
    with (backup/'database.dump').open('rb') as stream:
        result=subprocess.run(['docker','exec','-i',container,'pg_restore','-U','postgres','--no-owner','--exit-on-error','-d',name],
                              stdin=stream,capture_output=True,timeout=150)
    assert result.returncode==0,'BACKUP_RESTORE_FAILED_OUTPUT_WITHHELD'
    actual=read_database_state(lambda sql:command(['docker','exec','-i',container,'psql','-XqAt','-v','ON_ERROR_STOP=1','-U','postgres','-d',name],sql.encode()))
    expected=json.loads((backup/'database-state.json').read_text())
    assert actual==expected,'FRESH_BACKUP_TABLE_FINGERPRINT_MISMATCH'
    program="import sqlite3;d=sqlite3.connect('file:/backup/gateway.sqlite?immutable=1',uri=True);assert d.execute('PRAGMA integrity_check').fetchone()[0]=='ok';print('SQLite cold integrity PASS')"
    output=command(['docker','run','--rm','--network','none','--read-only','--entrypoint','python','--mount',f'type=bind,src={backup},dst=/backup,readonly',receipt['gateway_image'],'-c',program]).decode().strip()
    result={'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'backup_directory':str(backup),'archive_hashes_verified':True,
            'restored_database':name,'restored_container':container,'tables_and_sequences_matched':len(actual),
            'sqlite_cold_integrity':'PASS','existing_databases_dropped':0,'main_mutations':0,'passed':True}
    (OUT/'fresh-backup-restore.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
