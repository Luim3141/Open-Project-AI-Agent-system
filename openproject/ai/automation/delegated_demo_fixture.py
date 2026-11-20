"""Create one controlled non-coding Project6 Bug fixture as its own service user."""
import re

def create_fixture(native,principal,source_field,marker):
    if native.project_id!=6 or type(principal) is not int or principal<=23 or not re.fullmatch('OWNER-DELEGATED-[a-f0-9]{12}',marker):
        raise ValueError('DELEGATED_FIXTURE_SCOPE_REQUIRED')
    who=native.identity(principal)
    if who.get('role')!='PM':raise PermissionError('DELEGATED_FIXTURE_PM_REQUIRED')
    item=native.call('/api/v3/work_packages','POST',{'subject':'[Bug] '+marker,
        'description':{'format':'markdown','raw':marker+'\nDelegated fixture state: BASELINE'},source_field:marker,
        '_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/1'}}})
    assert item['_links']['project']['href']=='/api/v3/projects/6'
    current=int(item['_links']['status']['href'].rsplit('/',1)[1])
    form=native.call(f"/api/v3/work_packages/{item['id']}/form",'POST',{'lockVersion':item['lockVersion']})
    values=form.get('_embedded',{}).get('schema',{}).get('status',{}).get('_embedded',{}).get('allowedValues',[])
    candidates=[row for row in values if type(row.get('id')) is int and row['id']!=current and not row.get('isClosed')]
    candidates.sort(key=lambda row:(re.sub('[^A-Z]','',row.get('name','').upper()) not in {'INPROGRESS','TODO','CODING'},row['id']))
    if not candidates:raise ValueError('DELEGATED_FIXTURE_NO_NATIVE_TRANSITION_RECONCILE_CREATED_FIXTURE')
    target=candidates[0]['id']
    return {'policy':{'principal_id':principal,'owner_grant':'dd43ae4b5fb4646fa614e7d5d4ae166b127cf8e5fbd653b3382a4a1366c151c4',
                     'fixtures':{str(item['id']):{'marker':marker,'type_id':1,'transitions':[[current,target]]}}},
            'fixture':{'native_id':item['id'],'lock_version':item['lockVersion'],'initial_status':current,'target_status':target,'marker':marker}}
