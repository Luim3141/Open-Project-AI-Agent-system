import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
import uuid

from gateway.store import Store
from gateway.execution_events import append
from gateway.n8n_lifecycle_outbox import deliver_pending,observe
from automation.n8n_lifecycle_adapter import canonical_history_workflow


class DemoHistoryTests(unittest.TestCase):
    def test_authenticated_minimal_delivery_keeps_credentials_out_of_envelope(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);scope=SimpleNamespace(run_id=str(uuid.uuid4()),trace_id=str(uuid.uuid4()),actor_id=20,project_id=6)
            token='synthetic-transport-'+uuid.uuid4().hex
            Path(root,'webhook_secret.json').write_text(json.dumps({'webhook_token':token}))
            with store.connect() as db:append(db,scope,'AGENT_STARTED',agent='dev',status='RUNNING')
            captured=[]
            def transport(url,envelope,timeout,headers):
                captured.append((envelope,headers));return observe(store,envelope,'a'*64,execution_id='1')
            result=deliver_pending(store,{'enabled':True,'webhook_url':'http://n8n:5678/webhook/qldapm-lifecycle','signing_key':'a'*64,'authenticated_webhook':True},transport=transport)
            self.assertEqual(result,'ACKED');self.assertEqual(captured[0][1],{'X-QLDAPM-Webhook-Token':token})
            self.assertNotIn(token,json.dumps(captured[0][0]))
            self.assertEqual(deliver_pending(store,{'enabled':True,'webhook_url':'http://n8n:5678/webhook/qldapm-lifecycle','signing_key':'a'*64,'authenticated_webhook':True},transport=transport),'IDLE')

    def test_history_workflow_has_only_canonical_branch_and_bounded_settings(self):
        original={'id':'elfapV5D2PTnLiHW','name':'WF04','nodes':[{'name':'old raw trace'}]}
        spec=canonical_history_workflow(original,'http://gateway:8090')
        self.assertEqual(len(original['nodes']),1)
        self.assertEqual(len(spec['nodes']),4)
        self.assertEqual(spec['nodes'][0]['parameters']['authentication'],'headerAuth')
        self.assertEqual(spec['settings']['saveDataSuccessExecution'],'all')
        self.assertFalse(spec['settings']['saveExecutionProgress'])
        self.assertEqual(spec['settings']['executionTimeout'],30)


if __name__=='__main__':unittest.main()
