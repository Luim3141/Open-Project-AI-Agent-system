import os
import sys
import time
import unittest
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gateway.engineering_health import integration_health,openclaw_snapshot,demo_observability,provider_status
from automation.openclaw_health import collect


class IntegrationHealthTest(unittest.TestCase):
    def test_scoped_service_recreation_reuses_health_cache_without_new_probes(self):
        calls=[]
        def transport(url,headers):calls.append(url);return 200
        first=self.service();second=self.service()
        integration_health(first,transport=transport);count=len(calls)
        integration_health(second,transport=transport)
        self.assertGreater(count,0);self.assertEqual(len(calls),count,'each scoped status rebuild discards machine health cache')
    def test_provider_fresh_response_and_headroom_are_separate_from_stale_probe(self):
        from gateway.store import Store
        with tempfile.TemporaryDirectory() as root:
            store=Store(Path(root));policy={'model':'gemini-3.5-flash-lite','project':'fixture','quota':{'rpm':15,'tpm':250000,'rpd':500},'limits':{'rpm':13,'tpm':225000,'rpd':450}}
            service=SimpleNamespace(store=store,config={'engineering':{'provider_limits':{'rpm':10,'tpm':175000}}},gemini=SimpleNamespace(settings=lambda:policy,readiness=lambda _: {'state':'READY','last_successful_check':time.time()-600}))
            store.provider_receipt({'id':'fixture','actor':20,'run_id':None,'project':'fixture','phase':'generateContent','at':time.time(),'http_status':200})
            status=provider_status(service)
            self.assertEqual(status['state'],'AVAILABLE');self.assertEqual(status['project_limits']['rpm'],15)
            self.assertEqual(status['engineering_limits']['rpm'],10)
            store.provider_receipt({'id':'fixture','actor':20,'run_id':None,'project':'fixture','phase':'generateContent','at':time.time(),'http_status':429})
            self.assertEqual(provider_status(service)['state'],'RATE_LIMITED')
    def test_demo_metadata_does_not_claim_business_or_semantic_success(self):
        from gateway.store import Store
        with tempfile.TemporaryDirectory() as root:
            store=Store(Path(root));service=SimpleNamespace(store=store)
            with store.connect() as db:
                db.execute('INSERT INTO native_index_scans VALUES(?,?,?,?)',(20,6,3,json.dumps({'state':'OBSERVED','observed_at':time.time(),'visible':8,'secret':'private'})))
            path=Path(root)/'demo-dr-status.json'
            path.write_text(json.dumps({'state':'LOCAL_RESTORE_VERIFIED','checked_at':time.time(),'key':'private','off_host':'OFF_HOST_COPY_PENDING_OWNER'}))
            result=demo_observability(service)
            self.assertEqual(result['dr']['state'],'LOCAL_RESTORE_VERIFIED')
            self.assertEqual(result['rag']['scans'][0]['visible'],8)
            self.assertNotIn('secret',json.dumps(result));self.assertNotIn('key',result['dr'])
            self.assertEqual(result['n8n']['state'],'NOT_OBSERVED')
    def test_cli_snapshot_is_bounded_fresh_and_does_not_publish_arbitrary_fields(self):
        with tempfile.TemporaryDirectory() as root:
            service=self.service();service.store=SimpleNamespace(root=root)
            path=Path(root)/'openclaw-health.json'
            path.write_text(json.dumps({'checked_at':time.time(),'health':'READY','secret':'never expose'}))
            self.assertNotIn('secret',openclaw_snapshot(service))
            path.write_text(json.dumps({'checked_at':time.time()-151,'health':'READY'}))
            self.assertIsNone(openclaw_snapshot(service))
            path.write_text('x'*8193)
            self.assertIsNone(openclaw_snapshot(service))

    def test_cli_probe_has_no_inference_and_fixed_output(self):
        calls=[]
        def run(args,**kwargs):
            calls.append(args)
            if '--list' in args:return SimpleNamespace(returncode=0,stdout='OpenClawGateway\r\n'.encode('utf-16-le'))
            payload={'ok':True,'raw_secret':'private'} if 'health' in args else {'rpc':{'ok':True},'service':{'runtime':{'status':'running'}}}
            return SimpleNamespace(returncode=0,stdout=json.dumps(payload).encode())
        result=collect(run)
        self.assertEqual(result['health'],'READY');self.assertTrue(result['gateway_rpc_ok'])
        self.assertEqual(result['process_state'],'running');self.assertNotIn('raw_secret',result)
        self.assertEqual(len(calls),3)
        self.assertFalse(any('agent' in c or 'chat' in c for c in calls))
    def test_configured_openclaw_ready_is_separate_from_worker_and_provider(self):
        service=self.service({'integration_health_urls':{'openclaw':'http://host.docker.internal:18789','demo':'http://host.docker.internal:18791'}})
        calls=[]
        def probe(url,headers):
            calls.append(url)
            return (200,{'ready':True,'coreReady':True,'failing':[]}) if url.endswith('/readyz') else 200
        rows={r['key']:r for r in integration_health(service,transport=probe)}
        self.assertEqual(rows['openclaw']['health'],'READY')
        self.assertEqual(rows['demo']['health'],'UP')
        self.assertIn('http://host.docker.internal:18789/readyz',calls)
        self.assertEqual(rows['openclaw']['business_status'],'NOT CHECKED — Gateway availability không chứng minh Dev đang chạy')
        self.assertEqual(rows['openclaw']['process_health'],'HTTP_READY; CLI process details checked separately')

    def service(self, extra=None):
        return SimpleNamespace(config={'openproject_url': 'http://web:8080', **(extra or {})})

    def test_fixed_safe_paths_and_independent_semantics(self):
        calls = []
        def probe(url, headers):
            calls.append((url, headers))
            return 200
        service = self.service({'n8n_lifecycle': {'webhook_url': 'http://n8n:5678/webhook/qldapm-lifecycle'}})
        with patch.dict(os.environ, {}, clear=True):
            rows = integration_health(service, transport=probe)
        self.assertEqual(len(rows), 7)
        rows = {r['key']: r for r in rows}
        self.assertEqual(rows['n8n']['health'], 'UP')
        self.assertEqual(rows['n8n']['business_status'], 'NOT CHECKED — API readiness không chứng minh workflows PASS')
        self.assertEqual(rows['openclaw']['health'], 'UNKNOWN')
        self.assertEqual(rows['demo']['health'], 'UNKNOWN')
        self.assertEqual(rows['gateway']['authentication'], 'NOT CHECKED')
        self.assertTrue(all(r['process_health'] == 'NOT CHECKED' for r in rows.values()))
        self.assertTrue(any(url.endswith('/api/tags') for url, _ in calls))
        self.assertFalse(any('/embed' in url or '/generate' in url or '/webhook/' in url for url, _ in calls))
        self.assertTrue(all(not headers.get('Authorization') for _, headers in calls))
        self.assertTrue(all(row['checked_at'] for row in rows.values() if row['health'] == 'UP'))

    def test_failures_unknown_and_credentials_never_escape(self):
        config = {'integration_health_urls': {'openclaw': 'https://user:secret@example.test/token?q=secret', 'demo': 'http://demo:18791'}}
        def probe(url, headers):
            if 'demo' in url:
                raise TimeoutError('secret=do-not-output')
            return 503
        with patch.dict(os.environ, {}, clear=True):
            rows = integration_health(self.service(config), transport=probe)
        rows = {r['key']: r for r in rows}
        self.assertEqual(rows['openclaw']['health'], 'UNKNOWN')
        self.assertIsNone(rows['openclaw']['url'])
        self.assertEqual(rows['demo']['health'], 'DOWN')
        self.assertEqual(rows['demo']['last_error'], 'TIMEOUT')
        self.assertEqual(rows['gateway']['last_error'], 'HTTP_503')
        self.assertNotIn('secret', str(rows))

    def test_ttl_and_concurrent_bound(self):
        calls = []
        def probe(url, headers):
            calls.append(url)
            time.sleep(.06)
            return 200
        service = self.service()
        with patch.dict(os.environ, {}, clear=True):
            start = time.monotonic()
            first = integration_health(service, transport=probe)
            second = integration_health(service, transport=probe)
        self.assertLess(time.monotonic() - start, .2)
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 4)


if __name__ == '__main__':
    unittest.main()
