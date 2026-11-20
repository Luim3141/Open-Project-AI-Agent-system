"""Host operator only: pinned Main containers, graceful controls and private metadata backup."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time

TARGETS = {
    'qldapm-openproject-db-1':('qldapm-openproject','db'),
    'qldapm-openproject-cache-1':('qldapm-openproject','cache'),
    'qldapm-qdrant':(None,None),
    'qldapm-openproject-hocuspocus-1':('qldapm-openproject','hocuspocus'),
    'qldapm-openproject-web-1':('qldapm-openproject','web'),
    'qldapm-openproject-worker-1':('qldapm-openproject','worker'),
    'qldapm-openproject-cron-1':('qldapm-openproject','cron'),
    'qldapm-ai-gateway-1':('qldapm-ai','gateway'),
    'qldapm-n8n-main':(None,None),
    'qldapm-openproject-proxy-1':('qldapm-openproject','proxy'),
}
PRIVATE_ROOT = Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'QLDAPM/openproject-ai/operator'


def command(*args, data=None):
    result=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=600)
    if result.returncode:raise RuntimeError('MAIN_DOCKER_COMMAND_FAILED')
    return result.stdout


def inspect(name):
    if name not in TARGETS:raise ValueError('MAIN_TARGET_DENIED')
    return json.loads(command('inspect',name))[0]


def identity(name, row):
    project,service=TARGETS[name];labels=row['Config'].get('Labels') or {}
    if (row['Name']!='/'+name or not re.fullmatch('[a-f0-9]{64}',row['Id']) or
            not re.fullmatch('sha256:[a-f0-9]{64}',row['Image']) or
            project and (labels.get('com.docker.compose.project'),labels.get('com.docker.compose.service'))!=(project,service)):
        raise ValueError('MAIN_CONTAINER_IDENTITY_MISMATCH')


def verify(manifest):
    if manifest.get('version')!=1 or manifest.get('project_id')!=5 or set(manifest.get('containers',{}))!=set(TARGETS):
        raise ValueError('EXACT_MAIN_MANIFEST_REQUIRED')
    rows={name:inspect(name) for name in TARGETS}
    for name,row in rows.items():
        identity(name,row)
        if manifest['containers'][name]!={'id':row['Id'],'image':row['Image']}:
            raise ValueError('MAIN_MANIFEST_STALE_REVIEW_CURRENT_RUNTIME')
    return rows


def work_state():
    code="""import hashlib,json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
unknown=d.execute("select * from requests where state!='done' order by actor,key").fetchall()
active=sum(d.execute(sql).fetchone()[0] for sql in ["select count(*) from ai_queue where state!='finished'","select count(*) from knowledge_sync where state!='verified'"])
print(json.dumps({'active':active,'historical_pending':len(unknown),'unknown_sha256':hashlib.sha256(json.dumps(unknown,separators=(',',':')).encode()).hexdigest()}))"""
    return json.loads(command('exec','qldapm-ai-gateway-1','python','-c',code))


def capture():
    rows={name:inspect(name) for name in TARGETS}
    for name,row in rows.items():identity(name,row)
    return {'version':1,'project_id':5,'containers':{name:{'id':row['Id'],'image':row['Image']} for name,row in rows.items()},**work_state()}


def status(manifest):
    rows=verify(manifest)
    return {'project_id':5,'containers':{name:{'image':row['Image'],'state':row['State']['Status'],
        'health':row['State'].get('Health',{}).get('Status','NOT_CONFIGURED')} for name,row in rows.items()},
        'staging_operations':False,'scope':'Container state/health only; business acceptance is separate'}


def plan(action, manifest):
    if action not in {'start','stop'}:raise ValueError('MAIN_OPERATION_DENIED')
    verify(manifest)
    return {'action':action,'containers':list(TARGETS) if action=='start' else list(reversed(TARGETS)),
        'staging_operations':False,'remove_volumes':False,'restart_docker':False}


def apply(action, manifest):
    result=plan(action,manifest);rows=verify(manifest)
    if action=='stop':
        work=work_state()
        if work['active'] or work['unknown_sha256']!=manifest.get('unknown_sha256'):
            raise ValueError('MAIN_ACTIVE_OR_NEW_UNKNOWN_WORK_HOLD')
    changed=[]
    for name in result['containers']:
        running=rows[name]['State']['Status']=='running'
        if action=='start' and not running:
            command('start',name);changed.append(name)
            for _ in range(120):
                current=inspect(name);identity(name,current)
                if current['Id']!=rows[name]['Id'] or current['Image']!=rows[name]['Image']:raise ValueError('MAIN_IDENTITY_CHANGED_DURING_START')
                if current['State']['Status']=='running' and current['State'].get('Health',{}).get('Status','healthy')=='healthy':break
                time.sleep(1)
            else:raise RuntimeError('MAIN_START_HEALTH_TIMEOUT')
        elif action=='stop' and running:
            command('stop','--time','60',name);changed.append(name)
    return {**result,'changed':changed,'native_replay':False}


def private_path(path):
    path=Path(path).resolve()
    if not path.is_relative_to(PRIVATE_ROOT.resolve()) or path==PRIVATE_ROOT.resolve():
        raise ValueError('PRIVATE_OPERATOR_SUBDIRECTORY_REQUIRED')
    return path


def backup(manifest, output):
    verify(manifest);output=private_path(output);output.mkdir(mode=0o700,parents=True,exist_ok=False)
    files={'postgres.dump':command('exec','qldapm-openproject-db-1','pg_dump','-U','postgres','-Fc','openproject')}
    for name in ['gateway','knowledge']:
        code=f"import sqlite3,sys;s=sqlite3.connect('file:/state/{name}.sqlite?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);sys.stdout.buffer.write(d.serialize())"
        files[name+'.sqlite']=command('exec','qldapm-ai-gateway-1','python','-c',code)
    for name,data in files.items():(output/name).write_bytes(data)
    for name in ['gateway','knowledge']:
        with sqlite3.connect((output/(name+'.sqlite')).as_uri()+'?mode=ro&immutable=1',uri=True) as db:
            if db.execute('pragma quick_check').fetchone()[0]!='ok':raise ValueError('MAIN_SQLITE_BACKUP_INVALID')
    command('exec','-i','qldapm-openproject-db-1','pg_restore','--list',data=files['postgres.dump'])
    result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_NATIVE_AND_SQLITE_SNAPSHOT',
        'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()},
        'images':manifest['containers'],'scope':'Consistent individual PG and SQLite snapshots, not an atomic cross-service backup',
        'limitations':['Qdrant full restore remains BLOCKED_RESTORE_POLICY','n8n/assets/config/keys require their separately preserved private artifacts'],
        'native_writes':0,'staging_operations':False}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['capture','status','plan-start','plan-stop','start','stop','backup'])
    parser.add_argument('--manifest',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.action=='capture':
        if args.output is None:parser.error('capture needs a new private --output manifest path')
        output=private_path(args.output);output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with output.open('x') as stream:json.dump(capture(),stream,indent=2)
        result={'status':'PINNED_CURRENT_MAIN_MANIFEST','path':str(output)}
    else:
        if args.manifest is None:parser.error('--manifest is required')
        manifest=json.loads(private_path(args.manifest).read_text())
        if args.action=='status':result=status(manifest)
        elif args.action.startswith('plan-'):result=plan(args.action[5:],manifest)
        elif args.action=='backup':
            if args.output is None:parser.error('backup needs a new private --output directory')
            result=backup(manifest,args.output)
        else:result=apply(args.action,manifest)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
