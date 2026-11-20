import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from starlette.applications import Starlette
from starlette.testclient import TestClient
from gateway.app import Security
from gateway.store import Store
from gateway import integration_events as events
from gateway.n8n_lifecycle_outbox import sign_envelope


class IntegrationRouteTests(unittest.TestCase):
    def test_signed_persisted_event_routes_and_rejects_browser_or_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory));key='a'*64
            config={'hosts':['testserver'],'n8n_integration':{'enabled':True,'signing_key':key}}
            service=SimpleNamespace(store=store,config=config)
            event_id=events.enqueue(store,'GITHUB_PR_CHANGED','github:fixture:pr:10','b'*64,
                payload={'pr_number':10,'head_sha':'c'*40,'work_package_id':391})
            with store.connect() as db:
                event=json.loads(db.execute('SELECT document FROM integration_event_outbox WHERE id=?',(event_id,)).fetchone()[0])
            envelope=sign_envelope(event,key)
            with TestClient(Security(Starlette(),store.root,store,config,service)) as client, patch(
                    'gateway.integration_events._business',return_value={'state':'DELIVERY_OBSERVED'}) as effect:
                headers={'X-QLDAPM-N8n-Execution':'123'}
                response=client.post(events.PATH,json=envelope,headers=headers)
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(response.json()['event_id'],event_id)
                for extra in [{'Origin':'http://localhost:8090'},{'Authorization':'Bearer private'}]:
                    self.assertEqual(client.post(events.PATH,json=envelope,headers={**headers,**extra}).status_code,403)
                self.assertEqual(client.post(events.PATH+'?actor=18',json=envelope,headers=headers).status_code,403)
                envelope['signature']='0'*64
                self.assertEqual(client.post(events.PATH,json=envelope,headers=headers).status_code,403)
                effect.assert_called_once()
