import unittest
from automation.n8n_lifecycle_adapter import attach_lifecycle_adapter


class AdapterTests(unittest.TestCase):
    def test_original_graph_survives_and_callback_uses_allowed_gateway_host(self):
        original={'nodes':[{'name':'Human Trace Trigger'}], 'connections':{'Human Trace Trigger':{'main':[]}},'settings':{}}
        candidate=attach_lifecycle_adapter(original,'http://host.docker.internal:18089',gateway_host='localhost:18089')
        self.assertEqual(len(original['nodes']),1)
        self.assertEqual(candidate['nodes'][:1],original['nodes'])
        self.assertEqual(candidate['connections']['Human Trace Trigger'],original['connections']['Human Trace Trigger'])
        callback=next(n for n in candidate['nodes'] if n['name']=='Retrieve Source Trace And Observe')
        headers=callback['parameters']['headerParameters']['parameters']
        self.assertIn({'name':'Host','value':'localhost:18089'},headers)
        self.assertEqual(callback['parameters']['url'],'http://host.docker.internal:18089/internal/automation/lifecycle-observation')
        self.assertFalse(any(h['name'].lower()=='authorization' for h in headers))
