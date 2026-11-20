"""Read-only code/diff capture and immutable rollback image. Never restarts a serving container."""
import difflib
import hashlib
import json
import os
from pathlib import Path
from inspect_runtime import ROOT,OUT,run
from qualify import checked_build

def main():
    q=json.loads((OUT/'qualification.json').read_text());before=json.loads((OUT/'runtime-before.json').read_text())
    private=Path(q['private']);context=OUT/'rollback-core';overlay=context/'overlay';overlay.mkdir(parents=True,exist_ok=True)
    files={k:v for k,v in q['source'].items() if k.startswith('core/overlay/')}
    hashes={}
    for rel in files:
        path=rel.removeprefix('core/overlay/')
        destination=overlay/path;destination.parent.mkdir(parents=True,exist_ok=True)
        assert not destination.exists(),'ROLLBACK_SOURCE_ALREADY_CAPTURED'
        run('docker','cp','qldapm-openproject-web-1:/app/'+path,str(destination))
        hashes[path]=hashlib.sha256(destination.read_bytes()).hexdigest()
    (OUT/'core-runtime-before.json').write_text(json.dumps(hashes,indent=2))
    (context/'Dockerfile').write_text('FROM qldapm-core-dependency:write403-95da6c8e\nCOPY --chown=app:app overlay/ /app/\n')
    checked_build(['build','-t','qldapm-core:write403-rollback-20261021',str(context)],'rollback-core-build.log')
    rollback=run('docker','image','inspect','qldapm-core:write403-rollback-20261021','--format','{{.Id}}').strip()
    diffs=[];changed=[]
    for folder in ('gateway','core/overlay'):
        for path in (ROOT/'openproject/ai'/folder).rglob('*'):
            if not path.is_file() or '__pycache__' in str(path):continue
            relative=path.relative_to(ROOT).as_posix();old=private/'source-before'/relative
            if old.exists() and old.read_bytes()!=path.read_bytes():
                changed.append(relative)
                diffs.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True),path.read_text(encoding='utf-8').splitlines(True),fromfile='before/'+relative,tofile='after/'+relative))
    (OUT/'source.diff').write_text(''.join(diffs),encoding='utf-8')
    (OUT/'git-status.txt').write_text(run('git','status','--porcelain'),encoding='utf-8')
    core_drift=[k for k,v in hashes.items() if v!=before['source']['openproject/ai/core/overlay/'+k]]
    gateway_drift=[k for k,v in before['gateway']['hashes'].items() if before['source'].get('openproject/ai/gateway/'+k)!=v]
    result={'rollback_core':rollback,'rollback_gateway':before['containers']['qldapm-ai-gateway-1']['Image'],
            'core_files_captured':len(hashes),'core_runtime_vs_pre_edit_source_drift':core_drift,
            'gateway_runtime_vs_pre_edit_source_drift':gateway_drift,'changed_production_files':changed,
            'reviewed_scope':'5 production files; preserve Gemini recovery changes; no migrations, tools, provider settings or RBAC edits',
            'source_sha256':q['source_sha256'],'main_permission_pending':'manage_subtasks role22 requires separate Owner approval'}
    (OUT/'release-preparation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
