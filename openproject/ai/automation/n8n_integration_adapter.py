"""Attach fixed metadata/machine branches; existing authenticated human branches remain intact."""
import copy

WORKFLOWS={'WF01','WF02','WF03','WF04','WF05','WF06','WF08','WF09','WF10','WF11','WF13','WF14','WF15'}
PROJECT6_BUSINESS={'WF08','WF09','WF10'}


def enable_project6_business(workflow):
    """Keep legacy scope; expose only read/draft/proposal contracts for explicit Project6."""
    spec=copy.deepcopy(workflow);code=spec['name'][:4]
    if code not in PROJECT6_BUSINESS:return spec
    identifier='sprint_parameters' if code=='WF08' else 'explicit_request'
    nodes=[n for n in spec['nodes'] if n['id']==identifier and n['type']=='n8n-nodes-base.code']
    if len(nodes)!=1:raise ValueError('PROJECT6_BUSINESS_SOURCE_CONTRACT_CHANGED')
    source=nodes[0]['parameters']['jsCode']
    marker='// QLDAPM explicit Project6 business scope v1'
    if source.startswith(marker):return spec
    nodes[0]['parameters']['jsCode']=marker+"""
const requested=$input.first().json.body || {};
if (Object.hasOwn(requested,'project_id') && requested.project_id!==6)
  return [{json:{action:'INVALID_WORKFLOW_PROJECT_SCOPE'}}];
const routed=(()=>{
"""+source+"""
})();
if (!Object.hasOwn(requested,'project_id')) return routed;
const allowed=new Set(['sprint_risks','get_work_package','bug_triage','bug_propose','wbs_draft','wbs_get','get_project_options']);
return routed.map(item=>allowed.has(item.json.action)
  ? {json:{...item.json,project_id:6}}
  : {json:{action:'INVALID_PROJECT6_WORKFLOW_ACTION'}});
"""
    return spec


def enable_project6_files(source):
    replacements=(
        ("['id','path','file_path','content','project_id'].some(k=>Object.hasOwn(fileBody,k)))",
         "['id','path','file_path','content'].some(k=>Object.hasOwn(fileBody,k)) || (Object.hasOwn(fileBody,'project_id') && fileBody.project_id!==6))"),
        ("const args={source_key:fileBody.source_key};", "const args={source_key:fileBody.source_key};\n  const scope=Object.hasOwn(fileBody,'project_id')?{project_id:6}:{};"),
        ("action:'knowledge_file_search',arguments:args}}", "action:'knowledge_file_search',arguments:args,...scope}}"),
        ("action:'knowledge_file_read',arguments:{...args,document_id:fileBody.document_id}}}", "action:'knowledge_file_read',arguments:{...args,document_id:fileBody.document_id},...scope}}"),
        ("idempotency_key:'wf01-file-'+fileBody.request_id.toLowerCase()}}", "idempotency_key:'wf01-file-'+fileBody.request_id.toLowerCase(),...scope}}"),
    )
    for old,new in replacements:
        if source.count(new)==1:continue
        if source.count(old)!=1:raise ValueError('WF01_SOURCE_CONTRACT_CHANGED')
        source=source.replace(old,new,1)
    return source


def attach(workflow,gateway_url='http://qldapm-ai-gateway-1:8090'):
    spec=enable_project6_business(workflow);code=spec['name'][:4]
    if code not in WORKFLOWS:return spec
    if code=='WF01':
        nodes=[n for n in spec['nodes'] if n['id']=='explicit_request' and n['type']=='n8n-nodes-base.code']
        if len(nodes)!=1:raise ValueError('WF01_SOURCE_CONTRACT_CHANGED')
        params=nodes[0]['parameters'];params['jsCode']=enable_project6_files(params['jsCode'])
    nodes=[n for n in spec['nodes'] if not n['id'].startswith('integration-')]
    prefix='Integration '+code+' '
    trigger={'id':'integration-trigger','name':prefix+'Webhook','type':'n8n-nodes-base.webhook','typeVersion':2,'position':[0,1000],
        'webhookId':'qldapm-integration-'+code.lower(),'parameters':{'httpMethod':'POST','path':'qldapm-integration-'+code.lower(),
        'authentication':'headerAuth','responseMode':'responseNode','options':{}},
        'credentials':{'httpHeaderAuth':{'id':'2w9dSdmYbywZDuMB','name':'QLDAPM Webhook Header Auth'}}}
    callback={'id':'integration-callback','name':prefix+'Read Source And Observe','type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[260,1000],
        'parameters':{'method':'POST','url':gateway_url.rstrip('/')+'/internal/automation/integration-event','sendHeaders':True,
        'headerParameters':{'parameters':[{'name':'Host','value':'qldapm-ai-gateway-1:8090'},
            {'name':'X-QLDAPM-N8N-Execution','value':'={{ $execution.id }}'}]},'sendBody':True,'specifyBody':'json','jsonBody':'={{ $json.body }}',
        'options':{'timeout':18000,'redirect':{'redirect':{'followRedirects':False}}}}}
    guard={'id':'integration-business','name':prefix+'Require Business Receipt','type':'n8n-nodes-base.code','typeVersion':2,'position':[520,1000],
        'parameters':{'jsCode':f"const event=$('{trigger['name']}').first().json.body.event; const ack=$json; "
            f"if(event.workflow!=='{code}' || ack.workflow!=='{code}' || ack.status!=='OBSERVED' || ack.project_id!==6 || ack.event_id!==event.event_id || ack.correlation_id!==event.correlation_id || !ack.business_result?.state) throw new Error('BUSINESS_RECEIPT_REQUIRED'); "
            "if(['QA_BLOCKED','BLOCKED_DLQ','FAILED','DENIED'].includes(ack.business_result.state)) throw new Error('BUSINESS_'+ack.business_result.state); return [{json:ack}];"}}
    reply={'id':'integration-reply','name':prefix+'Reply','type':'n8n-nodes-base.respondToWebhook','typeVersion':1.4,'position':[780,1000],
        'parameters':{'respondWith':'json','responseBody':'={{ $json }}','options':{}}}
    branch=[trigger,callback,guard,reply];spec['nodes']=nodes+branch
    links={k:v for k,v in spec['connections'].items() if not k.startswith(prefix)}
    for a,b in zip(branch,branch[1:]):links[a['name']]={'main':[[{'node':b['name'],'type':'main','index':0}]]}
    spec['connections']=links
    return spec
