path = 'openproject/ai/automation/engineering_delivery.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = "knowledge=journal.step('planning-knowledge',lambda:knowledge_retry(worker,journal,next(iter(plan['native_units'].values()))['id']))"
replacement = "target_child=next((v['id'] for k,v in plan.get('native_units',{}).items() if v.get('state')=='PLANNED'),next(iter(plan['native_units'].values()))['id'])\n            knowledge=journal.step('planning-knowledge',lambda:knowledge_retry(worker,journal,target_child))"

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('PATCH_DELIVERY_SUCCESS')
else:
    print('TARGET_NOT_FOUND')
