"""Host-only daily Main snapshots. Windows Task invokes hourly; each store is read consistently."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import time
import uuid

from automation.main_operations import PRIVATE_ROOT,backup,capture,command,private_path,verify
from automation.main_auxiliary_backup import backup as auxiliary_backup
from gateway.knowledge_lock import lease

RUNTIME=PRIVATE_ROOT.parent


def once(root=None,now=None):
    root=private_path(root or PRIVATE_ROOT/'main-scheduled-backups');root.mkdir(parents=True,exist_ok=True)
    now=time.time() if now is None else now
    with lease(root/'backup.lock'):
        last=root/'last-success.json'
        if last.exists() and 0<=now-json.loads(last.read_text())['at']<86400:
            return {'status':'NOT_DUE','native_writes':0}
        manifest=capture()
        if shutil.disk_usage(root).free<5*1024**3:raise ValueError('BACKUP_REQUIRES_FIVE_GIB_FREE')
        output=root/(datetime.datetime.fromtimestamp(now,datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
        output.mkdir(exist_ok=False)
        try:
            (output/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2))
            native=backup(manifest,output/'native')
            auxiliary=auxiliary_backup(manifest,output/'auxiliary',qualify=False)
            private=output/'private-config';private.mkdir()
            names=['.env','image-lock.json','gateway/config.json','gateway/credentials.json','gateway/ui.key',
                'gateway/gemini.json','gateway/gemini.key','gateway/gemini-readiness.json','gateway/automation.key',
                'operator/gemini-main/free-tier-proof.json','operator/n8n-main-owner/owner.json']
            hashes={}
            for name in names:
                source=RUNTIME/name
                if source.is_symlink() or not source.is_file() or source.stat().st_size>1048576:
                    raise ValueError('BACKUP_PRIVATE_CONFIG_REQUIRED')
                data=source.read_bytes();destination=private/name;destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
            for name in manifest['containers']:
                (private/(name+'.json')).write_bytes(command('inspect',name))
            verify(manifest)
            result={'status':'PASS_MAIN_DAILY_SNAPSHOT','at':now,'directory':output.name,'private_config_sha256':hashes,
                'native_status':native['status'],'auxiliary_status':auxiliary['status'],'captured_active_work':manifest['active'],
                'native_writes':0,'staging_operations':False,
                'limits':['Individual consistent snapshots, not atomic across services','Qdrant collection is not backed up by this task',
                    'No automatic restore, history deletion or replay; existing backups retained','Runs only while the limited interactive Windows user and Docker are available']}
            (output/'result.json').write_text(json.dumps(result,indent=2))
            temporary=last.with_suffix('.tmp');temporary.write_text(json.dumps(result,indent=2));temporary.replace(last)
            return result
        except Exception as error:
            (output/'failure.json').write_text(json.dumps({'status':'FAILED_DO_NOT_RESTORE','at':now,'error_type':type(error).__name__}))
            raise


if __name__=='__main__':
    root=PRIVATE_ROOT/'main-scheduled-backups'
    try:
        result=once(root)
    except Exception as error:
        root.mkdir(parents=True,exist_ok=True)
        (root/'last-attempt.json').write_text(json.dumps({'status':'FAILED','at':time.time(),'error_type':type(error).__name__}))
        raise
    (root/'last-attempt.json').write_text(json.dumps({'at':time.time(),**result},indent=2))
    print(json.dumps({key:result[key] for key in ('status','native_writes')}))
