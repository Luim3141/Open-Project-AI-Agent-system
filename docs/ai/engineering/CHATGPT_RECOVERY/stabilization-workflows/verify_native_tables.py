import json,os,re,subprocess
from pathlib import Path

backup=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/stabilization-controls-rollout-20261102/backup/postgres.dump'
data=backup.read_bytes()
def run(args,stdin=None):
    return subprocess.run(['docker','exec','-i','qldapm-openproject-db-1',*args],input=stdin,capture_output=True,check=True,timeout=120).stdout
def rows(dump,table):
    m=re.search(rb'COPY (?:public\.)?'+table.encode()+rb' \(([^\n]+)\) FROM stdin;\r?\n',dump)
    assert m,table
    end=dump.index(b'\n\\.',m.end())
    return m.group(1),sorted(dump[m.end():end].splitlines())
result={}
for table in ['users','members','member_roles','roles','projects','work_packages']:
    old=run(['pg_restore','--data-only','--table='+table,'--file=-'],data)
    now=run(['pg_dump','-U','postgres','-d','openproject','--data-only','--table=public.'+table,'--no-owner','--no-privileges'])
    a,ar=rows(old,table);b,br=rows(now,table)
    result[table]={'rows_before':len(ar),'rows_after':len(br),'all_columns_equal':a==b and ar==br}
result['status']='PASS' if all(v['all_columns_equal'] for v in result.values()) else 'DIFFERENCE_OBSERVED'
(Path(__file__).parent/'native-table-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
