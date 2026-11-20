"""Exactly one Owner-approved tests-only demo on existing BA/PM/delivery path."""
import importlib.util,json,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prior_e2e',OUT.parent/'telegram-observer/real_e2e.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
FEEDBACK='''Owner-approved Agent Studio V2 stabilization live demo, ceiling14: tạo đúng một unit mới chỉ thêm regression tests cho HTTP methods bị từ chối tại endpoint /healthz của mini-task-manager.
BA đọc implementation thực tế để xác định method/status/contract hiện tại. Không đổi app hoặc thêm endpoint; tests chỉ xác minh methods thực sự bị từ chối và không gây side effects lên Task data.
PM tạo đúng một Task mới, title mô tả rejected HTTP methods /healthz, scope tests-only. Không replay391/397 hoặc unit cũ.
Dev viết tests thật; Reviewer độc lập kiểm diff; QA chạy tests và lưu exit code, revision, artifacts.
Giữ model gemini-3.5-flash-lite, provider/key/call caps/quota/gates/runner hiện có. Không merge/deploy sản phẩm; chỉ READY FOR RELEASE, không tự Owner DONE.'''
def save(name,data):
    target=OUT/name;assert not target.exists(),'RECEIPT_ALREADY_EXISTS';target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    action=sys.argv[1]
    if action=='plan':
        assert not (OUT/'demo-plan.json').exists()
        source=prior.source()
        result=prior.command('engineering_plan',{'native_id':379,'lock_version':source['lock_version'],'feedback':FEEDBACK},'studio-methods-plan-20261106')
        save('demo-plan.json',result);print(json.dumps(result,ensure_ascii=False))
    elif action=='run':
        assert not (OUT/'demo-run.json').exists()
        plan_id=json.loads((OUT/'demo-plan.json').read_text())['result']['id']
        state=prior.command('engineering_status',{})['result'];plan=next(p for p in state['plans'] if p.get('id')==plan_id)
        assert plan['state']=='PUBLISHED' and plan.get('feedback')==FEEDBACK,'EXACT_BA_PM_HANDOFF_REQUIRED'
        units=[(u,t) for u,t in plan['native_units'].items() if t['state']!='DELIVERED'];assert len(units)==1
        unit,native=units[0];assert native['id'] not in {379,391,397}
        task=next(t for t in state['tasks'] if t['id']==native['id'])
        result=prior.command('engineering_run_once',{'native_id':task['id'],'lock_version':task['lock_version'],'unit':unit},'studio-methods-run-20261106')
        save('demo-run.json',result);save('demo-target.json',{'task_id':task['id'],'unit':unit,'plan_id':plan_id,'at':time.time()});print(json.dumps(result,ensure_ascii=False))
    elif action=='status':
        state=prior.command('engineering_status',{})['result'];plan_id=json.loads((OUT/'demo-plan.json').read_text())['result']['id']
        ids={plan_id};target=json.loads((OUT/'demo-target.json').read_text()) if (OUT/'demo-target.json').exists() else {}
        if (OUT/'demo-run.json').exists():ids.add(json.loads((OUT/'demo-run.json').read_text())['result']['id'])
        result={'at':time.time(),'mode':state.get('mode'),'worker':state.get('delivery_worker'),'plans':[p for p in state['plans'] if p.get('id')==plan_id],
                'runs':[r for r in state['runs'] if r['id'] in ids],'target':target}
        name='demo-status-'+str(int(time.time()))+'.json';save(name,result)
        print(json.dumps({'mode':result['mode'],'runs':[{k:r.get(k) for k in ['id','queue_state','native_id','result','checkpoint']} for r in result['runs']]},ensure_ascii=False))
    else:raise ValueError(action)
if __name__=='__main__':main()
