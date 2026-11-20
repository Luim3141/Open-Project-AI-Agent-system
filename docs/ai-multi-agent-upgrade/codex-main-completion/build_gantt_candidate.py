"""Build an immutable Core overlay candidate; never change a serving container."""
import hashlib
import json
import subprocess
from pathlib import Path
from rehearse_rollback import docker, verify_image_source
OUT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[3]

def main():
    assert json.loads((OUT / 'gantt-clone-qualification.json').read_text())['passed'], 'GANTT_BROWSER_NOT_QUALIFIED'
    base = 'qldapm-openproject:codex-main-20261020'
    expected = 'sha256:dde3c32ee69af450a6316450ac076d502953610932627ee33ce948f20dfbe459'
    assert docker('image', 'inspect', base, '--format', '{{.Id}}') == expected
    root = REPO / 'openproject/ai/core/overlay'
    manifest = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    tag = 'qldapm-openproject:codex-gantt-20261021'
    assert not (OUT / 'gantt-candidate-build.json').exists(), 'CANDIDATE_ALREADY_BUILT_RECONCILE'
    subprocess.run(['docker', 'build', '--pull=false', '--network=none', '-f', 'automation/ExecutionMonitorCore.Dockerfile',
                    '--build-arg', 'CORE_IMAGE=' + base, '--build-arg', 'SOURCE_SHA256=' + digest, '-t', tag, '.'],
                   cwd=REPO / 'openproject/ai', check=True, timeout=180)
    identifier = docker('image', 'inspect', tag, '--format', '{{.Id}}')
    matched = verify_image_source(identifier)
    result = {'tag': tag, 'image': identifier, 'base_image': expected, 'source_sha256': digest,
              'source_files_matched': matched, 'overlay_manifest': manifest, 'deployed_main': False}
    (OUT / 'gantt-candidate-build.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'overlay_manifest'}))

if __name__ == '__main__': main()
