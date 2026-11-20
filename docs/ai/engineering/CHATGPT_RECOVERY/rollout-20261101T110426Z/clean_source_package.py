"""Private packaging correction only; deployed/approved source files are not modified."""
from support import *
import shutil
manifest=json.loads((PHASE/'source-versioning-manifest.json').read_text())
original=json.loads((PRIVATE/'qldapm-n8n-main-inspect.json').read_text())
key=next(v.split('=',1)[1] for v in original['Config']['Env'] if v.startswith('N8N_ENCRYPTION_KEY='))
assert len(key)>=32
excluded=[];included=[]
for row in manifest['included']:
    if key.encode() in (ROOT/row['path']).read_bytes():excluded.append(row['path'])
    else:included.append(row)
result={'approved_source_commit_unchanged':manifest['commit'],'current_n8n_encryption_key_in_legacy_source':bool(excluded),
        'excluded_paths':excluded,'main_credentials_rotated':False,'public_remote_created':False}
if excluded:
    output=PRIVATE/'clean-source';output.mkdir()
    for row in included:
        target=output/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/row['path'],target)
    (output/'.gitattributes').write_bytes(b'* -text\n')
    execute(['git','-C',str(output),'init','-b','codex/recovery-phase2-clean-source'])
    execute(['git','-C',str(output),'config','core.autocrlf','false'])
    spec=PRIVATE/'clean-source-pathspec.nul';spec.write_bytes(b'.gitattributes\0'+b''.join(Path(r['path']).as_posix().encode()+b'\0' for r in included))
    execute(['git','-C',str(output),'add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'])
    execute(['git','-C',str(output),'-c','user.name=Codex Recovery Snapshot','-c','user.email=codex@localhost','commit','-m','Package approved source without credential-bearing legacy tooling'])
    commit=execute(['git','-C',str(output),'rev-parse','HEAD']).decode().strip()
    bundle=PRIVATE/'clean-source.bundle';execute(['git','-C',str(output),'bundle','create',str(bundle),'HEAD'])
    execute(['git','-C',str(output),'bundle','verify',str(bundle)])
    assert key.encode() not in b''.join((output/r['path']).read_bytes() for r in included)
    old_parent=Path(manifest['private_source_root']).parent
    (old_parent/'SENSITIVE_SOURCE_DO_NOT_PUBLISH.txt').write_text('Historical private snapshot/bundle includes credential-bearing legacy tooling. Do not publish or export. Use clean-source package recorded in rollout evidence. Existing history retained; no shared history rewritten.\n')
    result.update(clean_private_source=str(output),clean_commit=commit,clean_bundle=str(bundle),clean_bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),clean_source_files=len(included),
                  historical_snapshot='Retained in private operator directory; marked sensitive and unsuitable for publication')
write('source-packaging-security-correction.json',result)
print(json.dumps({'legacy_source_paths_excluded':len(excluded),'clean_package_created':bool(excluded),'main_changed':False}))
