import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(root/'openproject/ai'))
from automation.main_native_clone import main_native_clone
out=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/stabilization-inspector-final-core-20261102'
out.mkdir(parents=True,exist_ok=False)
image='sha256:00f1e372ded7dc3ee0bcb02275233e0baad08990893f8d1c27511b5a66cb9cd8'
ruby=r'''
require 'net/http';require 'json'
raise 'CLONE_ONLY' unless ENV['QLDAPM_TEST_ONLY']=='true' && ENV.fetch('DATABASE_URL').include?('@qa-db/')
token=Token::API.create_and_return_value(User.find(20))
get=lambda do |path|
 uri=URI('http://localhost:8080'+path); req=Net::HTTP::Get.new(uri);req.basic_auth('apikey',token);req['Host']='localhost:8088'
 r=Net::HTTP.start(uri.host,uri.port,read_timeout:30){|h|h.request(req)}; [r.code.to_i,JSON.parse(r.body)]
end
who=get.call('/api/v3/users/me');project=get.call('/api/v3/projects/6')
raise 'READBACK_FAILED' unless who[0]==200 && who[1]['id']==20 && project[0]==200 && project[1]['id']==6
puts({identity:20,project:6,api:'PASS'}.to_json)
'''
with main_native_clone(out/'clone',candidate_web_image=image) as clone:
 p=subprocess.run(['docker','exec','-i',clone['web'],'bundle','exec','rails','runner',ruby],capture_output=True,timeout=150)
 if p.returncode:
  (out/'clone-error.log').write_bytes(p.stdout+p.stderr)
  raise RuntimeError('CLONE_API_FAILED_PRIVATE_LOG')
 result=json.loads(p.stdout.decode().splitlines()[-1]);result.update({'status':'PASS','candidate':image,'isolated':True})
 (Path(__file__).parent/'inspector-final-core-clone-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
