"""Metadata-only reconciliation of an already healthy tunnel. No start/stop/recreate/fault/network probe."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

AI=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(AI))
from jira_sync_backup import operator_lease
from free_tier_staging import private_directory

ACTIVE='sha256:a80f54e29918ec66c82cdc7ad8fd9a65e3082e59825c0356d5737916959884c6'


def checked_record(record,info,source_hash,actual_hash):
    labels=info['Config']['Labels'];host=info['HostConfig']
    if (record.get('quick_tunnel') is not True or info['Image']!=ACTIVE or
        labels.get('com.docker.compose.project')!='qldapm-ai-stage' or labels.get('com.docker.compose.service')!='quick-tunnel' or
        not info['State']['Running'] or info['State'].get('Health',{}).get('Status')!='healthy' or
        info.get('Mounts') or host['RestartPolicy']['Name']!='unless-stopped' or not host['ReadonlyRootfs'] or
        set(info['NetworkSettings']['Networks'])!={'qldapm-ai-stage_stage-front'} or source_hash!=actual_hash):
        raise ValueError('TUNNEL_IDENTITY_OR_SOURCE_NOT_VERIFIED')
    return {**record,'quick_tunnel_image':info['Image'],'quick_tunnel_supervisor_sha256':source_hash}


def main():
    def docker(*args):return subprocess.check_output(['docker',*args],stderr=subprocess.DEVNULL,timeout=30).decode().strip()
    out=AI.parents[1]/'docs/ai-multi-agent-upgrade/remaining-development'
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
    path=runtime/'operator/local-runtime/stage-runtime.json'
    before=json.loads(docker('inspect','qldapm-ai-stage-quick-tunnel-1'))[0]
    source=hashlib.sha256((AI/'automation/quick_tunnel_supervisor.sh').read_bytes()).hexdigest()
    candidates=json.loads((out/'candidate-images.json').read_text())
    proofs={}
    for name,image in [('live',before['Image']),('rebuilt',candidates['quick-tunnel']['image'])]:
        proofs[name]={'image':image,
            'script_sha256':docker('run','--rm','--network','none','--entrypoint','sha256sum',image,'/usr/local/bin/quick_tunnel_supervisor.sh').split()[0],
            'binary_sha256':docker('run','--rm','--network','none','--entrypoint','sha256sum',image,'/usr/local/bin/cloudflared').split()[0],
            'version':docker('run','--rm','--network','none','--entrypoint','cloudflared',image,'--version')}
    assert proofs['live']['script_sha256']==proofs['rebuilt']['script_sha256']==source
    assert proofs['live']['binary_sha256']==proofs['rebuilt']['binary_sha256'] and '2026.10.0' in proofs['live']['version']
    with operator_lease('staging'):
        old=json.loads(path.read_text())
        new=checked_record(old,before,source,proofs['live']['script_sha256'])
        backup=runtime/'operator/local-runtime'/('before-tunnel-metadata-'+str(time.time_ns()))
        private_directory(backup)
        (backup/'stage-runtime.json').write_bytes(path.read_bytes())
        temp=path.with_suffix('.rd.tmp');temp.write_text(json.dumps(new,indent=2));temp.replace(path)
    after=json.loads(docker('inspect','qldapm-ai-stage-quick-tunnel-1'))[0]
    for key in ('Id','Image','RestartCount'):assert before[key]==after[key]
    assert before['State']['StartedAt']==after['State']['StartedAt']
    result={'passed':True,'operation':'METADATA_ONLY','proofs':proofs,'old_manifest_image':old['quick_tunnel_image'],
        'new_manifest_image':new['quick_tunnel_image'],'container_id_unchanged':True,'restart_unchanged':True,
        'source_pinned_vendor_digests':True,'secret_mounts':0,'docker_socket':False,'public_restart_or_fault':False}
    (out/'quick-tunnel-reconciliation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
