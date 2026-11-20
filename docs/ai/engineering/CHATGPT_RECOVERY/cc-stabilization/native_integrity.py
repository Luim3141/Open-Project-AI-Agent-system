"""Read-only Project5/global config snapshots, private raw rows and public hashes."""
import ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).parent;private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization'
tree=ast.parse((OUT.parent/'integration-final/native_integrity.py').read_text())
queries=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='queries' for t in n.targets))
mode=sys.argv[1];assert mode in {'before','after'};path=private/f'native-integrity-{mode}.json';assert not path.exists()
snapshot={}
for table,query in queries.items():
    sql="SELECT coalesce(json_agg(row ORDER BY row::text),'[]'::json) FROM (SELECT row_to_json(t) AS row FROM ("+query+") t) s;"
    snapshot[table]=json.loads(subprocess.check_output(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',sql],timeout=45))
path.write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
result={'at':time.time(),'scope':'Read-only Project5 rows plus global config/security tables','tables':{t:{'count':len(v),'sha256':hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()} for t,v in snapshot.items()}}
if mode=='after':
    before=json.loads((private/'native-integrity-before.json').read_text(encoding='utf-8'));allowed={}
    for table,rows in snapshot.items():
        if table!='users':assert rows==before[table],table
        else:
            old={r['id']:r for r in before[table]};new={r['id']:r for r in rows};assert old.keys()==new.keys()
            allowed={str(i):[k for k in old[i] if old[i][k]!=new[i][k]] for i in old if old[i]!=new[i]}
            assert all(set(v)<={'last_login_on','updated_at'} for v in allowed.values())
    result.update(status='PASS',allowed_user_timestamp_changes=allowed)
(OUT/f'native-integrity-{mode}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
