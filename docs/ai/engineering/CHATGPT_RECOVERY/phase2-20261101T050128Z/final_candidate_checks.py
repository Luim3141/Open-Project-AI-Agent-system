"""Offline qualification against exact private snapshot and image IDs."""
from pathlib import Path
import hashlib,json,subprocess
RUN=Path(__file__).parent;ROOT=RUN.parents[4]
manifest=json.loads((RUN/'source-versioning-manifest.json').read_text())
source=Path(manifest['private_source_root'])/'openproject/ai'
images=json.loads((RUN/'candidate-images.json').read_text());checks=[]
def run(name,command,data=None):
    p=subprocess.run(command,input=data,capture_output=True,timeout=240)
    (RUN/(name+'.log')).write_bytes(p.stdout+p.stderr)
    checks.append({'check':name,'exit_code':p.returncode,'command':command,'log':name+'.log'})
    print(name,p.returncode,(p.stdout+p.stderr).decode(errors='replace')[-250:],flush=True)
    assert p.returncode==0,name
base=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:rw,size=512m']
cmd=base+['-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/app:/verification/openproject/ai','-e','QLDAPM_AI_RUNTIME=',
 '--workdir','/verification/openproject/ai','--entrypoint','python']
for folder in ['tests','automation','core/overlay']:
    cmd+=['--mount',f'type=bind,source={source/folder},target=/verification/openproject/ai/{folder},readonly']
modules=json.loads((RUN.parent/'run-20261101T035551Z/linux-regression-r2-command.json').read_text())
modules=modules[modules.index('unittest')+1:-1]
modules+=['tests.test_engineering_github_journal','tests.test_n8n_lifecycle_outbox','tests.test_main_backup_clone',
 'tests.test_main_native_clone','tests.test_engineering_integrity_projection','tests.test_engineering_worker_process',
 'tests.test_openclaw_provider_gate','tests.test_provider_wait','tests.test_knowledge_sync',
 'tests.test_engineering_delivery_recovery','tests.test_n8n_lifecycle_adapter']
try:
    run('linux-final-regression',cmd+[images['gateway']['id'],'-m','unittest',*modules,'-v'])
    for record in json.loads((RUN.parent/'run-20261101T035551Z/ruby-checks.json').read_text()):
        cmd=record['command'];cmd=[images['core']['id'] if a=='qldapm-core:chatgpt-recovery-20261101-r1' else a for a in cmd]
        run(record['check'],cmd)
    run('report-controller-final',base+['-i','--mount',f'type=bind,source={source/"tests/test_report_controller.rb"},target=/tmp/report-test.rb,readonly','--entrypoint','bundle',images['core']['id'],'exec','ruby','/tmp/report-test.rb'],json.dumps({'controller':(source/'core/overlay/app/controllers/qldapm_ai_controller.rb').read_text()}).encode())
    run('report-reader-final',base+['--mount',f'type=bind,source={source},target=/verification,readonly','--entrypoint','node',images['n8n']['id'],'/verification/tests/test_report_reader.js'])
    run('redactor-final',base+['--mount',f'type=bind,source={source/"tests/test_n8n_storage_redaction.js"},target=/tmp/test.js,readonly','--entrypoint','node',images['n8n']['id'],'/tmp/test.js'])
    parity=[]
    gateway=['engineering.py','engineering_lifecycle.py','store.py','engineering_github_sync.py','engineering_reporting.py','knowledge_search.py','app.py','service.py','execution_events.py','engineering_monitor.py','engineering_integrity.py','n8n_lifecycle_outbox.py']
    targets=[('gateway','gateway/'+f,'/app/gateway/'+f) for f in gateway]
    targets += [('core','core/overlay/'+p,'/app/'+p) for p in ['app/controllers/qldapm_ai_controller.rb','app/views/qldapm_ai/_engineering_command_center.html.erb']]
    targets += [('n8n','automation/n8n_storage_redaction.js','/opt/qldapm/n8n_storage_redaction.js')]
    for kind,local,remote in targets:
        actual=subprocess.check_output(base+['--entrypoint','cat',images[kind]['id'],remote])
        host=(ROOT/'openproject/ai'/local).read_bytes();snapshot=(source/local).read_bytes()
        assert host==snapshot==actual,local
        parity.append({'file':local,'sha256':hashlib.sha256(actual).hexdigest(),'host_snapshot_runtime_match':True})
    (RUN/'candidate-final-parity.json').write_text(json.dumps(parity,indent=2)+'\n')
    print('PARITY',len(parity),flush=True)
finally:(RUN/'final-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
