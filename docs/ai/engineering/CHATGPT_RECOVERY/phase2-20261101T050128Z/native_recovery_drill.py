"""Official Native API replacement preview on disposable restored DB; no MAIN writes."""
from pathlib import Path
import json,os,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.main_native_clone import main_native_clone
RUN=Path(__file__).parent
backup=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/chatgpt-recovery-20261101T043043Z/postgres.dump'
images=json.loads((RUN/'candidate-images.json').read_text())
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('phase2-native-drill-'+uuid.uuid4().hex[:8])
PRIVATE.mkdir()
proposal={'subject':'[Recovery WP385] Category, filter and CSV export (AC10–AC12)',
 'description':{'format':'markdown','raw':'Replacement proposal for deleted WP385; this is a NEW record, not a restoration of Native history.\nForensic reference: CHATGPT_RECOVERY/WP385_FORENSICS.md; plan b1cca031-81f5-4df1-870b-cbeb23d51e66; unit feedback-b1c22888cba835bb.\nAC10: category on task POST/PATCH.\nAC11: GET /tasks?category=… filters tasks.\nAC12: GET /tasks/export/csv returns CSV.\nDependency: health-check-v1 / WP384.\nOwner approval required before MAIN create; preserve the old plan mapping as evidence.'},
 '_links':{'project':{'href':'/api/v3/projects/6'},'parent':{'href':'/api/v3/work_packages/379'},'status':{'href':'/api/v3/statuses/1'}}}
(RUN/'wp385-replacement-preview.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n')
ruby=r'''
require 'net/http'; require 'json'; require 'digest'
raise 'CLONE_ONLY' unless ENV['QLDAPM_TEST_ONLY']=='true' && ENV.fetch('DATABASE_URL').include?('@qa-db/')
input=JSON.parse(STDIN.read)
before=WorkPackage.where(project_id:5).order(:id).pluck(:id,:lock_version,:updated_at)
raise 'ORIGINAL_385_PRESENT' if WorkPackage.exists?(385)
token=Token::API.create_and_return_value(User.find(20))
call=lambda do |method,path,body=nil|
  uri=URI('http://localhost:8080'+path)
  req=Net::HTTP.const_get(method).new(uri);req.basic_auth('apikey',token)
  req['Content-Type']='application/json';req['Host']='localhost:8088'
  req.body=body.to_json if body
  response=Net::HTTP.start(uri.host,uri.port,read_timeout:90){|h|h.request(req)}
  [response.code.to_i,JSON.parse(response.body)]
end
identity=call.call('Get','/api/v3/users/me');raise 'ACTOR_NOT_PM20' unless identity[0]==200 && identity[1]['id']==20 && !identity[1]['admin']
base=call.call('Get','/api/v3/work_packages/384');raise 'DEPENDENCY_MISSING' unless base[0]==200
input['_links']['type']=base[1].fetch('_links').fetch('type').slice('href')
created=call.call('Post','/api/v3/work_packages',input)
unless created[0]==201
  puts({status:'CLONE_REPLACEMENT_BLOCKED',http_status:created[0],error_id:created[1]['errorIdentifier'],message:created[1]['message']}.to_json);exit 2
end
id=created[1]['id'];raise 'NEW_ID_REQUIRED' unless id && id!=385
readback=call.call('Get',"/api/v3/work_packages/#{id}")
raise 'READBACK_SCOPE' unless readback[0]==200 && readback[1].dig('_links','project','href')=='/api/v3/projects/6' && readback[1].dig('_links','parent','href')=='/api/v3/work_packages/379'
relation=call.call('Post',"/api/v3/work_packages/#{id}/relations",{'type'=>'follows','_links'=>{'from'=>{'href'=>"/api/v3/work_packages/#{id}"},'to'=>{'href'=>'/api/v3/work_packages/384'}}})
unless relation[0]==201
  puts({status:'CLONE_DEPENDENCY_BLOCKED',http_status:relation[0],error_id:relation[1]['errorIdentifier'],message:relation[1]['message']}.to_json);exit 3
end
relation_read=call.call('Get',relation[1].dig('_links','self','href'))
raise 'RELATION_READBACK_FAILED' unless relation_read[0]==200 && relation_read[1]['id']==relation[1]['id']
raise 'PROJECT5_CHANGED' unless before==WorkPackage.where(project_id:5).order(:id).pluck(:id,:lock_version,:updated_at)
puts({status:'CLONE_REPLACEMENT_API_VERIFIED',new_clone_id:id,project:6,parent:379,dependency:384,relation_type:relation[1]['type'],original_385_absent:!WorkPackage.exists?(385),project5_preserved:true,main_mutations:0}.to_json)
'''
result={'private_artifacts':str(PRIVATE)}
try:
    with main_native_clone(PRIVATE/'native-candidate-clone',candidate_web_image=images['core']['id'],source_dump_path=backup) as clone:
        # Code and payload are input only to a labelled disposable Core, never a MAIN name.
        p=subprocess.run(['docker','exec','-i',clone['web'],'bundle','exec','rails','runner',ruby],
            input=json.dumps(proposal).encode(),capture_output=True,timeout=150)
        (RUN/'native-replacement-clone.log').write_bytes(p.stdout+p.stderr)
        assert p.returncode==0,'replacement API clone failed; inspect sanitized log'
        result['replacement']=json.loads(p.stdout.decode().splitlines()[-1]);result['candidate_core_health']='PASS'
    # A fresh isolated restore starts the pinned serving rollback image against the same backup.
    with main_native_clone(PRIVATE/'native-rollback-clone',candidate_web_image='sha256:a4fa8150728bc5fc50f8afed22fce898cc52065a55ff0fdb53b803a81d9e1c6b',source_dump_path=backup):
        result['rollback_core_health']='PASS'
finally:(RUN/'native-recovery-drill-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
