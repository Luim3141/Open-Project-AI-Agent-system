import hashlib, json, os, subprocess, time, urllib.request
from pathlib import Path

out = Path(__file__).parent
private = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/post30218-n8n-redaction'
private.mkdir(parents=True, exist_ok=False)
image = 'sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'
old_name = 'qldapm-n8n-main-pre-overwrite-redaction-20261101'

def docker(*args, timeout=180):
    p = subprocess.run(['docker', *args], capture_output=True, timeout=timeout)
    if p.returncode:
        (private/'failure.log').write_bytes(p.stderr)
        raise RuntimeError('Docker command failed; details stored privately')
    return p.stdout

def inspect(name):
    return json.loads(docker('inspect', name))[0]

old = inspect('qldapm-n8n-main')
assert old['Image'] == 'sha256:9e8d3393ca28a6603f3890218aeb3bb280952262c134e230b033380a2fd54e32'
assert subprocess.run(['docker','inspect',old_name],capture_output=True).returncode != 0
candidate = json.loads(docker('image','inspect',image))[0]['Config']
for key in ['Entrypoint','Cmd','User','WorkingDir']:
    assert candidate.get(key) == old['Config'].get(key), key
envfile = private/'preserved.env'
assert all('\n' not in v and '\r' not in v for v in old['Config']['Env'])
envfile.write_text('\n'.join(old['Config']['Env'])+'\n')
create = ['create','--name','qldapm-n8n-main','--pull','never','--env-file',str(envfile),
          '--network',old['HostConfig']['NetworkMode'],'--restart',old['HostConfig']['RestartPolicy']['Name']]
for bind in old['HostConfig']['Binds']: create += ['--volume',bind]
for port, bindings in old['HostConfig']['PortBindings'].items():
    for binding in bindings: create += ['--publish',binding['HostIp']+':'+binding['HostPort']+':'+port]
for key,value in old['Config'].get('Labels',{}).items(): create += ['--label',key+'='+value]
create += [image]
renamed = False
try:
    docker('stop','--time','45','qldapm-n8n-main')
    data = docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/data,readonly','--entrypoint','tar',image,'-C','/data','-cf','-','.',timeout=240)
    (private/'n8n-cold-volume.tar').write_bytes(data)
    docker('rename','qldapm-n8n-main',old_name); renamed = True
    docker(*create)
    new = inspect('qldapm-n8n-main')
    assert new['Image'] == image
    for key in ['Env','Entrypoint','Cmd','User','WorkingDir','Labels','ExposedPorts']:
        assert new['Config'].get(key) == old['Config'].get(key), key
    for key,value in old['HostConfig'].items():
        if key in ['Dns','OomKillDisable'] and not value and not new['HostConfig'].get(key): continue
        assert new['HostConfig'].get(key) == value, key
    for network,settings in old['NetworkSettings']['Networks'].items():
        if network == old['HostConfig']['NetworkMode']: continue
        args=['network','connect']
        for alias in settings.get('Aliases') or []:
            if alias not in {old['Id'],old['Id'][:12],'qldapm-n8n-main'}: args += ['--alias',alias]
        docker(*args,network,'qldapm-n8n-main')
    docker('start','qldapm-n8n-main')
    for _ in range(90):
        try:
            with urllib.request.urlopen('http://127.0.0.1:5679/healthz/readiness',timeout=2) as response:
                if response.status == 200: break
        except Exception: time.sleep(1)
    else: raise RuntimeError('N8N_READINESS_TIMEOUT')
    (out/'n8n-redaction-deployment.json').write_text(json.dumps({'status':'READY','image':image,'previous_container':old_name,'cold_backup_sha256':hashlib.sha256(data).hexdigest(),'workflow_changed':False},indent=2)+'\n')
    print('N8N_CANDIDATE_READY; old container and cold backup preserved')
except Exception:
    if renamed:
        if subprocess.run(['docker','inspect','qldapm-n8n-main'],capture_output=True).returncode == 0:
            subprocess.run(['docker','stop','--time','15','qldapm-n8n-main'],capture_output=True)
            docker('rename','qldapm-n8n-main','qldapm-n8n-main-failed-overwrite-redaction-20261101')
        docker('rename',old_name,'qldapm-n8n-main')
    docker('start','qldapm-n8n-main')
    raise
