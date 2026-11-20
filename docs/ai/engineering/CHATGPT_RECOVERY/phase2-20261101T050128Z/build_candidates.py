"""Build only from the private committed snapshot; no serving mutation."""
from pathlib import Path
import json,subprocess
RUN=Path(__file__).parent
manifest=json.loads((RUN/'source-versioning-manifest.json').read_text())
source=Path(manifest['private_source_root'])/'openproject/ai'
images={}
for kind,recipe,tag in [('gateway','GatewayRecovery.Dockerfile','qldapm-ai:recovery-phase2-20261101-r2'),
                        ('core','CoreRecovery.Dockerfile','qldapm-core:recovery-phase2-20261101-r1'),
                        ('n8n','N8nRedacted.Dockerfile','qldapm-n8n:recovery-phase2-redacted-r2')]:
    command=['docker','build','--pull=false','-f',str(source/'automation'/recipe),'-t',tag,str(source)]
    with (RUN/(kind+'-final-build.log')).open('w') as log:
        p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    assert p.returncode==0, kind+' build failed; inspect log'
    identity=json.loads(subprocess.check_output(['docker','image','inspect',tag]))[0]['Id']
    images[kind]={'tag':tag,'id':identity,'source_commit':manifest['commit'],'recipe':recipe}
    print(kind,identity,flush=True)
(RUN/'candidate-images.json').write_text(json.dumps(images,indent=2)+'\n')
