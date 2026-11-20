"""Private portable source bundle and final manifest; no remote/publication."""
from pathlib import Path
import hashlib,json,subprocess
RUN=Path(__file__).parent;ROOT=RUN.parents[4]
m=json.loads((RUN/'source-versioning-manifest.json').read_text());repo=Path(m['private_source_root'])
images=json.loads((RUN/'candidate-images.json').read_text())
payload={key:(repo/'openproject/ai/core/overlay'/path).read_text() for key,path in [('view','app/views/qldapm_ai/_engineering_command_center.html.erb'),('controller','app/controllers/qldapm_ai_controller.rb')]}
code=(RUN.parent/'check_github_ui.rb').read_text()
p=subprocess.run(['docker','run','--rm','-i','--network','none','--read-only','--tmpfs','/tmp:rw,size=128m','--entrypoint','bundle',images['core']['id'],'exec','ruby','-e',code],input=json.dumps(payload).encode(),capture_output=True,timeout=30)
(RUN/'github-ui-final.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
bundle=repo.parent/'source-final.bundle'
subprocess.run(['git','-C',str(repo),'bundle','create',str(bundle),'--all'],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'bundle','verify',str(bundle)],check=True,capture_output=True)
worker={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'openproject/ai/automation/engineering_worker.py',ROOT/'openproject/ai/automation/engineering_delivery.py',ROOT/'openproject/ai/automation/n8n_lifecycle_adapter.py']}
manifest={'qualification_source_commit':m['commit'],'image_build_source_commit':images['gateway']['source_commit'],
 'note':'Later commit changes host delivery/adapter/tests/architecture only; packaged app sources still match all15 parity checks.',
 'source_files':len(m['included']),'quarantined':m['quarantined'],'source_bundle':str(bundle),
 'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'worker_adapter_sha256':worker,
 'images':images,'source_manifest_sha256':hashlib.sha256((RUN/'source-versioning-manifest.json').read_bytes()).hexdigest()}
(RUN/'source-candidate-final-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'source_commit':m['commit'],'files':len(m['included']),'bundle_verified':True,'github_ui_contract':'PASS'},indent=2))
