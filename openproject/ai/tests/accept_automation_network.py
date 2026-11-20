"""Actual HTTP from n8n container, first to isolated candidate then primary after qualification."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from free_tier_staging import private_directory

PROBE = r"""
const http=require('http'), p=JSON.parse(require('fs').readFileSync(0));
const cases=[['valid','GET','/internal/automation/status',p.key,200],
 ['wrong_key','GET','/internal/automation/status','b'.repeat(64),401],
 ['missing_key','GET','/internal/automation/status','',401],
 ['business_api','POST','/api/v1/commands',p.key,403],
 ['human_bridge','POST','/internal/ui',p.key,403],
 ['actor_injection','GET','/internal/automation/status?actor_id=7',p.key,403],
 ['wrong_host','GET','/internal/automation/status',p.key,403]];
(async()=>{const results=[];for(const [name,method,path,key,status] of cases){
 const response=await new Promise((resolve,reject)=>{let data='';const req=http.request({hostname:p.host,port:8090,method,path,
 headers:{Host:name==='wrong_host'?'invalid.example':'gateway:8090',...(key?{'X-QLDAPM-Machine-Key':key}:{})}},r=>{
 r.on('data',c=>{data+=c;if(data.length>65536)req.destroy(Error('bounded'));});r.on('end',()=>resolve({status:r.statusCode,body:JSON.parse(data)}));
 });req.on('error',()=>reject(Error('network')));req.setTimeout(4000,()=>req.destroy(Error('timeout')));req.end();});
 if(response.status!==status)throw Error('case_'+name);
 if(name==='valid'&&(response.body.result.actor_id!==null||response.body.result.native_write_allowed!==false||response.body.result.model_calls!==0))throw Error('authority');
 results.push({case:name,status:response.status});}
 let signed;
 if(p.commands){
 const crypto=require('crypto'), secret=crypto.createHmac('sha256',p.key).update('QLDAPM-AUTOMATION-SIGNING-V1').digest('hex');
 const doc={version:1,kind:'status',request_key:crypto.randomUUID(),nonce:crypto.randomUUID(),issued_at:Math.floor(Date.now()/1000)};
 const sign=d=>crypto.createHmac('sha256',secret).update('QLDAPM-AUTOMATION-COMMAND-V1\nPOST\n/internal/automation/commands\n1\n'+d.kind+'\n'+d.request_key+'\n'+d.nonce+'\n'+d.issued_at).digest('hex');
 const send=(d,sig=sign(d))=>new Promise((resolve,reject)=>{let data='';const body=JSON.stringify(d);
 const req=http.request({hostname:p.host,port:8090,method:'POST',path:'/internal/automation/commands',headers:{Host:'gateway:8090',
 'X-QLDAPM-Machine-Key':p.key,'X-QLDAPM-Command-Signature':sig,'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)}},r=>{
 r.on('data',c=>{data+=c;if(data.length>65536)req.destroy(Error('bounded'));});r.on('end',()=>resolve({status:r.statusCode,body:JSON.parse(data)}));
 });req.on('error',()=>reject(Error('network')));req.setTimeout(4000,()=>req.destroy(Error('timeout')));req.end(body);});
 const replies=await Promise.all(Array.from({length:12},()=>send(doc)));
 if(replies.some(r=>r.status!==200)||new Set(replies.map(r=>r.body.result.run_id)).size!==1)throw Error('duplicate');
 const same=await send({...doc,nonce:crypto.randomUUID()});if(same.status!==200||same.body.result.run_id!==replies[0].body.result.run_id)throw Error('receipt');
 const failures=[['nonce_replay',{...doc,request_key:crypto.randomUUID()},null,403],
 ['expired',{...doc,nonce:crypto.randomUUID(),issued_at:doc.issued_at-61},null,403],
 ['future',{...doc,nonce:crypto.randomUUID(),issued_at:doc.issued_at+30},null,403],
 ['invalid_signature',{...doc,nonce:crypto.randomUUID()},'a'.repeat(64),403],
 ['actor_injection',{...doc,actor_id:7},null,422],['business_kind',{...doc,kind:'create_work_package'},null,422]];
 for(const [name,d,sig,status] of failures){const r=await send(d,sig||sign(d));if(r.status!==status)throw Error(name);results.push({case:name,status:r.status});}
 signed={concurrent_duplicates:12,one_run:true,same_receipt_on_fresh_nonce:true,authority:'machine',actor_id:replies[0].body.result.actor_id};
 if(signed.actor_id!==null||replies[0].body.result.model_calls!==0||replies[0].body.result.native_write_allowed!==false)throw Error('authority');
 }
 process.stdout.write(JSON.stringify({passed:true,cases:results,...(signed?{signed_commands:signed}:{}),caller:'actual_n8n_container',business_writes:0,model_calls:0}));
})().catch(()=>{process.stdout.write(JSON.stringify({passed:false,error:'NETWORK_SCOPE_ACCEPTANCE_FAILED'}));process.exitCode=1;});
"""


def docker(*args, payload=None):
    result = subprocess.run(['docker', *args], input=payload, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError('AUTOMATION_NETWORK_OPERATOR_FAILED:' + args[0])
    return result.stdout.decode().strip()


def accept(image, primary, commands=False):
    n8n = json.loads(docker('inspect', 'qldapm-ai-stage-n8n-1'))[0]
    assert n8n['Image'] == 'sha256:dd580fe1ab6e99e85bc66f2acf8bc8c5e9409fbe61b2e2803c5024403ef52833'
    assert set(n8n['NetworkSettings']['Networks']) == {'qldapm-ai-stage_automation'}
    assert not n8n['HostConfig']['PortBindings']
    if primary:
        info = json.loads(docker('inspect', 'qldapm-ai-stage-staging-gateway-1'))[0]
        assert info['Image'] == image and info['Config']['Labels']['com.docker.compose.project'] == 'qldapm-ai-stage'
        key = (Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/stage-ai/automation.key').read_text()
        host, name = 'gateway', None
    else:
        name = host = 'qldapm-p04-machine-' + str(uuid.uuid4())
        root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator' / name
        private_directory(root)
        key = secrets.token_hex(32)
        (root / 'automation.key').write_text(key)
        (root / 'config.json').write_text(json.dumps({'project_id': 3, 'users': {}, 'hosts': ['gateway:8090'],
                                                    'openproject_url': 'http://blocked.invalid'}))
        docker('run', '-d', '--name', name, '--label', 'qldapm.acceptance.machine=' + name,
               '--network', 'qldapm-ai-stage_automation', '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges:true', '--memory', '384m', '--pids-limit', '64',
               '--tmpfs', '/tmp:size=64m,mode=1777', '--env', 'QLDAPM_AI_RUNTIME=/state',
               '--mount', 'type=bind,src=' + str(root) + ',dst=/state', image)
    try:
        if name:
            docker('exec', name, 'python', '-c', "import time,urllib.request\nfor i in range(30):\n try:\n  urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8090/health',headers={'Host':'gateway:8090'}),timeout=1);break\n except OSError:time.sleep(1)\nelse:raise RuntimeError('NOT_READY')")
        result = json.loads(docker('exec', '-i', 'qldapm-ai-stage-n8n-1', 'node', '-e', PROBE,
                                   payload=json.dumps({'host': host, 'key': key, 'commands': commands}).encode()))
        assert result['passed']
        result.update({'image': image, 'target': 'primary' if primary else 'isolated_candidate',
                       'native_credentials_shared': False, 'n8n_private_network_only': True})
        return result
    finally:
        if name:
            info = json.loads(docker('inspect', name))[0]
            assert info['Image'] == image and info['Config']['Labels'].get('qldapm.acceptance.machine') == name
            docker('stop', '--time', '30', name)
            docker('rm', name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('output', type=Path)
    parser.add_argument('--primary', action='store_true')
    parser.add_argument('--commands', action='store_true')
    args = parser.parse_args()
    try:
        result = accept(args.image, args.primary, args.commands)
        args.output.write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'private_details_redacted': True}))
        raise SystemExit(1)
