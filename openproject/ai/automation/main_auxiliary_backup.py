"""Private Main n8n/assets snapshot and network-isolated CLI/server restore qualification."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tarfile
import uuid

from automation.main_operations import command, private_path, verify


def validate_assets(data):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        names = set()
        for member in members:
            parts = member.name.replace('\\', '/').split('/')
            normalized = '/'.join(part for part in parts if part not in {'', '.'})
            if member.name.startswith(('/', '\\')) or '..' in parts or ':' in member.name or not (member.isfile() or member.isdir()) or normalized in names:
                raise ValueError('UNSAFE_ASSET_ARCHIVE')
            names.add(normalized)
        return {member.name: {'bytes': member.size, 'sha256': hashlib.sha256(archive.extractfile(member).read()).hexdigest()}
                for member in members if member.isfile()}


def restore_assets(data, output):
    expected = validate_assets(data)
    output = Path(output)
    output.mkdir(mode=0o700, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(output, filter='data')
    actual = {str(path.relative_to(output)).replace('\\', '/'): {'bytes': path.stat().st_size,
              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in output.rglob('*') if path.is_file()}
    if actual != {name.removeprefix('./'): value for name, value in expected.items()}:
        raise ValueError('ASSET_RESTORE_CONTENT_MISMATCH')
    return len(actual)


def qualify_restore(output, image, expected):
    # Only the copied database/config is writable; no service, port or Main network is started.
    code = r"""const fs=require('fs'),cp=require('child_process');
const key=JSON.parse(fs.readFileSync('/backup/n8n-key.json'));
fs.copyFileSync('/backup/n8n.sqlite','/home/node/.n8n/database.sqlite');
fs.copyFileSync('/backup/n8n-config','/home/node/.n8n/config');
if(key.env_key)process.env.N8N_ENCRYPTION_KEY=key.env_key;
for(const kind of ['workflow','credentials']){
 const args=['export:'+kind,'--all','--output=/tmp/'+kind+'.json'];
 if(kind==='credentials')args.push('--decrypted');
 cp.execFileSync('n8n',args,{stdio:'pipe',timeout:180000});
}
const w=JSON.parse(fs.readFileSync('/tmp/workflow.json')),c=JSON.parse(fs.readFileSync('/tmp/credentials.json'));
if(c.some(x=>!x.data||typeof x.data!=='object'))throw Error('DECRYPTED_CREDENTIAL_SHAPE');
console.log(JSON.stringify({workflow_ids:w.map(x=>x.id).sort(),credential_ids:c.map(x=>x.id).sort(),credential_decryption:true}));"""
    raw = command('run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
                  '--tmpfs', '/tmp:size=128m,mode=1777', '--tmpfs', '/home/node/.n8n:size=64m,mode=1777',
                  '--memory', '512m', '--cpus', '1', '--pids-limit', '128', '--cap-drop', 'ALL',
                  '--security-opt', 'no-new-privileges:true', '-e', 'N8N_DIAGNOSTICS_ENABLED=false',
                  '-e', 'N8N_VERSION_NOTIFICATIONS_ENABLED=false',
                  '--mount', f'type=bind,source={output},target=/backup,readonly',
                  '--entrypoint', 'node', image, '-e', code)
    result = json.loads(raw)
    if result != {**expected, 'credential_decryption': True}:
        raise ValueError('N8N_RESTORE_EXPORT_MISMATCH')
    return result


def qualify_restored_server(output, image, expected):
    # Network-none plus inactive copied workflows prevents restore from firing Main automations.
    code = r"""const fs=require('fs'),cp=require('child_process'),{DatabaseSync}=require('node:sqlite');
(async()=>{
const path='/home/node/.n8n/database.sqlite',key=JSON.parse(fs.readFileSync('/backup/n8n-key.json'));
fs.copyFileSync('/backup/n8n.sqlite',path);fs.copyFileSync('/backup/n8n-config','/home/node/.n8n/config');
fs.chmodSync('/home/node/.n8n/config',0o600);if(key.env_key)process.env.N8N_ENCRYPTION_KEY=key.env_key;
let db=new DatabaseSync(path);
const snapshot=()=>Object.fromEntries(['user','credentials_entity','execution_entity'].map(t=>[t,JSON.stringify(db.prepare('SELECT * FROM "'+t+'" ORDER BY id').all())]));
const workflows=()=>JSON.stringify(db.prepare('SELECT * FROM workflow_entity ORDER BY id').all().map(({active,activeVersionId,...row})=>row));
const workflowBefore=workflows(),before=snapshot();db.exec('UPDATE workflow_entity SET active=0');
if(db.prepare('PRAGMA table_info(workflow_entity)').all().some(x=>x.name==='activeVersionId'))db.exec('UPDATE workflow_entity SET activeVersionId=NULL');
db.close();const log=fs.openSync('/tmp/restored-server.log','w');let child;
try{
 child=cp.spawn('n8n',['start'],{stdio:['ignore',log,log]});
 let ready=false;
 for(let i=0;i<120;i++){
  if(child.exitCode!==null)throw Error('RESTORED_SERVER_EXITED');
  try{ready=(await fetch('http://127.0.0.1:5678/healthz/readiness',{signal:AbortSignal.timeout(500)})).status===200;}catch{}
  if(ready)break;await new Promise(r=>setTimeout(r,500));
 }
 if(!ready)throw Error('RESTORED_SERVER_NOT_READY');
 const health=(await fetch('http://127.0.0.1:5678/healthz')).status;
 const auth=(await fetch('http://127.0.0.1:5678/rest/workflows',{redirect:'manual'})).status;
 db=new DatabaseSync(path,{readOnly:true});const after=snapshot();
 const result={workflow_ids:db.prepare('SELECT id FROM workflow_entity ORDER BY id').all().map(x=>x.id),
  credential_ids:db.prepare('SELECT id FROM credentials_entity ORDER BY id').all().map(x=>x.id),
  active_workflows:db.prepare('SELECT count(*) AS n FROM workflow_entity WHERE active<>0').get().n,
  health_http:health,readiness_http:200,unauthenticated_workflows_http:auth,
  workflow_rows_unchanged:workflowBefore===workflows(),execution_rows_unchanged:before.execution_entity===after.execution_entity,
  users_unchanged:before.user===after.user,credential_rows_unchanged:before.credentials_entity===after.credentials_entity};
 db.close();console.log(JSON.stringify(result));
}finally{
 if(child&&child.exitCode===null){child.kill('SIGTERM');await Promise.race([new Promise(r=>child.once('exit',r)),new Promise(r=>setTimeout(r,5000))]);if(child.exitCode===null)child.kill('SIGKILL');}
 fs.closeSync(log);
}
})().catch(e=>{console.error(e.message);if(fs.existsSync('/tmp/restored-server.log'))console.error(fs.readFileSync('/tmp/restored-server.log','utf8'));process.exitCode=1});"""
    raw = command('run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
                  '--tmpfs', '/tmp:size=128m,mode=1777', '--tmpfs', '/home/node/.n8n:size=96m,mode=1777',
                  '--tmpfs', '/home/node/.cache:size=96m,mode=1777',
                  '--memory', '768m', '--cpus', '1', '--pids-limit', '128', '--cap-drop', 'ALL',
                  '--security-opt', 'no-new-privileges:true', '-e', 'N8N_DIAGNOSTICS_ENABLED=false',
                  '-e', 'N8N_VERSION_NOTIFICATIONS_ENABLED=false',
                  '--mount', f'type=bind,source={output},target=/backup,readonly',
                  '--entrypoint', 'node', image, '-e', code)
    result = json.loads(raw)
    required = {**expected, 'health_http': 200, 'readiness_http': 200,
                'unauthenticated_workflows_http': 401, 'active_workflows': 0,
                'workflow_rows_unchanged': True, 'execution_rows_unchanged': True, 'users_unchanged': True, 'credential_rows_unchanged': True}
    if result != required:
        raise ValueError('N8N_RESTORED_SERVER_OR_AUTH_MISMATCH')
    return result


def backup(manifest, output, *, qualify=True):
    rows = verify(manifest)
    output = private_path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    temporary = '/tmp/qldapm-online-backup-' + uuid.uuid4().hex + '.sqlite'
    code = r"""const fs=require('fs'),s=require('node:sqlite');
(async()=>{const path=process.argv[2],db=new s.DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
try{await s.backup(db,path);process.stdout.write(fs.readFileSync(path));}
finally{db.close();if(fs.existsSync(path))fs.unlinkSync(path);}})().catch(()=>{process.exitCode=1});"""
    files = {'n8n.sqlite': command('exec', '-i', 'qldapm-n8n-main', 'node', '-', temporary, data=code.encode()),
             'n8n-config': command('exec', 'qldapm-n8n-main', 'cat', '/home/node/.n8n/config'),
             'n8n-key.json': command('exec', 'qldapm-n8n-main', 'node', '-e',
                                    "process.stdout.write(JSON.stringify({env_key:process.env.N8N_ENCRYPTION_KEY||null}))"),
             'assets.tar': command('exec', 'qldapm-openproject-web-1', 'tar', '-C', '/var/openproject/assets', '-cf', '-', '.')}
    for name, data in files.items():
        (output / name).write_bytes(data)
    with sqlite3.connect((output/'n8n.sqlite').as_uri()+'?mode=ro&immutable=1', uri=True) as db:
        if db.execute('pragma quick_check').fetchone()[0] != 'ok':
            raise ValueError('N8N_BACKUP_INVALID')
        expected = {label: [row[0] for row in db.execute(f'select id from {table} order by id')]
                    for label, table in [('workflow_ids', 'workflow_entity'), ('credential_ids', 'credentials_entity')]}
    assets = validate_assets(files['assets.tar'])
    # Verify a second read has the same file contents, without extracting anything onto Main.
    if validate_assets(command('exec', 'qldapm-openproject-web-1', 'tar', '-C', '/var/openproject/assets', '-cf', '-', '.')) != assets:
        raise ValueError('MAIN_ASSETS_CHANGED_DURING_BACKUP')
    restore_assets(files['assets.tar'], output / 'restored-assets')
    restore = qualify_restore(output, rows['qldapm-n8n-main']['Image'], expected) if qualify else None
    restored_server = qualify_restored_server(output, rows['qldapm-n8n-main']['Image'], expected) if qualify else None
    verify(manifest)
    result = {'status': 'PASS_PRIVATE_N8N_CLI_RESTORE_AND_ASSETS_SNAPSHOT' if qualify else 'PASS_PRIVATE_N8N_ASSETS_SNAPSHOT_ONLY',
              'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in files.items()},
              'workflow_count': len(expected['workflow_ids']), 'credential_count': len(expected['credential_ids']),
              'credential_decryption': True if restore else 'NOT_RUN_SNAPSHOT_ONLY', 'isolated_restored_server': restored_server, 'asset_files': len(assets), 'asset_bytes': sum(x['bytes'] for x in assets.values()),
              'asset_private_restore': True,
              'images': manifest['containers'], 'main_native_writes': 0, 'staging_operations': False,
              'limits': ['Individual snapshots, not an atomic cross-service backup',
                         'Restored n8n CLI/server with copied automations disabled' if qualify else 'Scheduled snapshot; no repeated DR drill or credential decryption test',
                         'Assets restored and content-verified only in a new private directory; no Main restore',
                         'Full Qdrant restore remains BLOCKED_RESTORE_POLICY']}
    (output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = backup(json.loads(private_path(args.manifest).read_text()), args.output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
