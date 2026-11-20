"""Read-only PG row snapshots; raw data stays in private operator storage, output hashes only."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase3_1-native-integrity';root.mkdir(exist_ok=True)
queries={
'work_packages':'SELECT * FROM work_packages WHERE project_id=5',
'projects':'SELECT * FROM projects WHERE id=5','members':'SELECT * FROM members WHERE project_id=5',
'member_roles':'SELECT * FROM member_roles WHERE member_id IN (SELECT id FROM members WHERE project_id=5)',
'versions':'SELECT * FROM versions WHERE project_id=5','enabled_modules':'SELECT * FROM enabled_modules WHERE project_id=5',
'relations':'SELECT * FROM relations WHERE from_id IN (SELECT id FROM work_packages WHERE project_id=5) OR to_id IN (SELECT id FROM work_packages WHERE project_id=5)',
'journals':"SELECT * FROM journals WHERE journable_type='WorkPackage' AND journable_id IN (SELECT id FROM work_packages WHERE project_id=5)",
'roles':'SELECT * FROM roles','role_permissions':'SELECT * FROM role_permissions','workflows':'SELECT * FROM workflows','settings':'SELECT * FROM settings','users':'SELECT * FROM users'}
mode=sys.argv[1];assert mode in ['before','after','after-final','after-identity'];target=root/(mode+'.json');assert not target.exists(),'Snapshot exists; preserve it'
snapshot={}
for table,query in queries.items():
 sql="SELECT coalesce(json_agg(row ORDER BY row::text),'[]'::json) FROM (SELECT row_to_json(t) AS row FROM ("+query+") t) s;"
 p=subprocess.run(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',sql],capture_output=True,check=True,timeout=45)
 snapshot[table]=json.loads(p.stdout)
target.write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Project5 scoped Native rows + global security/config tables; no writes','tables':{t:{'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()} for t,rows in snapshot.items()}}
if mode.startswith('after'):
 before=json.loads((root/'before.json').read_text(encoding='utf-8'));diff={}
 for t in snapshot:
  if before[t]!=snapshot[t]:
   if t=='users':
    old={r['id']:r for r in before[t]};new={r['id']:r for r in snapshot[t]};assert old.keys()==new.keys()
    changed={str(i):[k for k in old[i] if old[i][k]!=new[i][k]] for i in old if old[i]!=new[i]}
    assert all(set(v)<= {'last_login_on','updated_at'} for v in changed.values()),'USER_SECURITY_DATA_CHANGED'
    diff[t]={'per_id_changed_columns':changed,'security_fields_unchanged':True}
   else:raise AssertionError('PROJECT5_OR_SECURITY_TABLE_CHANGED: '+t)
 result['comparison']={'identical_tables':len(snapshot)-len(diff),'allowed_observed_changes':diff,'status':'PASS_WITH_TIMESTAMP_LIMIT' if diff else 'PASS'}
out=Path(__file__).parent/('native-'+mode+'.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'snapshot':mode,'tables':{k:v['count'] for k,v in result['tables'].items()},'comparison':result.get('comparison')}))

