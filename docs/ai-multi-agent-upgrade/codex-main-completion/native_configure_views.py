"""Idempotent Native OpenProject API configuration; no work-package writes or direct SQL."""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode,unquote

OUT=Path(__file__).parent
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from gateway.native import Native,NativeError

def filter_value(name,operator='*',values=()):
    return {'_links':{'filter':{'href':'/api/v3/queries/filters/'+name},
                      'operator':{'href':'/api/v3/queries/operators/'+operator},
                      'values':[{'href':value} for value in values]}}

def filter_signature(filters):
    return sorted((f['_links']['filter']['href'].rsplit('/',1)[-1],
                   unquote(f['_links']['operator']['href'].rsplit('/',1)[-1]),
                   tuple(sorted(v['href'] for v in f['_links'].get('values',[])))) for f in filters)

class Configuration:
    def __init__(self,target):
        self.target=target
        runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
        if target=='clone':
            clone=json.loads((OUT/'clone.json').read_text())
            accounts=json.loads((Path(clone['private'])/'browser-accounts.json').read_text())['users']
            self.actor=next(a for a in accounts if a['role']=='PM')['id']
            self.token=next(a for a in accounts if a['role']=='PM')['token']
            # The DB is a Main clone; its existing card assignees remain Main actors19–23.
            self.users={'PM':19,'BA':20,'BE':21,'FE':22,'QA':23}
            self.base='http://127.0.0.1:18088'
        else:
            self.actor=19;self.token=json.loads((runtime/'gateway/credentials.json').read_text())['19']
            self.users={'PM':19,'BA':20,'BE':21,'FE':22,'QA':23};self.base='http://127.0.0.1:8088'
        who=Native(self.base,self.token,5).identity(self.actor)
        assert who['role']=='PM' and who['project_id']==5
        self.project='/api/v3/projects/5'
        self.events=[]
        self.started=time.monotonic()
        self.path=OUT/f'{target}-native-views-configuration.json'

    def call(self,path,method='GET',payload=None):
        assert time.monotonic()-self.started<300,'CONFIGURATION_TIME_BUDGET_EXHAUSTED'
        return Native(self.base,self.token,5).call(path,method,payload)

    def collection(self,path):
        return Native(self.base,self.token,5).collection(path)

    def record(self,kind,document,operation):
        self.events.append({'kind':kind,'id':document['id'],'name':document.get('name'),'operation':operation})
        self.path.write_text(json.dumps({'target':self.target,'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                                       'native_api_actor':self.actor,'events':self.events,'wp_writes':0,'completed':False},ensure_ascii=False,indent=2),encoding='utf8')

    def query(self,name,filters,timeline=False):
        existing=[q for q in self.queries if q.get('name')==name]
        assert len(existing)<=1,'DUPLICATE_QUERY_NAME'
        if existing:
            current=self.call('/api/v3/queries/'+str(existing[0]['id']))
            assert current['_links']['project']['href']==self.project and current['public'],'EXISTING_QUERY_SCOPE_OR_VISIBILITY_DIFFERS'
            assert current['timelineVisible']==timeline,'EXISTING_QUERY_DIFFERENT_DO_NOT_OVERWRITE'
            assert current['includeSubprojects'] is False and filter_signature(current['filters'])==filter_signature(filters),'EXISTING_QUERY_FILTERS_DIFFER_DO_NOT_OVERWRITE'
            self.record('query',current,'PRESERVED_EXISTING');return current
        payload={'name':name,'public':True,'includeSubprojects':False,'showHierarchies':timeline,
                 'timelineVisible':timeline,'filters':filters,
                 '_links':{'project':{'href':self.project},'sortBy':[{'href':'/api/v3/queries/sort_bys/id-asc'}],
                           'columns':[{'href':'/api/v3/queries/columns/'+c} for c in ('id','subject','type','status','assignee','startDate','dueDate')]}}
        created=self.call('/api/v3/queries','POST',payload)
        assert created['_links']['project']['href']==self.project and created['public']
        self.queries.append(created);self.record('query',created,'CREATED_NATIVE_SERVICE');return created

    def version(self,name):
        found=[v for v in self.versions if v['name']==name]
        assert len(found)<=1,'DUPLICATE_VERSION_NAME'
        if found:
            assert found[0]['_links']['definingProject']['href']==self.project,'VERSION_DEFINED_OUTSIDE_PROJECT'
            self.record('version',found[0],'PRESERVED_EXISTING');return found[0]
        created=self.call('/api/v3/versions','POST',{'name':name,'status':'open','sharing':'none','_links':{'definingProject':{'href':self.project}}})
        self.versions.append(created);self.record('version',created,'CREATED_UNDATED_NO_WP_ASSIGNMENT');return created

    def board(self,name,attribute,columns):
        found=[b for b in self.boards if b['name']==name]
        assert len(found)<=1,'DUPLICATE_BOARD_NAME'
        if found:
            current=self.call('/api/v3/grids/'+str(found[0]['id']))
            assert current['options']=={'type':'action','attribute':attribute},'EXISTING_BOARD_TYPE_DIFFERS_DO_NOT_OVERWRITE'
            assert len(current['widgets'])==len(columns),'EXISTING_COLUMNS_DIFFER_DO_NOT_OVERWRITE'
            for widget,(_,_,expected) in zip(sorted(current['widgets'],key=lambda w:w['startColumn']),columns):
                assert widget['options']['filters']==[expected],'EXISTING_BOARD_FILTERS_DIFFER_DO_NOT_OVERWRITE'
            self.record('board',current,'PRESERVED_EXISTING');return current
        widgets=[]
        for index,(column_name,api_filter,widget_filter) in enumerate(columns):
            filters=[filter_value('status')]+([api_filter] if api_filter else [])
            if attribute=='status':filters=[api_filter]
            query=self.query(name+' — '+column_name,filters)
            widgets.append({'identifier':'work_package_query','startRow':1,'endRow':2,'startColumn':index+1,'endColumn':index+2,
                            'options':{'queryId':query['id'],'filters':[widget_filter]}})
        document=self.call('/api/v3/grids','POST',{'name':name,'rowCount':1,'columnCount':len(columns),
                      'options':{'type':'action','attribute':attribute},'widgets':widgets,
                      '_links':{'scope':{'href':'/projects/qldapm-local/boards'}}})
        assert document['_links']['project']['href']==self.project and len(document['widgets'])==len(columns)
        self.boards.append(document);self.record('board',document,'CREATED_NATIVE_SERVICE');return document

    def apply(self):
        project_filter=urlencode({'filters':json.dumps([{'project':{'operator':'=','values':['5']}}])})
        self.queries=self.collection('/api/v3/queries?'+project_filter)
        self.boards=self.collection('/api/v3/grids?'+urlencode({'filters':json.dumps([{'scope':{'operator':'=','values':['/projects/qldapm-local/boards']}}])}))
        self.versions=self.collection('/api/v3/projects/5/versions')
        self.query('QLDAPM — Scrum Roadmap theo Epic',[filter_value('status')],timeline=True)
        statuses=self.collection('/api/v3/statuses')
        columns=[]
        for title in ('NEW','IN PROGRESS','CODE REVIEW','READY FOR TEST','IN TESTING','READY FOR RELEASE','DONE'):
            matches=[s for s in statuses if s['name'].upper()==title];assert len(matches)==1,'NATIVE_STATUS_NAME_AMBIGUOUS'
            identifier=matches[0]['id'];columns.append((title,filter_value('status','=',[f'/api/v3/statuses/{identifier}']),{'status_id':{'operator':'=','values':[str(identifier)]}}))
        self.board('QLDAPM — Main Scrum Kanban Board','status',columns)
        columns=[(role,filter_value('assignee','=',[f'/api/v3/users/{actor}']),{'assigned_to_id':{'operator':'=','values':[str(actor)]}}) for role,actor in self.users.items()]
        columns.append(('Unassigned',filter_value('assignee','!*'),{'assigned_to_id':{'operator':'!*','values':[]}}))
        self.board('QLDAPM — Team Workload & Assignee Board','assignee',columns)
        columns=[]
        for identifier in range(38,43):
            wp=self.call(f'/api/v3/work_packages/{identifier}')
            assert wp['_links']['project']['href']==self.project and wp['_links']['type']['title']=='Epic'
            columns.append((f'Epic #{identifier}: '+wp['subject'],filter_value('parent','=',[f'/api/v3/work_packages/{identifier}']),{'parent':{'operator':'=','values':[str(identifier)]}}))
        self.board('QLDAPM — Epic Breakdown & Subtasks Board','subtasks',columns)
        columns=[]
        for i in range(1,5):
            version=self.version('Sprint '+str(i));identifier=version['id']
            columns.append((version['name'],filter_value('version','=',[f'/api/v3/versions/{identifier}']),{'version_id':{'operator':'=','values':[str(identifier)]}}))
        self.board('QLDAPM — Roadmap & Milestone Board','version',columns)
        result=json.loads(self.path.read_text(encoding='utf8'));result['completed']=True
        self.path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps({'target':self.target,'completed':True,'events':len(self.events),'wp_writes':0}))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target',choices=('clone','main'),default='clone')
    args=parser.parse_args()
    if args.target=='main':
        assert json.loads((OUT/'native-views-clone-qualification.json').read_text())['passed'],'CLONE_CONFIGURATION_NOT_QUALIFIED'
        assert json.loads((OUT/'fresh-backup-restore.json').read_text())['passed']
    Configuration(args.target).apply()

if __name__=='__main__':main()
