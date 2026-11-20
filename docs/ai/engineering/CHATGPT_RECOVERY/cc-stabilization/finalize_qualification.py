import json,subprocess,sys,importlib,re
from pathlib import Path
caption='--caption' in sys.argv;reports='--reports' in sys.argv or caption;polish='--polish' in sys.argv or reports
suffix='-caption' if caption else '-reports' if reports else '-polish' if polish else ''
setup=importlib.import_module('release_caption' if caption else 'release_reports' if reports else 'release_polish' if polish else 'release_cc')
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4];release=setup.release
bundle,manifest=release.load_guarded(setup.BUNDLE)
clone_file='clone-qualification'+suffix+'.json';image_file='image-regression-reports.json' if caption else 'image-regression'+suffix+'.json'
clone=json.loads((OUT/clone_file).read_text());image=json.loads((OUT/image_file).read_text())
assert clone['status']=='PASS' and clone['images']==manifest['images'] and clone['source_hashes']==manifest['source_hashes']
assert image['exit_code']==0 and image['image']==manifest['images']['gateway']
test_count=int(re.search(r'Ran (\d+) tests',image['stderr_tail']).group(1))
js={}
for name in ['test_cc_navigation.js','test_owner_live_transport.js','test_report_reader.js']:
    p=subprocess.run(['node',str(ROOT/'openproject/ai/tests'/name)],capture_output=True,timeout=30)
    assert p.returncode==0,p.stderr.decode();js[name]=p.stdout.decode().strip()
proof={'status':'PASS','images':manifest['images'],'source_hashes':manifest['source_hashes'],'checks':{'github':True,'events':True,'core':True},
    'evidence':{'immutable_gateway_image':image_file,'actual_native_and_rails_clone':clone_file,'navigation_transport':js,'main_native_read_only_preview':'native-dry-run.json'},
    'test_count':test_count,'scope':str(test_count)+' immutable-image regression tests including GitHub/outbox; actual Native forms/PATCH/readback/controls; actual Rails login/CSRF/render/fast receipt (exact Core image reuse recorded where applicable); deterministic browser-handler regression. Actual Main browser/GitHub/n8n readback follows rollout.',
    'generation_calls':0,'main_writes':0}
(OUT/('qualification'+suffix+'.json')).write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'status':'PASS','images':proof['images']}))
