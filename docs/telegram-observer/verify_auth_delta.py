"""Verify the one failed local UI-login delta in memory; never reset counters or credentials."""
import hashlib
import json
from pathlib import Path
import subprocess

out=Path(__file__).parent
expected=json.loads((out/'auth-security-before.json').read_text())
query="SELECT coalesce(json_agg(row ORDER BY row::text),'[]'::json) FROM (SELECT to_jsonb(u)-'last_login_on'-'updated_at' AS row FROM users u) s;"
rows=json.loads(subprocess.check_output(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',query]))
checksum=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
current=checksum(rows)
owner=next(row for row in rows if row['id']==18)
observed={key:owner.get(key) for key in ('failed_login_count','last_failed_login_on')}
owner.update(failed_login_count=0,last_failed_login_on=None)
verified=len(rows)==expected['rows'] and checksum(rows)==expected['sha256']
report={'status':'PASS' if verified else 'UNVERIFIED','baseline_sha256':expected['sha256'],
    'current_sha256':current,'actor':18,'observed_auth_metadata_delta':observed,
    'comparison':'Reconstructed pre-attempt counter0/last_failed NULL matches baseline only if every other user security field is unchanged',
    'database_mutations':0,'credential_reset':False}
(out/'auth-delta-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
assert verified,'AUTH_SECURITY_DELTA_REQUIRES_REVIEW'
