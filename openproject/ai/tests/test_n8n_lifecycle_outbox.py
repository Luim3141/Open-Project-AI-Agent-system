import json
import tempfile
import time
import unittest
import uuid
from types import SimpleNamespace

from gateway.store import Store
from gateway.execution_events import append


class LifecycleOutboxTests(unittest.TestCase):
    def test_http_ack_has_total_deadline_even_when_server_keeps_sending(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        from gateway.n8n_lifecycle_outbox import http_transport
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200); self.end_headers()
                try:
                    for char in b'{"status":"OBSERVED","padding":"' + b'x'*100 + b'"}':
                        self.wfile.write(bytes([char])); self.wfile.flush(); time.sleep(.025)
                except OSError: pass  # Client deadline intentionally closes the fixture socket.
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, 'ACK_DEADLINE'):
            http_transport('http://127.0.0.1:'+str(server.server_port), {}, .2)
        self.assertLess(time.monotonic()-started, 1)

    def test_http_ack_deadline_also_covers_slow_headers(self):
        import socketserver
        import threading
        from gateway.n8n_lifecycle_outbox import http_transport
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.recv(8192)
                try:
                    for char in b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}':
                        self.request.sendall(bytes([char])); time.sleep(.025)
                except OSError: pass
        server = socketserver.ThreadingTCPServer(('127.0.0.1', 0), Handler)
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, 'ACK_DEADLINE'):
            http_transport('http://127.0.0.1:'+str(server.server_address[1]), {}, .2)
        self.assertLess(time.monotonic()-started, 1)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.scope = SimpleNamespace(run_id=str(uuid.uuid4()), trace_id=str(uuid.uuid4()), actor_id=20, project_id=6)

    def event(self, key='started'):
        with self.store.connect() as db:
            append(db, self.scope, 'AGENT_STARTED', agent='dev', key=key)

    def test_lifecycle_event_and_outbox_share_transaction_and_stable_id(self):
        self.event()
        self.event()
        with self.store.connect() as db:
            rows = db.execute('SELECT * FROM n8n_lifecycle_outbox').fetchall()
            self.assertEqual(len(rows), 1)
            event = json.loads(rows[0]['document'])
            self.assertEqual(event['correlation_id'], self.scope.trace_id)
            self.assertEqual(event['project_id'], 6)
            self.assertNotIn('actor_id', event)
        with self.assertRaises(RuntimeError):
            with self.store.connect() as db:
                append(db, self.scope, 'AGENT_FAILED', agent='dev', key='rolled-back')
                raise RuntimeError('rollback')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM n8n_lifecycle_outbox').fetchone()[0], 1)

    def test_other_project_is_never_enqueued(self):
        from gateway.n8n_lifecycle_outbox import ensure_schema
        self.scope.project_id = 5
        self.event()
        with self.store.connect() as db:
            ensure_schema(db)
            self.assertEqual(db.execute('SELECT count(*) FROM n8n_lifecycle_outbox').fetchone()[0], 0)

    def test_unrestricted_payload_status_and_agent_are_rejected_before_persistence(self):
        from pydantic import ValidationError
        cases=[{'status':'synthetic-secret'}, {'agent':'synthetic-secret'},
               {'payload':{'nested':'synthetic-secret'}}, {'headers':{'Authorization':'synthetic-secret'}}]
        for values in cases:
            with self.subTest(values=values),self.assertRaises(ValidationError),self.store.connect() as db:
                append(db,self.scope,'AGENT_STARTED',key='denied',**values)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM execution_events').fetchone()[0],0)

    def test_lifecycle_storage_is_bounded_projection_of_identifiers_enums_and_numbers(self):
        self.event()
        with self.store.connect() as db:
            event=json.loads(db.execute('SELECT document FROM n8n_lifecycle_outbox').fetchone()[0])
        self.assertEqual(set(event),{'schema_version','event_id','event_type','run_id','project_id',
            'work_package_id','unit_id','timestamp','correlation_id','status','agent_id'})
        self.assertLess(len(json.dumps(event)),1024)
        self.assertEqual(event['agent_id'],'dev')
        for key in ['event_id','run_id','correlation_id']:self.assertEqual(str(uuid.UUID(event[key])),event[key])

    def test_retry_business_ack_idempotent_observation_and_dlq(self):
        from gateway.n8n_lifecycle_outbox import deliver_pending, observe, sign_envelope
        self.event()
        key = 'a' * 64
        config = {'enabled': True, 'webhook_url': 'http://n8n:5678/webhook/qldapm-lifecycle', 'signing_key': key}
        envelopes = []
        def transport(url, envelope, timeout):
            envelopes.append(envelope)
            return {'status': 'success'}  # Engine green is not a business ACK.
        self.assertEqual(deliver_pending(self.store, config, transport=transport, now=100), 'RETRY')
        self.assertEqual(deliver_pending(self.store, config, transport=transport, now=101), 'IDLE')
        with self.store.connect() as db:
            db.execute('UPDATE n8n_lifecycle_outbox SET next_at=0')
        def success(url, envelope, timeout):
            ack = observe(self.store, envelope, key)
            self.assertEqual(observe(self.store, envelope, key), ack)
            return ack
        self.assertEqual(deliver_pending(self.store, config, transport=success), 'ACKED')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM n8n_lifecycle_observations').fetchone()[0], 1)
        bad = sign_envelope({**envelopes[0]['event'], 'project_id': 5}, key)
        with self.assertRaises(PermissionError): observe(self.store, bad, key)
        bad = sign_envelope({**envelopes[0]['event'], 'correlation_id': str(uuid.uuid4())}, key)
        with self.assertRaises(PermissionError): observe(self.store, bad, key)
        self.event('dlq')
        for attempt in range(5):
            with self.store.connect() as db: db.execute("UPDATE n8n_lifecycle_outbox SET next_at=0 WHERE state!='ACKED'")
            result = deliver_pending(self.store, config, transport=transport)
        self.assertEqual(result, 'DEAD')

    def test_metadata_audit_keeps_only_execution_id_and_rejects_secret_header_value(self):
        from gateway.n8n_lifecycle_outbox import observe, sign_envelope
        self.event()
        with self.store.connect() as db:
            event = json.loads(db.execute('SELECT document FROM n8n_lifecycle_outbox').fetchone()[0])
        envelope = sign_envelope(event, 'a' * 64)
        observe(self.store, envelope, 'a' * 64, '123')
        with self.assertRaises(PermissionError):
            observe(self.store, envelope, 'a' * 64, 'Bearer synthetic-secret')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT execution_id FROM n8n_lifecycle_execution_metadata').fetchone()[0], '123')

    def test_restart_after_consumer_ack_recovers_expired_lease_without_duplicate_observation(self):
        from gateway.n8n_lifecycle_outbox import deliver_pending, observe
        self.event()
        key = 'a' * 64
        config = {'enabled': True, 'webhook_url': 'http://n8n:5678/webhook/qldapm-lifecycle', 'signing_key': key}
        def crash(url, envelope, timeout):
            observe(self.store, envelope, key)
            raise SystemExit('consumer committed before publisher restart')
        with self.assertRaises(SystemExit): deliver_pending(self.store, config, transport=crash)
        reopened = Store(self.temp.name)
        self.assertEqual(deliver_pending(reopened, config, now=time.time()+31,
            transport=lambda u, e, t: observe(reopened, e, key)), 'ACKED')
        with reopened.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM n8n_lifecycle_observations').fetchone()[0], 1)

    def test_http_observation_requires_source_signature_scope_and_no_bearer_header(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        from gateway.n8n_lifecycle_outbox import PATH, sign_envelope
        from tests.test_engineering_auto_mode import make_service
        from gateway.service import Service
        from pathlib import Path
        service = make_service(self.temp.name)
        service.config['n8n_lifecycle'] = {'enabled': True, 'signing_key': 'a' * 64}
        service.config['hosts'] = ['testserver']
        service = Service(self.store, service.config, Path(self.temp.name)/'workspaces')
        self.event()
        with self.store.connect() as db:
            event = json.loads(db.execute('SELECT document FROM n8n_lifecycle_outbox').fetchone()[0])
        client = TestClient(create_app(self.temp.name, service=service))
        self.addCleanup(client.close)
        signed = sign_envelope(event, 'a' * 64)
        self.assertEqual(client.post(PATH, json=signed).status_code, 200)
        self.assertEqual(client.post(PATH, json=signed, headers={'Authorization': 'Bearer fixture'}).status_code, 403)
        self.assertEqual(client.post(PATH, json=sign_envelope(event, 'b' * 64)).status_code, 403)
        self.assertEqual(client.post(PATH+'?project_id=5', json=signed).status_code, 403)


if __name__ == '__main__': unittest.main()

