"""One-shot PM7 credential recovery explicitly authorized by Owner on 21 Oct 2026."""
import datetime
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
from read_only_audit import OUT, RUNTIME, command

receipt = OUT/'pm-recovery.json'
assert not receipt.exists(), 'Refuse repeated credential reset'
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
private = RUNTIME/'operator'/('PUBLICATION_REDACTED-pm-recovery-'+stamp)
private.mkdir(exist_ok=False)
principal = os.environ['USERDOMAIN']+'\\'+os.environ['USERNAME']
command(['icacls',str(private),'/inheritance:r','/grant:r',principal+':(OI)(CI)F','SYSTEM:(OI)(CI)F'])
backup = subprocess.run(['docker','exec','qldapm-ai-stage-db-1','pg_dump','-Fc','-U','postgres','openproject'],capture_output=True,timeout=60)
assert backup.returncode == 0 and backup.stdout.startswith(b'PGDMP'), 'Private backup failed'
(private/'staging-before-recovery.dump').write_bytes(backup.stdout)
account_file = RUNTIME/'stage/accounts.json'
accounts = json.loads(account_file.read_text(encoding='utf-8'))
pm = next(x for x in accounts['users'] if x.get('id') == 7 or x.get('login') == 'pm' or x.get('username') == 'pm')
assert pm.get('role') == 'PM', 'Saved PM mapping mismatch'
assert 'password' in pm, 'Saved password contract missing'
(private/'accounts-before.json').write_bytes(account_file.read_bytes())
password = secrets.token_urlsafe(24)+'aA9!'
url = json.loads((RUNTIME/'access/current-url.json').read_text())['url']
login_file = private/'PM_STAGING_LOGIN.txt'
login_file.write_text('Staging ONLY\nURL: '+url+'/login\nUsername: pm\nPassword: PUBLICATION_REDACTED\nTOTP: enroll a NEW native authenticator after sign-in. Do not reuse the old seed.\n',encoding='utf-8')
program = '''require "json"
data=JSON.parse(STDIN.read)
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner") && Project.find_by!(identifier: "qldapm-local").id == 3
c=ActiveRecord::Base.connection
hash_query=lambda { |table,condition| c.select_value("SELECT md5(coalesce(string_agg(row_to_json(t)::text,'' ORDER BY t.id),'')) FROM #{table} t WHERE #{condition}") }
protected=lambda { {"other_users"=>hash_query.call("users","id<>7"),"other_totp"=>hash_query.call("two_factor_authentication_devices","user_id<>7"),"other_passwords"=>hash_query.call("user_passwords","user_id<>7"),"work_packages"=>hash_query.call("work_packages","true"),"members"=>hash_query.call("members","true"),"roles"=>hash_query.call("roles","true"),"api_tokens"=>hash_query.call("tokens","type='Token::API'"),"settings"=>hash_query.call("settings","true")} }
before=protected.call
result=nil
ActiveRecord::Base.transaction do
 u=User.lock.find(7)
 raise "TARGET_IDENTITY_MISMATCH" unless u.login=="pm" && !u.admin? && u.active?
 removed=u.otp_devices.pluck(:id)
 u.password=data.fetch("password")
 u.password_confirmation=u.password
 u.force_password_change=false
 u.failed_login_count=0
 u.last_failed_login_on=nil
 u.save!
 u.otp_devices.destroy_all
 u.reload
 raise "PASSWORD_VERIFICATION_FAILED" unless u.check_password?(data.fetch("password"),update_legacy:false)
 raise "TOTP_RESET_FAILED" unless u.otp_devices.count.zero?
 after=protected.call
 raise "OUT_OF_SCOPE_DATA_CHANGED" unless before==after
 result={target:"Staging",actor_id:7,login:"pm",password_verified:true,removed_device_ids:removed,active_devices:0,other_users_roles_api_tokens_settings_business_unchanged:true,protected_before:before,protected_after:after}
end
puts "RECOVERY="+JSON.generate(result)
'''
# Feed the secret via stdin to a fixed native runner; never arguments, stdout or repository.
runner = 'require "base64"; eval(Base64.decode64("'+base64.b64encode(program.encode()).decode()+'"), TOPLEVEL_BINDING)'
p = subprocess.run(['docker','exec','-i','qldapm-ai-stage-staging-web-1','bundle','exec','rails','runner',runner],input=json.dumps({'password':password}),text=True,capture_output=True,timeout=90)
if p.returncode:
    (private/'recovery-error.log').write_text(p.stderr+p.stdout,encoding='utf-8')
    raise RuntimeError('Recovery failed; private diagnostic retained, no secret output')
line=next((x for x in p.stdout.splitlines() if x.startswith('RECOVERY=')),None)
assert line, 'Native recovery receipt missing; do not repeat blindly'
result=json.loads(line[len('RECOVERY='):])
pm['password']=password
account_file.write_text(json.dumps(accounts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result.update(timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(),login_file=str(login_file),private_backup=str(private/'staging-before-recovery.dump'),owner_authorization='Explicit password + TOTP recovery after reported 422, this chat',native_enrollment_pending=True)
receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'PM_PASSWORD_RESET_TOTP_NATIVE_ENROLLMENT_PENDING','login_file':str(login_file),'protected_data_unchanged':True},ensure_ascii=False))
