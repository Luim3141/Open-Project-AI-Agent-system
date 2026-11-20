"""Date and intent acceptance on owned staging fixtures; preserve PM-only-write policy."""
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from tests.rbac_stage import command, native, bootstrap, credentials

path = Path('artifacts/dates-stage.json')
report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
    'source': 'AI-DATES-' + uuid.uuid4().hex, 'created': [], 'checks': [], 'runs': []}


def save():
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def check(text):
    report['checks'].append(text)
    save()
    print(text, flush=True)


def snapshot():
    return [{**{k:r.get(k) for k in ('id','subject','description','startDate','dueDate','lockVersion','updatedAt','percentageDone')},
        'links':{k:r['_links'].get(k) for k in ('parent','type','status','assignee','priority')},
        'custom':{k:v for k,v in r.items() if k.startswith('customField')}}
        for r in sorted(native().packages(),key=lambda r:r['id']) if r['id'] not in report['created']]


def update(changes, label, status=200):
    item=native().package(report['child'])
    return command('PM','update_work_package',{'id':item['id'],'lock_version':item['lockVersion'],'changes':changes},
        report['source']+'-'+label,True,status)


def native_matrix():
    if not report['created']:
        report['baseline']=snapshot()
        save()
        for label,type_name in (('parent','Task'),('child','Subtask')):
            args={'subject':report['source']+' '+label,'source_id':report['source']+'-'+label,
                'type_id':bootstrap['types'][type_name],'assignee_role':'BE'}
            if label=='child':args['parent_id']=report['parent']
            item=command('PM','create_work_package',args,report['source']+'-'+label,True)
            report[label]=item['id'];report['created'].append(item['id']);save()
    assert all(native().package(id)['subject'].startswith(report['source']) for id in report['created'])
    item=update({'start_date':'2026-10-10','due_date':'2026-12-31'},'native-pair-canonical')
    assert (item['startDate'],item['dueDate'])==('2026-10-12','2026-12-31')
    assert item['date_adjustments']['start_date']['requested']=='2026-10-10'
    update({'start_date':'2027-01-01'},'invalid-range',409)
    update({'start_date':'2026-02-31'},'invalid-date',409)
    actual=native().package(report['child'])
    assert actual['lockVersion']==item['lockVersion']
    for role in ('BA-PM','BE','FE','QA'):
        args={'id':actual['id'],'lock_version':actual['lockVersion'],'changes':{'start_date':'2026-10-01','due_date':'2026-10-20'}}
        command(role,'update_work_package',args,report['source']+'-deny-'+role,True,403)
    assert native().package(report['child'])['lockVersion']==item['lockVersion']
    item=update({'start_date':None,'due_date':None},'clear-native')
    assert item['startDate'] is None and item['dueDate'] is None
    assert snapshot()==report['baseline']
    check('Native atomic date pair/readback, invalid range/date rejected, both dates clear, four non-PM roles denied')


def run(label,prompt,allow=True):
    args={'prompt':prompt,'allow_routine_writes':allow,'write_scope_ids':[]}
    started=command('PM','start_ai_run',args,report['source']+'-'+label)
    report['runs'].append({'label':label,'id':started['id'],'prompt':prompt});save()
    deadline=time.monotonic()+650
    while True:
        result=command('PM','get_ai_run',{'id':started['id']})
        if result['state']!='running':break
        assert time.monotonic()<deadline
        time.sleep(2)
    report['runs'][-1]['result']=result;save()
    assert result['state']=='done', 'No retry of sent inference or uncertain write; receipts saved'
    assert not any(t.get('result',{}).get('error') for t in result['result'].get('tools',[]))
    print(label+': '+result['result']['status'],flush=True)
    return result['result']


def google_matrix():
    identifier=report['child']
    result=run('set-dates',f'set ngày bắt đầu và ngày kết thúc cho task {identifier} là từ ngày 10/10/2026 đến ngày 31/12/2026')
    writes=[t for t in result['tools'] if t['action']=='update_work_package']
    assert len(writes)==1 and {'start_date','due_date'}<=set(writes[0]['arguments']['changes'])
    item=native().package(identifier)
    assert (item['startDate'],item['dueDate'])==('2026-10-12','2026-12-31')
    assert 'lịch làm việc' in result['text']
    check('Real Gemini exact user wording set dates: both ISO dates in one update, native readback')
    update({'start_date':None,'due_date':None},'clear-for-deadline')
    run('add-deadline',f'thêm deadline cho subtask {identifier} là vào ngày 31/12/2026')
    item=native().package(identifier)
    assert item['dueDate']=='2026-12-31'
    check('Real Gemini thêm deadline: only due_date requested; native scheduling may derive start from retained duration')
    assert snapshot()==report['baseline']


def cleanup():
    ruby=f'''raise "STAGING_ONLY" unless User.exists?(login:"stage-owner") && !User.exists?(login:"op-owner")
field=WorkPackageCustomField.find_by!(name:"Source ID")
User.execute_as(User.find_by!(login:"pm")) do
 {list(reversed(report['created']))}.each do |id|
  item=WorkPackage.find(id)
  raise "OTHER_FIXTURE" unless item.project_id==3 && item.author_id==User.current.id && item.custom_value_for(field).value.to_s.start_with?("{report['source']}") && !item.children.exists?
  Qldapm::MutationReceipt.where(work_package_id:id).delete_all
  Thread.current[:qldapm_approved_delete]=id
  item.destroy!
 ensure
  Thread.current[:qldapm_approved_delete]=nil
 end
end
puts "Owned date fixtures removed"
'''
    result=subprocess.run(['docker','exec','-i','qldapm-ai-stage-staging-web-1','bundle','exec','rails','runner','-'],
        input=ruby,text=True,capture_output=True,timeout=180)
    Path('artifacts/dates-cleanup-native.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode==0,'Exact fixture cleanup failed; inspect saved IDs'
    assert snapshot()==report['baseline'],'Source changed; do not undo human edits'
    report['cleaned']=True
    check('Owned date fixtures removed; all source business/version fields preserved')


if __name__=='__main__':
    {'native':native_matrix,'google':google_matrix,'cleanup':cleanup}[sys.argv[1]]()
