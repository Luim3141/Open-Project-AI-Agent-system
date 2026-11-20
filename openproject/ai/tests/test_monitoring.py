import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from gateway.app import create_app
from gateway.automation import HEADER
from gateway.monitoring import MONITOR_PATH,collect,snapshot
from gateway.store import Store,canonical,digest


class MonitorTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.service=SimpleNamespace(store=Store(self.root),config={'project_id':5,'openproject_url':'http://web:8080'})
        self.calls=[]
        def handler(request):
            self.calls.append((request.method,str(request.url)))
            data={'result':{'status':'green','points_count':17,'config':{'params':{'vectors':{'size':1024}}}}} if 'qdrant' in request.url.host else {'models':[{'name':'bge-m3:latest'}]}
            return httpx.Response(200,json=data)
        self.http=httpx.Client(transport=httpx.MockTransport(handler));self.addCleanup(self.http.close)
        self.vector=SimpleNamespace(qdrant_url='http://qldapm-qdrant:6333',ollama_url='http://host.docker.internal:11434',
            collection_name='qldapm_knowledge_dense',embed_texts=lambda _: [[.1]*1024],close=lambda:None)

    def collect(self,provider='UNKNOWN'):
        health=[{'key':key,'health':'READY' if key=='openclaw' else 'UP','checked_at':123,'latency_ms':2,'last_error':None} for key in ['gateway','openclaw','n8n','demo']]
        with patch('gateway.monitoring.httpx.Client',return_value=self.http),patch('gateway.monitoring.VectorClient',return_value=self.vector), \
                patch('gateway.monitoring.resources',return_value={'state':'OK','memory_bytes':100}), \
                patch('gateway.engineering_health.integration_health',return_value=health), \
                patch('gateway.engineering_health.provider_status',return_value={'state':provider}):
            return collect(self.service)

    def test_fixed_probes_and_metrics_come_from_responses_not_constants(self):
        report=self.collect()
        self.assertEqual(report['state'],'HEALTHY')
        self.assertEqual(report['checks']['qdrant']['points'],17)
        self.assertNotIn('embedding',report['checks'])
        self.assertEqual(report['checks']['openclaw']['health'],'READY')
        self.assertEqual(report['checks']['resources']['memory_bytes'],100)
        self.assertEqual({method for method,url in self.calls},{'GET'})
        self.assertEqual({httpx.URL(url).host for method,url in self.calls},{'web','qldapm-qdrant','host.docker.internal'})
        self.assertFalse(report['native_write_allowed'])
        self.assertEqual(report['model_calls'],0)

    def test_health_never_calls_embedding_inference(self):
        self.vector.embed_texts=lambda _: self.fail('Health must not invoke a model')
        report=self.collect()
        self.assertEqual(report['state'],'HEALTHY')
        self.assertNotIn('embedding',report['checks'])
        self.assertNotIn('NaN',json.dumps(report))

    def test_rate_limit_is_distinct_from_service_ready_and_degrades_health(self):
        report=self.collect(provider='RATE_LIMITED')
        self.assertEqual(report['state'],'DEGRADED')
        self.assertEqual(report['checks']['provider']['health'],'PROVIDER_RATE_LIMITED')
        self.assertEqual(report['checks']['openclaw']['health'],'READY')

    def test_durable_integration_failure_is_not_flattened_to_up(self):
        from gateway.integration_events import enqueue
        identifier=enqueue(self.service.store,'GITHUB_PR_CHANGED','github:fixture:pr:1','a'*64,payload={'pr_number':1})
        with self.service.store.connect() as db:db.execute("UPDATE integration_event_outbox SET state='DEAD' WHERE id=?",(identifier,))
        report=self.collect()
        self.assertEqual(report['state'],'DEGRADED')
        self.assertEqual(report['checks']['business_integration']['health'],'BUSINESS_INTEGRATION_FAILED')
        self.assertEqual(report['checks']['business_integration']['workflows'],['WF04'])

    def test_http_failure_and_oversized_body_are_degraded_without_raw_errors(self):
        self.http=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(503,text='password=synthetic-secret')))
        self.addCleanup(self.http.close)
        report=self.collect()
        self.assertEqual(report['state'],'DEGRADED')
        self.assertEqual(report['checks']['qdrant']['state'],'ERROR')
        self.assertNotIn('synthetic-secret',json.dumps(report))

    def test_json_response_bound_prevents_unbounded_health_payloads(self):
        from gateway.monitoring import json_get
        with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,content=b'x'*131073))) as client:
            with self.assertRaisesRegex(ValueError,'BOUND_EXCEEDED'):json_get(client,'http://qldapm-qdrant:6333/healthz')

    def test_wrong_target_rejected_before_network_and_before_cached_receipt(self):
        self.service.config['project_id']=3
        with self.assertRaises(PermissionError):self.collect()
        with self.assertRaises(PermissionError):snapshot(self.service)
        self.assertEqual(self.calls,[])

    def test_persistent_bucket_receipt_replays_once_and_tamper_is_denied(self):
        report={'observed_at':123,'state':'DEGRADED','checks':{}}
        with patch('gateway.monitoring.collect',return_value=report) as probe:
            first=snapshot(self.service)
            self.service.store=Store(self.root)
            second=snapshot(self.service)
            probe.assert_called_once()
        self.assertFalse(first['cached']);self.assertTrue(second['cached'])
        self.assertEqual(first['correlation_id'],second['correlation_id'])
        self.assertEqual(second['sha256'],digest(canonical(report)))
        with self.service.store.connect() as db:
            db.execute("UPDATE audit SET outcome='{}' WHERE action='health_monitor'")
        with self.assertRaisesRegex(ValueError,'HASH_CHANGED'):snapshot(self.service)

    def test_http_boundary_requires_machine_key_and_forbids_query_body_and_bearer(self):
        from tests.test_automation_auth import AutomationAuthTests
        fixture=AutomationAuthTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.service.config.update(project_id=5,openproject_url='http://web:8080')
        with patch('gateway.monitoring.collect',return_value={'state':'HEALTHY'}):
            response=fixture.client.get(MONITOR_PATH,headers=fixture.headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['result']['state'],'HEALTHY')
        self.assertEqual(fixture.client.get(MONITOR_PATH).status_code,401)
        self.assertEqual(fixture.client.get(MONITOR_PATH+'?target=external',headers=fixture.headers).status_code,403)
        self.assertEqual(fixture.client.request('GET',MONITOR_PATH,headers=fixture.headers,content='{}').status_code,403)
        self.assertEqual(fixture.client.get(MONITOR_PATH,headers={**fixture.headers,'Authorization':'Bearer arbitrary'}).status_code,403)
        from gateway.knowledge_lock import lease
        with lease(fixture.root/'main-monitor.lock'):
            self.assertEqual(fixture.client.get(MONITOR_PATH,headers=fixture.headers).status_code,503)


if __name__=='__main__':unittest.main()
