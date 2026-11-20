"""Bind actual immutable-image tests and independent business/Core clone receipts."""
import hashlib,json,sys
from pathlib import Path
import release_delegation as setup
OUT=Path(__file__).parent;release=setup.release
bundle,manifest=release.load_guarded(setup.BUNDLE)
business=json.loads((OUT/'delegated-clone-attempt5.json').read_text())
passed=next(r for r in business['checks'] if r['workflow']=='OWNER_DELEGATED_PROJECT6')
assert passed['status']=='BUSINESS_PASS_IN_CLONE'
assert business['gateway_base_image']==manifest['images']['gateway'] and business['core_image']==manifest['images']['core']
for path,value in manifest['source_hashes'].items():
    if release.SOURCES[path][0]=='gateway':assert business['gateway_sources'][Path(path).name]==value
core=json.loads((OUT/'delegated-core-clone.json').read_text());assert core['status']=='PASS' and core['image']==manifest['images']['core']
image=json.loads((OUT/'image-regression.json').read_text());assert image['exit_code']==0 and image['image']==manifest['images']['gateway']
github=json.loads((OUT/'github-regression.json').read_text());assert github['exit_code']==0
proof={'status':'PASS','source_hashes':manifest['source_hashes'],'images':manifest['images'],
       'checks':{'github':True,'events':True,'core':True},
       'evidence':{'immutable_image':'image-regression.json','business':'delegated-clone-attempt5.json','core':'delegated-core-clone.json','github_unchanged_regression':'github-regression.json'},
       'scope':'Project6 delegated policy/WF05/06/09/CC. RAG research excluded, no coding or GitHub release.',
       'human_uat':False,'business_generation_calls':0,'main_business_readback':'PENDING_ROLLOUT',
       'limits':['Task[Bug] uses actual Task1 workflow NEW→IN ANALYSIS; reverse is not permitted. Baseline note compensated; owned fixture remains in valid non-coding test state.']}
(OUT/'delegated-qualification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'status':'PASS','images':manifest['images'],'scope':proof['scope']}))
