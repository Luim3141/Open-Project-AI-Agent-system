import hashlib,json,os,re,subprocess
from pathlib import Path

backup=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/post30218-e2e-prechange-20261101T153721Z/native/postgres.dump'
dump=backup.read_bytes()
def call(args,data=None):
    p=subprocess.run(['docker','exec','-i','qldapm-openproject-db-1',*args],input=data,capture_output=True,timeout=120,check=True)
    return p.stdout
old=call(['pg_restore','--data-only','--table=work_packages','--file=-'],dump)
live=call(['pg_dump','-U','postgres','-d','openproject','--data-only','--table=public.work_packages','--no-owner','--no-privileges'])
def extract(data):
    m=re.search(rb'COPY (?:public\.)?work_packages \(([^\n]+)\) FROM stdin;\r?\n',data)
    assert m,'WORK_PACKAGE_COPY_NOT_FOUND'
    cols=m.group(1).decode().replace('"','').split(', '); idx=cols.index('project_id')
    end=data.index(b'\n\\.',m.end()); rows=data[m.end():end].splitlines()
    selected=sorted(row for row in rows if row.split(b'\t')[idx]==b'5')
    assert len(selected)==341
    return cols,hashlib.sha256(b'\n'.join(selected)).hexdigest()
a,ha=extract(old);b,hb=extract(live)
assert a==b and ha==hb,'PROJECT5_ROWS_CHANGED'
result={'status':'PASS','project':5,'rows':341,'all_columns_equal_snapshot':True,'sha256':ha}
(Path(__file__).parent/'project5-content-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
