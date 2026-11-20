"""Local sink contract; no network, real recipients or Main runtime."""
import concurrent.futures
import tempfile
import unittest
from pathlib import Path

from gateway.notification_delivery import deliver_local
from gateway.store import Store


class LocalDeliveryTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.root=Path(folder.name);self.store=Store(self.root/'state');self.sink=self.root/'sink'
        self.report=self.store.save_report(18,5,'health',{'private_business_text':'Must never be sent'},[])

    def test_exact_metadata_only_delivery_is_durable_idempotent_and_concurrent(self):
        def send(_):return deliver_local(Store(self.root/'state'),self.sink,18,5,self.report['report_id'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(send,range(8)))
        self.assertEqual(len({r['receipt_id'] for r in results}),1)
        files=list(self.sink.iterdir());self.assertEqual(len(files),1)
        self.assertNotIn('Must never be sent',files[0].read_text())
        self.assertEqual(results[0]['state'],'DELIVERED_LOCAL_METADATA_ONLY')
        self.assertEqual(results[0]['external_delivery'],'BLOCKED_CONFIGURATION')
        self.assertEqual(send(None),results[0])

    def test_foreign_actor_project_tamper_or_corrupt_sink_never_overwrite(self):
        for actor,project in [(19,5),(18,6)]:
            with self.assertRaises(PermissionError):deliver_local(self.store,self.sink,actor,project,self.report['report_id'])
        self.assertFalse(self.sink.exists())
        deliver_local(self.store,self.sink,18,5,self.report['report_id'])
        receipt=next(self.sink.iterdir());receipt.write_text('preserve corrupted receipt')
        with self.assertRaisesRegex(ValueError,'LOCAL_DELIVERY_RECEIPT_MISMATCH'):
            deliver_local(self.store,self.sink,18,5,self.report['report_id'])
        self.assertEqual(receipt.read_text(),'preserve corrupted receipt')
        with self.store.connect() as db:db.execute("update operational_reports set document='{}'")
        with self.assertRaisesRegex(ValueError,'REPORT_HASH_MISMATCH'):
            deliver_local(self.store,self.sink,18,5,self.report['report_id'])

    def test_new_report_enqueues_once_and_delivery_survives_process_restart(self):
        from gateway.notification_delivery import process_pending
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from local_deliveries').fetchone()[0],1)
        self.store.save_report(18,5,'health',{'private_business_text':'Must never be sent'},[])
        self.assertEqual(process_pending(Store(self.root/'state'))['state'],'delivered')
        files=list((self.root/'state/local-notifications').glob('*.json'))
        self.assertEqual(len(files),1);self.assertNotIn('Must never be sent',files[0].read_text())
        self.assertIsNone(process_pending(Store(self.root/'state')))

    def test_retry_dlq_and_lost_completion_do_not_overwrite_or_duplicate_delivery(self):
        from gateway.notification_delivery import process_pending
        from unittest.mock import patch
        with patch('gateway.notification_delivery.publish_metadata',side_effect=OSError('private disk error')):
            for i in range(6):result=process_pending(self.store,now=1000+i*1000)
        self.assertEqual(result['state'],'dlq');self.assertNotIn('private',str(result))
        self.assertIsNone(process_pending(Store(self.root/'state'),now=10000))
        new=self.store.save_report(18,5,'health',{'sequence':2},[])
        from gateway.notification_delivery import publish_metadata
        def lost(*args):
            publish_metadata(*args);raise OSError('lost completion after atomic file')
        with patch('gateway.notification_delivery.publish_metadata',side_effect=lost):
            self.assertEqual(process_pending(self.store,now=10000)['state'],'pending')
        self.assertEqual(process_pending(Store(self.root/'state'),now=11000)['state'],'delivered')
        self.assertEqual(len(list((self.root/'state/local-notifications').glob('*.json'))),1)

    def test_queue_or_authoritative_report_tamper_is_held_without_external_io(self):
        from gateway.notification_delivery import process_pending
        with self.store.connect() as db:db.execute("update operational_reports set document='{}'")
        result=process_pending(self.store,now=1000)
        self.assertEqual(result['state'],'pending');self.assertFalse((self.root/'state/local-notifications').exists())
        self.assertEqual(result['error'],'ValueError')

    def test_scheduled_daily_and_monitor_receipts_enqueue_and_are_actor_scoped(self):
        import time,uuid
        from types import SimpleNamespace
        from unittest.mock import patch
        from gateway.notification_delivery import process_pending,status
        from gateway.monitoring import snapshot
        command={'version':1,'kind':'daily_brief','request_key':'daily:2026-10-25','nonce':uuid.uuid4().hex,'issued_at':int(time.time())}
        receipt,_=self.store.begin_automation(command,project=5,targets=1)
        report={'actor':19,'project':5,'day':'2026-10-25','run_id':receipt['run_id'],'state':'READY','private_data':'Do not deliver'}
        self.store.finish_daily_brief(receipt['run_id'],[report])
        service=SimpleNamespace(store=self.store,config={'project_id':5,'openproject_url':'http://web:8080'})
        with patch('gateway.monitoring.collect',return_value={'project_id':5,'state':'HEALTHY','private_data':'Do not deliver'}):
            first=snapshot(service);second=snapshot(service)
        self.assertTrue(second['cached']);self.assertEqual(first['correlation_id'],second['correlation_id'])
        self.assertEqual(status(self.store,19,'BA',5)['counts'],{'pending':1})
        self.assertEqual(status(self.store,20,'QA',5)['counts'],{})
        self.assertEqual(status(self.store,18,'AI_SYSTEM_OWNER',5)['counts'],{'pending':3})
        self.assertNotIn('source_id',str(status(self.store,20,'QA',5)))
        while process_pending(self.store):pass
        files=list((self.root/'state/local-notifications').glob('*.json'));self.assertEqual(len(files),3)
        self.assertTrue(all('Do not deliver' not in p.read_text() for p in files))

    def test_existing_background_worker_drains_queue_without_native_calls(self):
        import time
        from unittest.mock import patch
        from gateway.service import Service
        service=Service(self.store,{'project_id':5},self.root/'workspace')
        with patch.object(service,'process_knowledge_sync'):
            service.start_knowledge_worker()
            try:
                deadline=time.monotonic()+3
                while time.monotonic()<deadline:
                    with self.store.connect() as db:state=db.execute('select state from local_deliveries').fetchone()[0]
                    if state=='delivered':break
                    time.sleep(.02)
                self.assertEqual(state,'delivered')
            finally:service.stop_knowledge_worker()


if __name__=='__main__':unittest.main()
