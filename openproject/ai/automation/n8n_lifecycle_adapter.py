"""Add a metadata-only trigger to WF04; existing human trace contract is preserved."""
import copy
from urllib.parse import urlsplit

RETENTION_SETTINGS = {'saveDataErrorExecution': 'none', 'saveDataSuccessExecution': 'none',
                      'saveManualExecutions': False, 'saveExecutionProgress': False}


def attach_lifecycle_adapter(workflow, gateway_url, *, gateway_host=None):
    spec = copy.deepcopy(workflow)
    nodes = [
        {'id': 'lifecycle-trigger', 'name': 'Lifecycle Event Webhook', 'type': 'n8n-nodes-base.webhook',
         'typeVersion': 2, 'position': [0, 600], 'webhookId': 'qldapm-lifecycle',
         'parameters': {'httpMethod': 'POST', 'path': 'qldapm-lifecycle', 'responseMode': 'responseNode', 'options': {}}},
        {'id': 'lifecycle-observe', 'name': 'Retrieve Source Trace And Observe', 'type': 'n8n-nodes-base.httpRequest',
         'typeVersion': 4.2, 'position': [260, 600], 'parameters': {'method': 'POST',
             'url': gateway_url.rstrip('/')+'/internal/automation/lifecycle-observation',
             'sendHeaders': True, 'headerParameters': {'parameters': [
                 {'name': 'Host', 'value': gateway_host or urlsplit(gateway_url).netloc},
                 {'name': 'X-QLDAPM-N8N-Execution', 'value': '={{ $execution.id }}'}]},
             'sendBody': True, 'specifyBody': 'json', 'jsonBody': '={{ $json.body }}',
             'options': {'timeout': 5000, 'redirect': {'redirect': {'followRedirects': False}}}}},
        {'id': 'lifecycle-ack', 'name': 'Require Business Observation', 'type': 'n8n-nodes-base.code',
         'typeVersion': 2, 'position': [520, 600], 'parameters': {'jsCode':
             "const event=$('Lifecycle Event Webhook').first().json.body.event; const ack=$json; "
             "if(ack.status!=='OBSERVED' || ack.event_id!==event.event_id || ack.trace_event_id!==event.event_id || "
             "ack.run_id!==event.run_id || ack.project_id!==6 || ack.correlation_id!==event.correlation_id) "
             "throw new Error('BUSINESS_OBSERVATION_REQUIRED'); return [{json:ack}];"}},
        {'id': 'lifecycle-reply', 'name': 'Reply Lifecycle ACK', 'type': 'n8n-nodes-base.respondToWebhook',
         'typeVersion': 1.4, 'position': [780, 600], 'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}}}
    ]
    spec.setdefault('nodes', []).extend(nodes)
    connections = spec.setdefault('connections', {})
    for left, right in zip(nodes, nodes[1:]):
        connections[left['name']] = {'main': [[{'node': right['name'], 'type': 'main', 'index': 0}]]}
    spec['settings'] = {**spec.get('settings', {}), **RETENTION_SETTINGS}
    return spec


def canonical_history_workflow(workflow, gateway_url, *, gateway_host=None):
    """WF04 is the durable canonical lifecycle viewer; full traces stay in Gateway Inspector."""
    spec=attach_lifecycle_adapter({'id':workflow['id'],'name':workflow['name'],'nodes':[],'connections':{},'settings':workflow.get('settings',{})},gateway_url,gateway_host=gateway_host)
    trigger=spec['nodes'][0]
    trigger['parameters']['authentication']='headerAuth'
    trigger['credentials']={'httpHeaderAuth':{'id':'2w9dSdmYbywZDuMB','name':'QLDAPM Webhook Header Auth'}}
    spec['settings'].update(saveDataErrorExecution='all',saveDataSuccessExecution='all',saveManualExecutions=False,saveExecutionProgress=False,executionTimeout=30)
    return spec
