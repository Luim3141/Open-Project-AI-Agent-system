"""Restore DPAPI tar to an isolated tmpfs and report aggregate checks only."""
import io
import json
import re
import subprocess
import sys
import tarfile
import uuid
from pathlib import PurePosixPath

from inspect_backup import unprotect, private

archive = unprotect(private / 'n8n-cold-volume.tar.dpapi')
env_text = unprotect(private / 'preserved.env.dpapi').decode()
env = dict(line.split('=', 1) for line in env_text.splitlines() if '=' in line)
assert env.get('N8N_ENCRYPTION_KEY')
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:*') as tar:
    names = [m.name.removeprefix('./') for m in tar]
    assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names)
    assert all(n in names for n in ('database.sqlite', 'database.sqlite-wal', 'database.sqlite-shm', 'config'))
    assert all(m.isfile() or m.isdir() for m in tar.getmembers())

name = 'qldapm-n8n-restore-drill-' + uuid.uuid4().hex[:12]
image = 'sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'


def docker(args, data=None):
    p = subprocess.run(['docker', *args], input=data, capture_output=True, timeout=180)
    if p.returncode:
        codes = sorted(set(re.findall(r'\b(?:SQLITE_[A-Z_]+|MODULE_NOT_FOUND|EACCES|ENOENT|SyntaxError|TypeError|ReferenceError)\b', p.stderr.decode(errors='replace'))))
        try:
            details = json.loads(p.stdout)
            safe = {k: details.get(k) for k in ('error', 'stage', 'code') if k in details}
        except (ValueError, TypeError):
            safe = {}
        raise RuntimeError('DOCKER_FAILED: ' + args[0] + ' ' + json.dumps({'codes': codes, 'diagnostic': safe}))
    return p.stdout


runner = r'''
const fs=require('fs'), cp=require('child_process');
const crypto=require('crypto');
const data=JSON.parse(fs.readFileSync(0,'utf8'));
const env={...process.env,...data.env, HOME:'/tmp/restore', N8N_USER_FOLDER:'/tmp/restore',
  N8N_DIAGNOSTICS_ENABLED:'false', N8N_VERSION_NOTIFICATIONS_ENABLED:'false'};
const sqlite=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));
const db=new sqlite.Database('/tmp/restore/.n8n/database.sqlite');
const query=(sql)=>new Promise((resolve,reject)=>db.all(sql,(err,rows)=>err?reject(err):resolve(rows)));
let stage='integrity';
(async()=>{
  const integrity=await query('PRAGMA integrity_check');
  stage='workflows';
  const workflows=await query('SELECT count(*) AS n, sum(active) AS active FROM workflow_entity');
  stage='credentials';
  const creds=await query('SELECT count(*) AS n FROM credentials_entity');
  const beforeCipher=await query('SELECT id,data FROM credentials_entity ORDER BY id');
  stage='owners';
  const owners=await query("SELECT count(*) AS n FROM user WHERE roleSlug='global:owner'");
  stage='published_and_sharing';
  const published=await query('SELECT count(*) AS n FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId AND h.workflowId=w.id WHERE w.active=1');
  const sharing=await query('SELECT count(*) AS n FROM shared_workflow s JOIN workflow_entity w ON w.id=s.workflowId JOIN project p ON p.id=s.projectId');
  stage='decrypt';
  const version=cp.spawnSync('n8n',['--version'],{env,encoding:'utf8',timeout:60000});
  const exp=cp.spawnSync('n8n',['export:credentials','--all','--decrypted'],{env,encoding:'utf8',timeout:120000,maxBuffer:20*1024*1024});
  let exported=null, original=null, migration=null;
  if(exp.status===0){try {const a=exp.stdout.indexOf('['), b=exp.stdout.lastIndexOf(']'); const v=JSON.parse(exp.stdout.slice(a,b+1)); if(Array.isArray(v)){original=v;exported=v.length;}}catch{}}
  if(data.migrate && original && original.length===creds[0].n){
    const file='/tmp/restore/credentials-plain.json';
    fs.writeFileSync(file,JSON.stringify(original),{mode:0o600});
    const configPath='/tmp/restore/.n8n/config', config=JSON.parse(fs.readFileSync(configPath));
    if(config.encryptionKey!==env.N8N_ENCRYPTION_KEY) throw new Error('KEY_CONFIGURATION_MISMATCH');
    const key=crypto.randomBytes(32).toString('hex');config.encryptionKey=key;
    fs.writeFileSync(configPath,JSON.stringify(config),{mode:0o600});
    const migratedEnv={...env,N8N_ENCRYPTION_KEY:key};
    const imp=cp.spawnSync('n8n',['import:credentials','--input='+file],{env:migratedEnv,encoding:'utf8',timeout:120000,maxBuffer:20*1024*1024});
    const verify=imp.status===0?cp.spawnSync('n8n',['export:credentials','--all','--decrypted'],{env:migratedEnv,encoding:'utf8',timeout:120000,maxBuffer:20*1024*1024}):null;
    let same=false;
    if(verify && verify.status===0){try{
      const a=verify.stdout.indexOf('['),b=verify.stdout.lastIndexOf(']');const after=JSON.parse(verify.stdout.slice(a,b+1));
      const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
      const sort=x=>x.slice().sort((a,b)=>String(a.id).localeCompare(String(b.id)));
      same=JSON.stringify(canonical(sort(original)))===JSON.stringify(canonical(sort(after)));
    }catch{}}
    const afterCipher=await query('SELECT id,data FROM credentials_entity ORDER BY id');
    const err=verify?(verify.stderr+'\n'+verify.stdout).toLowerCase():'';
    const imported=(imp.stdout+'\n'+imp.stderr).match(/Successfully imported (\d+) credential/i);
    migration={import_exit:imp.status,import_reported_count:imported?Number(imported[1]):null,
      import_reported_error:(imp.stdout+'\n'+imp.stderr).includes('An error occurred while importing credentials'),
      ciphertext_changed_count:beforeCipher.filter((x,i)=>afterCipher[i] && x.data!==afterCipher[i].data).length,
      export_exit:verify?verify.status:null,credentials_equal:same,
      error_flags:{decrypt:err.includes('decrypt'),encryption_key:err.includes('encryption key'),
        sqlite_busy:err.includes('sqlite_busy'),invalid:err.includes('invalid'),mismatch:err.includes('mismatch'),
        no_data:err.includes('no data')}};
  }
  console.log(JSON.stringify({integrity:integrity[0].integrity_check, workflows:workflows[0], credentials:creds[0].n,
    owners:owners[0].n, published_workflows:published[0].n, valid_shared_workflows:sharing[0].n,
    n8n_version:version.status===0?version.stdout.trim():'ERROR',
    credential_export_exit:exp.status, decrypted_export_count:exported, migration}));
  db.close();
})().catch(e=>{console.log(JSON.stringify({error:'CLONE_QUERY_FAILED',stage,code:/^SQLITE_[A-Z_]+$/.test(e.code||'')?e.code:null}));process.exitCode=1;db.close()});
'''
result = {'container': name, 'network': 'none', 'status': 'FAILED'}
try:
    docker(['run', '-d', '--pull', 'never', '--name', name, '--network', 'none', '--read-only',
            '--tmpfs', '/tmp:rw,uid=1000,gid=1000,mode=0700,size=256m',
            '--entrypoint', '/bin/sh', image, '-c', 'mkdir -p /tmp/restore/.n8n; sleep 1800'])
    docker(['exec', '-i', name, 'tar', '-C', '/tmp/restore/.n8n', '-xf', '-'], archive)
    report = json.loads(docker(['exec', '-i', name, 'node', '-e', runner], json.dumps({'env': env,'migrate':'--migration' in sys.argv}).encode()))
    result.update(report)
    result['status'] = 'PASS' if (report.get('integrity') == 'ok' and report.get('credential_export_exit') == 0
        and report.get('decrypted_export_count') == report.get('credentials')
        and report.get('published_workflows') == report.get('workflows', {}).get('active')
        and report.get('valid_shared_workflows', 0) > 0) else 'INCOMPLETE'
    if '--migration' in sys.argv and not (report.get('migration') or {}).get('credentials_equal'):
        result['status'] = 'MIGRATION_FAILED'
finally:
    # The container is retained for audit; stopping discards only its ephemeral tmpfs.
    subprocess.run(['docker', 'stop', '--time', '5', name], capture_output=True, timeout=30)
    print(json.dumps(result))
if result['status'] != 'PASS':
    sys.exit(1)
