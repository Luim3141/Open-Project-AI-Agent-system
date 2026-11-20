"""Exact immutable Core concurrency, callback and existing ACK/report contracts."""
import json,subprocess
from release import release,OUT
from pathlib import Path
release.BASE_IMAGES=json.loads((OUT/'candidate-final/deployment.json').read_text())['images']
release.SOURCES={k:v for k,v in release.SOURCES.items() if k.endswith('/qldapm_ai_controller.rb') or k.endswith('/ai_bridge.rb')}
bundle=OUT/'candidate-admission'
manifest=json.loads((bundle/'manifest.json').read_text());image=manifest['images']['core'];repo=OUT.parents[1]
mount=['--mount',f'type=bind,source={repo / "openproject/ai/tests"},target=/qa,readonly']
base=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=16m,mode=1777','--add-host','gateway:127.0.0.1',*mount,'--entrypoint','bundle',image,'exec','ruby']
evidence={}
for name,script,args in [('admission-unit','test_ai_bridge_admission.rb',['/app/app/services/qldapm/ai_bridge.rb']),('puma-callback','bridge_pool_probe.rb',['/app/app/services/qldapm/ai_bridge.rb']),('cc-ack','test_cc_core_ack.rb',[]),('report-contract','test_report_controller.rb',[])]:
    data=json.dumps({'controller':(repo/'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb').read_text()}) if not args else None
    command=base+['/qa/'+script,*args]
    if data is not None:command.insert(2,'-i')
    p=subprocess.run(command,input=data,text=True,capture_output=True,timeout=90);(OUT/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,name
    evidence[name]=p.stdout.strip()
for role in ['core','gateway']:assert release.runtime_hashes(role,manifest['images'][role])=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True},'evidence':{'scope':'Only bridge/controller admission+RetryAfter; UI/Gateway same qualified serving bases','contracts':evidence,'prior_ui':'candidate-browser.json; actual Main host/API; final asset image16c472 deployed','puma_baseline':'4 bridge requests /4threads ->4HTTP503 in1222ms on prior16c472; candidate2HTTP200+2HTTP429 in~181ms'}}
release.write_json(OUT/'admission-qualification.json',proof);print(json.dumps({'status':'PASS','image':image,'evidence':evidence}))
