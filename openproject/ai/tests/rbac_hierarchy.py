"""PM Epic/Task/Subtask native forms and parent links, with exact owned cleanup."""
import json
import subprocess
import uuid
from rbac_stage import ROOT, WEB, command, native, bootstrap, snapshot, canonical

path=ROOT/'artifacts/rbac-hierarchy.json'
assert not path.exists(), 'Do not replay a hierarchy acceptance manifest'
source='RBAC-HIERARCHY-'+uuid.uuid4().hex
evidence={'source':source,'created':[]}
baseline=snapshot()
for kind in ('Epic','Task','Subtask'):
    args={'source_id':source+'-'+kind,'subject':source+' '+kind,'type_id':bootstrap['types'][kind],'assignee_role':'BE'}
    if evidence['created']: args['parent_id']=evidence['created'][-1]
    item=command('PM','create_work_package',args,source+'-'+kind,True)
    evidence['created'].append(item['id'])
    path.write_text(canonical(evidence),encoding='utf-8')
    actual=native().package(item['id'])
    assert actual['subject']==args['subject']
    if 'parent_id' in args: assert actual['_links']['parent']['href'].endswith('/'+str(args['parent_id']))
assert len(evidence['created'])==3
ruby=f'''raise "STAGING_ONLY" unless User.exists?(login:"stage-owner") && !User.exists?(login:"op-owner")
field=WorkPackageCustomField.find_by!(name:"Source ID")
User.execute_as(User.find_by!(login:"pm")) do
 {list(reversed(evidence['created']))!r}.each do |id|
  item=WorkPackage.find(id)
  raise "UNOWNED_FIXTURE" unless item.project_id==3 && item.custom_value_for(field).value.to_s.start_with?("{source}") && !item.children.exists?
  Thread.current[:qldapm_approved_delete]=id
  item.destroy!
 ensure
  Thread.current[:qldapm_approved_delete]=nil
 end
end
puts "PM approved exact hierarchy deletion PASS"
'''
result=subprocess.run(['docker','exec','-i',WEB,'bundle','exec','rails','runner','-'],input=ruby,text=True,capture_output=True,timeout=180)
assert result.returncode==0, result.stderr[-1000:]
assert snapshot()==baseline, 'Existing Work Packages changed'
evidence.update(passed=True,cleaned=True)
path.write_text(canonical(evidence),encoding='utf-8')
print('PM Epic -> Task -> Subtask create/parent/readback/approved delete PASS; all original records preserved')
