"""Move only this run's generated Native clone DB artifacts to the private operator root."""
from pathlib import Path
import hashlib,json,os,shutil,uuid
RUN=Path(__file__).parent.resolve()
operator=(Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator').resolve()
private=(operator/('phase2-native-artifacts-'+uuid.uuid4().hex[:8])).resolve()
assert private.is_relative_to(operator) and private.parent==operator
private.mkdir()
manifest=[]
for name in ['native-candidate-clone','native-candidate-clone-final','native-rollback-clone']:
    source=(RUN/name).resolve();target=(private/name).resolve()
    assert source.parent==RUN and source.is_relative_to(RUN)
    assert target.parent==private and target.is_relative_to(operator) and not target.exists()
    if not source.exists():continue
    assert (source/'clone.json').is_file()
    for path in source.rglob('*'):
        if path.is_file():manifest.append({'path':str(target/path.relative_to(source)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    shutil.move(str(source),str(target))
(RUN/'private-native-artifacts.json').write_text(json.dumps({'private_root':str(private),'files':manifest,'source_git_bundle_included_db_files':False},indent=2)+'\n')
assert not any(p.suffix in {'.dump','.sqlite','.db'} for p in RUN.rglob('*') if p.is_file())
print(json.dumps({'private_artifact_files':len(manifest),'workspace_db_artifacts_remaining':0}))
