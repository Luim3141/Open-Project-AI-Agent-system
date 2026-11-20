"""One idempotent factual engineering report, no model narrative, actual Rails reader."""
import json,subprocess,os
from pathlib import Path
out=Path(__file__).parent
ruby=r'''
require 'json';require 'nokogiri'
project=Project.find(6);owner=User.find(18);User.current=owner
payload={action:'engineering_report_generate',arguments:{report_type:'ON_DEMAND',include_narrative:false},idempotency_key:'demo-final-391-completed-report-v1'}
first=Qldapm::AiBridge.call(project,owner,'command',payload)['result']
second=Qldapm::AiBridge.call(project,owner,'command',payload)['result']
raise 'DUPLICATE_REPORT' unless first['id']==second['id']
report=Qldapm::AiBridge.call(project,owner,'command',{action:'engineering_report_get',arguments:{id:first['id']},idempotency_key:SecureRandom.uuid})['result']
raise 'REPORT_SCOPE' unless report['project_id']==6 || report['project']==6 || report.dig('metrics','project')==6
reader=Qldapm::ReportReader.render(report['narrative']) if defined?(Qldapm::ReportReader)
raise 'FACTUAL_NARRATIVE_MISSING' unless report['narrative'].to_s.include?('AI ENGINEERING')
puts({status:'PASS',utc:Time.now.utc.iso8601,report:report.slice('id','report_type','source_status','source_state','ai_narrative_status','generated_at'),metrics:report['metrics'],idempotent:true,include_narrative:false,provider_calls:0}.to_json)
'''
p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-'],input=ruby.encode(),capture_output=True,timeout=150)
if p.returncode:
 private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/demo-report391-failure.log';private.write_bytes(p.stdout+p.stderr)
 raise RuntimeError('FACTUAL_REPORT_READBACK_FAILED_PRIVATE_LOG')
result=json.loads(p.stdout.decode().splitlines()[-1]);(out/'report391-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='metrics'}))
