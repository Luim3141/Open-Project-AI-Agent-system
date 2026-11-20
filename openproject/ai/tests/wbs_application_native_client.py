import datetime,json,pathlib,uuid
from unittest.mock import patch
from gateway.native import Native,NativeError
from gateway.service import Service
from gateway.store import Store,canonical,digest
from gateway.vector_client import VectorClient
root=pathlib.Path('/qualification');clone=json.loads((root/'clone.json').read_text());assert clone['base_url']=='http://web:8080' and __import__('os').environ.get('QLDAPM_APPLICATION_QUALIFICATION')==clone['id'],'ISOLATED_APPLICATION_ONLY';keys=json.loads((root/'credentials.json').read_text());config=json.loads((root/'config.json').read_text());config['openproject_url']=clone['base_url'];store=Store(root/'state');(store.root/'ui.key').write_bytes((root/'ui.key').read_bytes());service=Service(store,config,root/'workspace');created=set();decisions=[];checks=[];original_max=clone['original_max_wp_id']
def provider_ledger():
 with store.connect() as db:
  return {'receipts':[tuple(r) for r in db.execute('select id,project,actor,run_id,document from gemini_call_receipts order by id')],
   'usage':[tuple(r) for r in db.execute('select rowid,project,at,input_tokens from gemini_usage order by rowid')]}
provider_before=provider_ledger()

def native(actor):return Native(clone['base_url'],keys[str(actor)],5)
tokens={actor:store.issue_token(actor,native(actor).identity(actor)['role'],keys[str(actor)]) for actor in [18,19,20,21,22,23]}
vector=VectorClient(qdrant_url='http://fixture-vector:6333');assert vector.ensure_collection();vector.embed_texts=lambda texts:[[0.01]*1024 for _ in texts]
def command(action,args,key=None,actor=18):return service.execute(tokens[actor],{'action':action,'arguments':args,'idempotency_key':('app-qa-'+clone['id']+'-'+key) if key else None})['result']
def approve(p):
 assert p['command']['action'] in {'create_work_package','create_dependency'},'FIXED_WBS_MUTATIONS_ONLY'
 args=p['command']['arguments']
 if p['command']['action']=='create_work_package' and args.get('parent_id'):assert args['parent_id']>original_max,'ORIGINAL_PARENT_MUTATION_DENIED'
 if p['command']['action']=='create_dependency':assert args['predecessor_id']>original_max and args['successor_id']>original_max,'ORIGINAL_RELATION_ENDPOINT_DENIED'
 decisions.append({'id':p['id'],'hash':p['hash'],'authorization_kind':'SIMULATED_ISOLATED_FIXTURE_NOT_MAIN_HUMAN_APPROVAL'})
 result=service.decide_proposal(tokens[18],p['id'],'approve',p['hash'])
 if p['command']['action']=='create_work_package':assert result['result']['id']>original_max;created.add(result['result']['id'])
 return result
def settle():
 report=command('knowledge_incremental_sync',{},'scan-'+str(uuid.uuid4()));assert all(job['native_id'] in created for job in report['jobs']),'ORIGINAL_NATIVE_SOURCE_DRIFT_OUTSIDE_FIXTURE'
 with patch('gateway.vector_client.VectorClient',return_value=vector),patch.object(vector,'close'):
  for _ in range(20):
   with store.connect() as db:pending=[dict(row) for row in db.execute("select id,native_id,state from knowledge_sync where state!='verified'")]
   assert all(row['native_id'] in created for row in pending),'UNRELATED_SYNC_JOB_OUTSIDE_FIXTURE'
   if not pending:return
   assert service.process_knowledge_sync(),'CACHE_RETRY_NOT_READY_OR_NO_JOB'
 raise AssertionError('FIXTURE_RAG_NOT_SETTLED')
import atexit
@atexit.register
def diagnostic():
 if 'plan' not in globals() or not created:return
 try:
  (root/'final-progress.json').write_text(json.dumps(command('wbs_get',{'id':plan['id']}),indent=2))
  (root/'final-native.json').write_text(json.dumps({str(i):{'package':native(18).package(i),'hierarchy':native(18).call('/api/v3/qldapm/wbs_hierarchy/'+str(i))} for i in created},indent=2))
  with store.connect() as db:(root/'final-wbs-documents.json').write_text(json.dumps([json.loads(row[0]) for row in db.execute('select document from wbs_documents')],indent=2))
 except Exception as error:(root/'diagnostic-error.txt').write_text(type(error).__name__+':'+str(error)[:300])

run_id='f04b5c59-26dc-40af-b999-00298b298ca0';run=command('get_ai_run',{'id':run_id},actor=20);output=next(o for o in run['result']['agent_outputs'] if o['agent']=='ba');source_hash=digest(canonical(output));assert source_hash=='4bcbbd93eeb110f99bab1b66846c814cda1af09ded78d2a18c209a63121a9ae7';raw_plan=json.loads(output['result']['summary']);assert raw_plan['schema']=='QLDAPM_WBS_V2'
draft=command('wbs_from_ba',{'run_id':run_id,'output_hash':source_hash,'share_for_review':True},'fresh-model-convert',20);assert draft['origin']['output_hash']==source_hash and draft['origin']['native_key_mapping']=={'EPIC-1':'epic-1','TASK-A':'task-a','SUB-A':'sub-a','TASK-B':'task-b'}
assert digest(canonical(next(o for o in command('get_ai_run',{'id':run_id},actor=20)['result']['agent_outputs'] if o['agent']=='ba')))==source_hash
from gateway.native_wbs import specification
import copy
from gateway.wbs_analysis import native_keys
negative,_=native_keys(copy.deepcopy(raw_plan));negative.pop('schema');negative['share_for_review']=True;negative['relations'].append({'predecessor':'task-b','successor':'task-a','lag':0})
try:specification(service,negative);raise AssertionError('CYCLIC_GENERATED_GRAPH_ACCEPTED')
except ValueError as error:assert 'CYCLE' in str(error)
plan=command('wbs_adopt',{'id':draft['id'],'hash':draft['hash']},'fresh-model-adopt');model_ids=[];lost_posts=[]
for index in range(4):
 value=command('wbs_next',{'id':plan['id'],'hash':plan['hash']},'fresh-node-'+str(index));(root/('progress-'+str(index)+'.json')).write_text(json.dumps(value,indent=2))
 if value['state']!='AWAITING_APPROVAL':
  (root/('native-progress-'+str(index)+'.json')).write_text(json.dumps({str(i):{'package':native(18).package(i),'hierarchy':native(18).call('/api/v3/qldapm/wbs_hierarchy/'+str(i))} for i in created},indent=2))
 assert value['state']=='AWAITING_APPROVAL',value['state'];p=value['proposal'];node=next(n for n in draft['spec']['nodes'] if n['key']==value['node_key'])
 for key in ['start_date','due_date']:
  if key in node:assert p['command']['arguments'][key]==node[key]
 if index==1:
  original=Native.call
  def lose(self,path,method='GET',payload=None,**kwargs):
   result=original(self,path,method,payload,**kwargs)
   if path=='/api/v3/work_packages' and method=='POST':lost_posts.append(result['id']);created.add(result['id']);raise NativeError(503,'ISOLATED_FRESH_MODEL_NODE_ACK_LOST_AFTER_COMMIT')
   return result
  with patch.object(Native,'call',lose):
   try:approve(p);raise AssertionError('NODE_ACK_LOSS_NOT_OBSERVED')
   except NativeError as error:assert error.status==503
  assert len(lost_posts)==1;service=Service(Store(root/'state'),config,root/'workspace');hold=command('wbs_next',{'id':plan['id'],'hash':plan['hash']},'fresh-node-hold');assert hold['state']=='UNKNOWN_HOLD'
  result=command('reconcile_request',{'key':'proposal-'+p['id']});assert result['reconciled'];model_ids.append(result['result']['id'])
 else:result=approve(p);model_ids.append(result['result']['id'])
 settle()
state=command('wbs_get',{'id':plan['id']})['progress'];assert state['state']=='READY_FOR_DEPENDENCIES'
value=command('wbs_next',{'id':plan['id'],'hash':plan['hash']},'fresh-model-relation');p=value['proposal'];assert p['command']['action']=='create_dependency';assert p['command']['arguments']['lag']==0;receipt=approve(p);settle();state=command('wbs_get',{'id':plan['id']})['progress'];assert state['state']=='VERIFIED_COMPLETED',state['state'];assert state['relations'][0]['state']=='VERIFIED'
ids=state['native_ids'];n=native(18);packages={key:n.package(identifier) for key,identifier in ids.items()};assert packages['task-a']['startDate']==packages['task-a']['dueDate']=='2026-10-26' and packages['sub-a']['startDate']==packages['sub-a']['dueDate']=='2026-10-26' and packages['task-b']['startDate']==packages['task-b']['dueDate']=='2026-10-27'
assert packages['task-a']['_links']['parent']['href']=='/api/v3/work_packages/'+str(ids['epic-1']);assert packages['sub-a']['_links']['parent']['href']=='/api/v3/work_packages/'+str(ids['task-a']);assert packages['task-b']['_links']['parent']['href']=='/api/v3/work_packages/'+str(ids['epic-1'])
relation=n.call('/api/v3/relations/'+str(state['relations'][0]['native_relation_id']));assert relation['type']=='follows' and relation['lag']==0 and relation['_links']['from']['href']=='/api/v3/work_packages/'+str(ids['task-b']) and relation['_links']['to']['href']=='/api/v3/work_packages/'+str(ids['task-a'])
with patch('gateway.vector_client.VectorClient',return_value=vector),patch.object(vector,'close'):
 citations=command('knowledge_search',{'query':'Requirement trace','native_ids':sorted(created),'limit':20})
assert citations['items'] and {item['native_id'] for item in citations['items']}<=created
for item in citations['items']:assert item['lock_version']==n.package(item['native_id'])['lockVersion'] and item.get('citation'),item
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(store.root/'knowledge.sqlite')));documents=[d for d in storage.query_documents('5') if d.metadata.get('native_id') in created];points={str(point['id']):point['payload'] for point in vector.scroll_points('5')};count=0
for document in documents:
 assert document.metadata['lock_version']==n.package(document.metadata['native_id'])['lockVersion']
 for chunk in storage._mock_tables[f'{storage.schema_name}.knowledge_chunks'].values():
  if chunk['document_id']!=document.source_hash:continue
  count+=1;point=points[vector.deterministic_uuid(document.source_hash+':'+str(chunk['chunk_index']))];assert point['document_id']==document.source_hash and point['chunk_hash']==chunk['chunk_hash'] and point['metadata']==document.metadata
assert count==len(points) and len({d.metadata['native_id'] for d in documents})==4
assert provider_ledger()==provider_before,'PROVIDER_LEDGER_CHANGED_WITHOUT_AUTHORIZED_GENERATION'
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_RETAINED_BA_TO_ISOLATED_NATIVE_WBS_RELATION_SCHEDULE_RAG_RECOVERY','run_id':run_id,'output_hash':source_hash,'native_key_mapping':draft['origin']['native_key_mapping'],'raw_ba_output_unchanged':True,'plan_hash':plan['hash'],'progress':state,'native_readback':{key:{'id':item['id'],'version':item['lockVersion'],'type':item['_links']['type']['title'],'status':item['_links']['status']['title'],'startDate':item.get('startDate'),'dueDate':item.get('dueDate'),'parent':item['_links'].get('parent',{}).get('href')} for key,item in packages.items()},'cyclic_graph_rejected':True,'lost_node_response_reconciled_one_create':len(lost_posts)==1,'fixture_decisions':decisions,'citations':citations,'target_documents':len(documents),'target_points':count,'candidate_images':clone['images'],'gateway_image':clone['gateway_image'],'provider_ledger_preserved':True,'provider_counts_before':{k:len(v) for k,v in provider_before.items()},'main_native_writes':0,'new_model_calls_in_clone':0,'main_human_decisions_by_agent':0,'staging_operations':False,'limits':['Real BA run generated once on Main under exact human egress approval; no regenerated or edited model business output','Identifier encoding only, explicitly recorded; all graph/business fields preserved','Every Native node and relation decision is SIMULATED_ISOLATED_FIXTURE, not Main human approval','Actual Native/PG/SQLite/FTS/Qdrant; synthetic1024embeddings, no dense semantic quality claim','No Main WBS proposal/create or whole-application QA closure claim']};(root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)
vector.close()
