"""Run exact candidate source on the existing isolated WSL Python runtime."""
import base64,datetime,hashlib,io,json,subprocess,sys,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.engineering_worker import python as linux_python

SOURCE=ROOT/'.codex-local/demo-release-candidate'
OUT=Path(__file__).parent
label=sys.argv[1]
assert label in {'baseline','formula-red','final'}
names=subprocess.check_output(['git','ls-files'],cwd=SOURCE).decode().splitlines()
names+= [str(p.relative_to(SOURCE)).replace('\\','/') for p in (SOURCE/'tests').glob('test_integration_release.py') if str(p.relative_to(SOURCE)).replace('\\','/') not in names]
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w') as archive:
 for name in names:
  path=SOURCE/name
  if path.is_file():archive.writestr(name,path.read_bytes())
data=buffer.getvalue();digest=hashlib.sha256(data).hexdigest()
folder='/home/openclaw/engineering/integration-release-tests/'+digest
code=r'''
from pathlib import Path,PurePosixPath
import base64,io,zipfile,subprocess,os,hashlib
root=Path(document['folder']);root.mkdir(parents=True,exist_ok=True)
data=base64.b64decode(document['archive']);assert hashlib.sha256(data).hexdigest()==document['sha256']
with zipfile.ZipFile(io.BytesIO(data)) as archive:
 for info in archive.infolist():
  name=PurePosixPath(info.filename);assert not name.is_absolute() and '..' not in name.parts
  path=root.joinpath(*name.parts);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(info))
runtime='/home/openclaw/engineering/feedback-2ec52f6742aa972f/.venv/bin/python'
env={**os.environ,'PYTHONPATH':str(root),'NODE_BINARY':'/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node'}
result=subprocess.run([runtime,'-m','pytest','-q','tests','/opt/qldapm/acceptance/test_create_list.py','/opt/qldapm/acceptance/test_crud_web.py'],cwd=root,env=env,capture_output=True,timeout=120)
print(json.dumps({'exit_code':result.returncode,'output':(result.stdout+result.stderr).decode(errors='replace'),'runtime':runtime,'source_sha256':document['sha256'],'network':'local test only; no model/provider calls'}))
'''
result=json.loads(linux_python(code,{'folder':folder,'archive':base64.b64encode(data).decode(),'sha256':digest},timeout=150).stdout)
result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
target=OUT/(label+'.json')
if target.exists():
 history=OUT/'test-history';history.mkdir(exist_ok=True)
 saved=target.read_bytes();(history/(label+'-'+hashlib.sha256(saved).hexdigest()+'.json')).write_bytes(saved)
target.write_text(json.dumps(result,indent=2)+'\n')
print(result['output']);print(json.dumps({k:v for k,v in result.items() if k!='output'}));raise SystemExit(result['exit_code'])
