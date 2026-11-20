"""Independent, read-only recheck. No login, OTP verification, rotation or service change."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
LOGINS=['ba-pm','pm','be','fe','qa','stage-owner']
SQL="""SELECT json_build_object(
 'identity',(SELECT row_to_json(t) FROM (SELECT current_database() dbname,
   (SELECT oid::text FROM pg_database WHERE datname=current_database()) db_oid,
   (SELECT system_identifier::text FROM pg_control_system()) cluster_id,
   inet_server_addr()::text server_address,inet_server_port() server_port,
   current_setting('transaction_read_only') transaction_read_only) t),
 'users',(SELECT coalesce(json_agg(t),'[]'::json) FROM
   (SELECT id,login,status,admin FROM users WHERE login IN
    ('ba-pm','pm','be','fe','qa','stage-owner') OR id IN (5,13) ORDER BY id) t),
 'devices',(SELECT coalesce(json_agg(t),'[]'::json) FROM
   (SELECT d.id,d.user_id,u.login,d.channel,d.active,d."default",d.created_at,d.updated_at
    FROM two_factor_authentication_devices d LEFT JOIN users u ON u.id=d.user_id
    WHERE d.id BETWEEN 23 AND 40 OR u.login IN ('ba-pm','pm','be','fe','qa','stage-owner')
    ORDER BY d.id) t),
 'counts',json_build_object(
   'old_23_28',(SELECT count(*) FROM two_factor_authentication_devices WHERE id BETWEEN 23 AND 28),
   'old_active',(SELECT count(*) FROM two_factor_authentication_devices WHERE id BETWEEN 23 AND 28 AND active),
   'new_35_40',(SELECT count(*) FROM two_factor_authentication_devices WHERE id BETWEEN 35 AND 40),
   'user_13',(SELECT count(*) FROM users WHERE id=13)))"""

def command(args, payload=None, timeout=35):
    p=subprocess.run(args,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=timeout,cwd=ROOT)
    if p.returncode:raise RuntimeError(f'RECHECK_COMMAND_FAILED_EXIT_{p.returncode}')
    return p.stdout

def save(name,document):
    (OUT/name).write_text(json.dumps(document,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    names=['qldapm-ai-stage-db-1','qldapm-ai-stage-staging-web-1','qldapm-ai-stage-staging-gateway-1','qldapm-ai-stage-quick-tunnel-1','qldapm-ai-stage-n8n-editor-1']
    raw=json.loads(command(['docker','inspect',*names]))
    safe=[]
    for c in raw:
        labels=c['Config'].get('Labels',{})
        env=dict(v.split('=',1) for v in c['Config'].get('Env',[]) if '=' in v)
        db=urlsplit(env['DATABASE_URL']) if 'DATABASE_URL' in env else None
        safe.append({'name':c['Name'].lstrip('/'),'id':c['Id'],'image':c['Image'],'image_ref':c['Config']['Image'],
          'compose_project':labels.get('com.docker.compose.project'),'compose_service':labels.get('com.docker.compose.service'),
          'compose_files':labels.get('com.docker.compose.project.config_files'),'compose_workdir':labels.get('com.docker.compose.project.working_dir'),
          'state':c['State']['Status'],'health':c['State'].get('Health',{}).get('Status'),'started_at':c['State']['StartedAt'],'restart_count':c['RestartCount'],
          'networks':{k:{'ip':v.get('IPAddress'),'aliases':v.get('Aliases')} for k,v in c['NetworkSettings']['Networks'].items()},
          'mounts':[{k:m.get(k) for k in ['Type','Name','Source','Destination','RW']} for m in c['Mounts']],
          'database_endpoint':{'hostname':db.hostname,'port':db.port or 5432,'database':db.path.lstrip('/')} if db else None})
    assert all(c['compose_project']=='qldapm-ai-stage' for c in safe),'WRONG_PROJECT'
    save('target-identity.json',{'at':datetime.now(timezone.utc).isoformat(),'docker_context':command(['docker','context','show']).strip(),'containers':safe})
    db=json.loads(command(['docker','exec','-e','PGOPTIONS=-c default_transaction_read_only=on','qldapm-ai-stage-db-1',
        'psql','-X','-U','postgres','-d','openproject','-At','-v','ON_ERROR_STOP=1','-c',SQL]))
    save('postgres-direct.json',db)
    credential_path=PRIVATE/'secrets/staging_totp_secrets.json'
    creds=json.loads(credential_path.read_text(encoding='utf-8-sig'))
    payload={login:creds[login]['totp_secret'] for login in LOGINS}
    ruby="""require 'json'
sql = %s
db = JSON.parse(ActiveRecord::Base.connection.select_value(sql))
secrets = JSON.parse(STDIN.read)
matches = secrets.map do |login,secret|
  user = User.find_by(login: login)
  devices = user ? TwoFactorAuthentication::Device::Totp.where(user_id: user.id).to_a : []
  {login: login, user_id: user&.id, saved_key_matching_device_ids: devices.select { |d| d.otp_secret == secret }.map(&:id),
   active_device_ids: devices.select(&:active?).map(&:id), default_device_ids: devices.select(&:default?).map(&:id)}
end
puts 'TOTP_RECHECK_RESULT=' + JSON.generate({database: db, private_saved_key_matches: matches})
""" % json.dumps(SQL)
    response=command(['docker','exec','-i','-e','PGOPTIONS=-c default_transaction_read_only=on','qldapm-ai-stage-staging-web-1',
        'bundle','exec','rails','runner',ruby],payload=json.dumps(payload),timeout=100)
    records=[line.removeprefix('TOTP_RECHECK_RESULT=') for line in response.splitlines() if line.startswith('TOTP_RECHECK_RESULT=')]
    if len(records)!=1:raise ValueError('RAILS_RESULT_MISSING_NO_RAW_OUTPUT')
    rails=json.loads(records[0]);save('rails-actual-connection.json',rails)
    keys=['cluster_id','db_oid','dbname']
    assert all(db['identity'][k]==rails['database']['identity'][k] for k in keys),'DATABASE_MISMATCH'
    assert db['identity']['transaction_read_only']=='on' and rails['database']['identity']['transaction_read_only']=='on'
    assert db['users']==rails['database']['users'] and db['devices']==rails['database']['devices']
    current=OUT.parent/'runtime.json'
    before=json.loads(current.read_text())['containers']
    unchanged=[{'name':c['name'],'same_image':c['image']==next(x for x in before if x['name']==c['name'])['image'],
        'same_started_at':c['started_at']==next(x for x in before if x['name']==c['name'])['started'],
        'same_restart_count':c['restart_count']==next(x for x in before if x['name']==c['name'])['restart_count']} for c in safe]
    save('preservation.json',unchanged)
    def canonical(value):
        import re
        p=value.replace('\\','/').lower()
        p=re.sub('/+','/',p)
        p=re.sub(r'^/run/desktop/mnt/host/([a-z])/',r'\1:/',p)
        return p.rstrip('/')
    f=canonical(str(credential_path))
    mounts=[{'container':c['name'],'destination':m['Destination']} for c in safe for m in c['mounts']
            if f==canonical(m['Source']) or f.startswith(canonical(m['Source'])+'/')]
    save('secret-file-metadata.json',{'path':str(credential_path),'exists':credential_path.is_file(),
        'bytes':credential_path.stat().st_size,'modified_at':datetime.fromtimestamp(credential_path.stat().st_mtime,timezone.utc).isoformat(),
        'legacy_access_file_exists':(PRIVATE/'access/staging_totp_secrets.json').exists(),
        'account_fields':{k:sorted(creds[k]) for k in LOGINS},'serving_containers_exposing_secret_file_by_mount':mounts})
    old=ROOT/'docs/ai-multi-agent-upgrade/verification_runs/run_20261018_0515'
    evidence={}
    for name in ['TOTP_ROTATION_EXECUTION_PROOF.md','DEFECT_REGISTER.md','FINAL_OWNER_APPROVED_EXECUTION_REPORT.md','logs/totp_rotation_execution.log','logs/old_devices_deactivation_check.log','logs/qtt_03_playwright_e2e.log']:
        path=old/name;evidence[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
    save('wave6-evidence-sha256.json',evidence)
    result={'at':datetime.now(timezone.utc).isoformat(),'same_cluster_and_database_via_actual_rails':True,
        'direct_and_rails_rows_identical':True,'read_only_enforced_both':True,'counts':db['counts'],
        'stage_owner_actual_user_id':next(x['id'] for x in db['users'] if x['login']=='stage-owner'),
        'owner_authorization':'NOT_APPROVED_DO_NOT_ROTATE','rotation_or_device_changes_performed':False,
        'historical_success_proven_for_current_target':False}
    save('result.json',result);print(json.dumps(result))

if __name__=='__main__':main()
