"""Compare deployed files to Git objects, including line-ending-independent checkout parity."""
import datetime,hashlib,json,subprocess,sys,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.engineering_worker import python as linux_python
source=ROOT/'.codex-local/demo-release-candidate';out=Path(__file__).parent
deploy=json.loads((out/'deployment.json').read_text());head=deploy['head_sha']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source).decode().strip()==head
assert not subprocess.check_output(['git','diff','HEAD','--'],cwd=source).strip()
files={};blobs={};line_endings={}
archive=zipfile.ZipFile(io.BytesIO(subprocess.check_output(['git','archive','--format=zip',head],cwd=source)))
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',head],cwd=source).decode().splitlines():
 data=subprocess.check_output(['git','show',head+':'+name],cwd=source)
 packed=archive.read(name)
 assert packed.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n'),'SOURCE_CONTENT_DIFFERS_BEYOND_LINE_ENDINGS'
 files[name]=hashlib.sha256(packed).hexdigest();blobs[name]=hashlib.sha256(data).hexdigest()
 line_endings[name]='ARCHIVE_CRLF_GIT_LF' if packed!=data else 'BYTE_IDENTICAL'
code=r'''
from pathlib import Path
import hashlib
root=Path(document['release']);actual={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in document['files']}
assert actual==document['files']
print(json.dumps(actual))
'''
actual=json.loads(linux_python(code,{'release':deploy['release'],'files':files}).stdout)
result={'status':'DEPLOYED_EXACT_GIT_ARCHIVE_PARITY_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head_sha':head,'files':actual,'git_blob_sha256':blobs,'line_endings':line_endings,'content_equal_to_git_blobs_after_crlf_normalization':True,'checkout_has_no_diff':True,'no_secret_files_in_release':set(files)<= {'.gitignore','README.md','requirements.txt','task_manager/__init__.py','task_manager/app.py','tests/test_export_csv.py','tests/test_tasks.py','tests/test_web_ui.py','tests/test_integration_release.py'}}
assert result['no_secret_files_in_release']
(out/'source-parity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
