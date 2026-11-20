"""Private-setting hashes, original row prefixes and Native status/security fingerprints."""
import importlib.util,json,hashlib,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prior_preserve',OUT.parent/'agent-studio-v2/preservation.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def capture():
    ecosystem=prior.capture()
    sql="""SELECT json_build_object(
    'project5',(SELECT md5(string_agg(row_to_json(w)::text,'' ORDER BY id)) FROM work_packages w WHERE project_id=5),
    'old_project6',(SELECT md5(string_agg(json_build_array(id,subject,status_id,lock_version,assigned_to_id,parent_id)::text,'' ORDER BY id)) FROM work_packages WHERE project_id=6 AND id<=397),
    'roles',(SELECT md5(string_agg(row_to_json(r)::text,'' ORDER BY id)) FROM roles r),
    'members',(SELECT md5(string_agg(row_to_json(r)::text,'' ORDER BY id)) FROM members r),
    'member_roles',(SELECT md5(string_agg(row_to_json(r)::text,'' ORDER BY id)) FROM member_roles r),
    'workflows',(SELECT md5(string_agg(row_to_json(r)::text,'' ORDER BY id)) FROM workflows r),
    'statuses',(SELECT md5(string_agg(row_to_json(r)::text,'' ORDER BY id)) FROM statuses r),
    'auth',(SELECT md5(string_agg(json_build_array(id,login,status,admin)::text,'' ORDER BY id)) FROM users),
    'passwords',(SELECT md5(string_agg(row_to_json(r)::text,'' ORDER BY id)) FROM user_passwords r));"""
    native=json.loads(subprocess.check_output(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',sql]))
    baseline=json.loads((OUT/'baseline.json').read_text())['protected_state']
    code='''import json,sqlite3,hashlib,sys,pathlib
p=json.load(sys.stdin);d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
out={}
for t in ['ai_queue','ai_runs','requests','gemini_call_receipts','engineering_checkpoints','tokens']:
 rows=d.execute('SELECT * FROM '+t+' ORDER BY rowid LIMIT ?',(p['tables'][t]['rows'],)).fetchall()
 out[t]={'original_rows_sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),'rows':d.execute('SELECT count(*) FROM '+t).fetchone()[0]}
print(json.dumps({'tables':out,'files':{f:hashlib.sha256((pathlib.Path('/state')/f).read_bytes()).hexdigest() for f in p['files']},'active':d.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0],'mode':d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]}))'''
    p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-c',code],input=json.dumps(baseline),text=True,capture_output=True,check=True)
    gateway=json.loads(p.stdout)
    assert gateway['files']==baseline['files']
    assert all(v['original_rows_sha256']==baseline['tables'][t]['sha256'] for t,v in gateway['tables'].items()),'ORIGINAL_ROW_CHANGED'
    return {'ecosystem':ecosystem,'native':native,'gateway':gateway}
if __name__=='__main__':
    phase=sys.argv[1];data=capture()
    if phase=='before':assert not (OUT/'preservation-before.json').exists()
    else:
        before=json.loads((OUT/'preservation-before.json').read_text());assert data['native']==before['native'],'NATIVE_PROTECTED_STATE_CHANGED'
        assert data['ecosystem']['files']==before['ecosystem']['files'] and data['ecosystem']['n8n']==before['ecosystem']['n8n']
        assert data['ecosystem']['containers']==before['ecosystem']['containers']
    (OUT/f'preservation-{phase}.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'status':'BASELINED' if phase=='before' else 'PRESERVED','native':data['native'],'mode':data['gateway']['mode'],'active':data['gateway']['active']}))
