"""Retain the previous owned browser container; start the built candidate on its clone DB."""
import json
from pathlib import Path
from rehearse_rollback import docker
OUT = Path(__file__).parent

def main():
    record = json.loads((OUT / 'clone.json').read_text()); private = Path(record['private']); names = record['names']
    build = json.loads((OUT / 'gantt-candidate-build.json').read_text())
    assert not record.get('previous_browser'), 'CLONE_REPLACEMENT_EXISTS_RECONCILE'
    old = json.loads(docker('inspect', names['browser']))[0]
    assert old['Config']['Labels'].get('qldapm.qualification') == 'codex-main-20261020'
    assert old['Image'] == build['base_image']
    assert set(old['NetworkSettings']['Networks']) == {names['network'], names['front']}
    assert str(private.resolve()).startswith(str((Path.home() / 'AppData/Local/QLDAPM/openproject-ai/operator/codex-main-completion').resolve()))
    previous = names['browser'] + '-pre-gantt-20261021'
    (OUT / 'gantt-clone-replacement.json').write_text(json.dumps({'phase': 'PREPARED', 'previous': previous, 'candidate': build['image']}))
    docker('stop', names['browser']); docker('rename', names['browser'], previous)
    docker('run', '-d', '--name', names['browser'], '--label', record['label'], '--network', names['network'], '--network-alias', 'web',
           '-p', '127.0.0.1:18088:8080', '--env-file', str(private / 'browser.env'), '--memory', '3g',
           '--mount', f'type=bind,src={private},dst=/qa-private', '--entrypoint', 'bundle', build['image'],
           'exec', 'rails', 'server', '-b', '0.0.0.0', '-p', '8080')
    docker('network', 'connect', names['front'], names['browser'])
    record.update(previous_browser=previous, image=build['image'], status='GANTT_CANDIDATE_IMAGE_BROWSER_STARTING')
    (OUT / 'clone.json').write_text(json.dumps(record, indent=2))
    (OUT / 'gantt-clone-replacement.json').write_text(json.dumps({'phase': 'STARTED_NOT_YET_QUALIFIED', 'previous': previous, 'candidate': build['image'], 'serving_changes': 0}))
    print('Built image started on existing owned clone; previous container retained stopped; serving unchanged.')

if __name__ == '__main__': main()
