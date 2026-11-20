"""Private Git only: make archive bytes equal the candidate source manifest on Windows."""
from pathlib import Path
import hashlib,io,json,subprocess,tarfile
RUN=Path(__file__).parent
manifest=json.loads((RUN/'source-versioning-manifest.json').read_text());repo=Path(manifest['private_source_root'])
subprocess.run(['git','-C',str(repo),'config','core.autocrlf','false'],check=True)
(repo/'.gitattributes').write_bytes(b'* -text\n')
spec=repo.parent/'source-final-pathspec.nul'
spec.write_bytes(b''.join(Path(row['path']).as_posix().encode()+b'\0' for row in manifest['included']))
subprocess.run(['git','-C',str(repo),'add','--renormalize','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'add','--','.gitattributes'],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'-c','user.name=Codex Recovery Snapshot','-c','user.email=codex@localhost','commit','-m','Preserve exact candidate bytes in portable Git archive'],check=True,capture_output=True)
manifest['commit']=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()
archive=subprocess.check_output(['git','-C',str(repo),'archive','HEAD'])
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    for row in manifest['included']:
        data=tar.extractfile(Path(row['path']).as_posix()).read()
        assert hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
manifest['git_archive_byte_parity']={'files':len(manifest['included']),'status':'PASS','attributes':'private .gitattributes * -text; local core.autocrlf=false; global config unchanged'}
(RUN/'source-versioning-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(RUN/'git-archive-parity.json').write_text(json.dumps({'commit':manifest['commit'],**manifest['git_archive_byte_parity']},indent=2)+'\n')
print(json.dumps({'commit':manifest['commit'],'git_archive_exact_files':len(manifest['included'])},indent=2))
