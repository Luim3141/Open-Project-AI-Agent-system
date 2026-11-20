"""Durable actor/project-scoped reports are generated internally, never arbitrary uploads."""
import tempfile
import unittest
from pathlib import Path

from gateway.store import Store


class OperationalReportTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.store=Store(self.root)

    def test_deduplication_durability_and_scoped_readback(self):
        document={'status':'PARTIAL_UNMATCHED_POINTS','unmatched':3}
        refs=[{'id':12,'lockVersion':2}]
        saved=self.store.save_report(7,5,'knowledge_integrity',document,refs)
        duplicate=self.store.save_report(7,5,'knowledge_integrity',dict(reversed(list(document.items()))),refs)
        self.assertEqual(saved['report_id'],duplicate['report_id'])
        self.assertEqual(Store(self.root).report(7,5,saved['report_id'])['document'],document)
        for actor,project in ((8,5),(7,3)):
            with self.assertRaises(PermissionError):
                self.store.report(actor,project,saved['report_id'])
        changed=self.store.save_report(7,5,'knowledge_integrity',document,[{'id':12,'lockVersion':3}])
        self.assertNotEqual(saved['report_id'],changed['report_id'])

    def test_tampered_report_is_not_returned_as_verified_evidence(self):
        saved=self.store.save_report(7,5,'health',{'status':'ok'},[])
        with self.store.connect() as db:
            db.execute("UPDATE operational_reports SET document='{}' WHERE id=?",(saved['report_id'],))
        with self.assertRaisesRegex(ValueError,'REPORT_HASH_MISMATCH'):
            self.store.report(7,5,saved['report_id'])

    def test_unknown_report_kind_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'FIXED_REPORT_KIND'):
            self.store.save_report(7,5,'arbitrary-client-content',{},[])

    def test_service_revalidates_visibility_and_marks_changed_versions_as_historical(self):
        from gateway.service import Service
        class Native:
            items=[{'id':12,'lockVersion':2}]
            def __init__(self,*args):
                pass
            def identity(self,actor):
                return {'user_id':actor,'role':'PM'}
            def packages(self):
                return self.items
        token=self.store.issue_token(7,'PM','synthetic-native')
        other=self.store.issue_token(8,'PM','synthetic-other')
        service=Service(self.store,{'users':{'7':'PM','8':'PM'},'project_id':5,'gateway_mode':'native',
            'openproject_url':'http://127.0.0.1:8088'},self.root/'workspace',Native)
        saved=self.store.save_report(7,5,'knowledge_integrity',{'status':'VERIFIED'},Native.items)
        command={'action':'get_report','arguments':{'id':saved['report_id']}}
        self.assertTrue(service.execute(token,command)['result']['source_versions_current'])
        Native.items=[{'id':12,'lockVersion':3}]
        self.assertFalse(service.execute(token,command)['result']['source_versions_current'])
        Native.items=[]
        result=service.execute(token,command)['result']
        self.assertTrue(result['data_hidden'])
        self.assertNotIn('document',result)
        with self.assertRaises(PermissionError):
            service.execute(other,command)
        with self.assertRaisesRegex(ValueError,'REPORT_UUID_REQUIRED'):
            service.execute(token,{'action':'get_report','arguments':{'id':[]}})

    def test_pm_report_cannot_be_read_after_owner_role_changes_to_ba(self):
        from gateway.service import Service
        class Native:
            def __init__(self,*args):
                pass
            def identity(self,actor):
                return {'user_id':actor,'role':'BA'}
            def packages(self):
                raise AssertionError('Role change must hide the report before reading references')
        token=self.store.issue_token(7,'PM','synthetic-native')
        saved=self.store.save_report(7,5,'weekly_summary',{'actor_role':'PM','member_breakdown':{'private':'fixture'}},[])
        service=Service(self.store,{'users':{'7':'BA'},'project_id':5,'gateway_mode':'native',
            'openproject_url':'http://127.0.0.1:8088'},self.root/'workspace',Native)
        result=service.execute(token,{'action':'get_report','arguments':{'id':saved['report_id']}})['result']
        self.assertEqual(result['state'],'SOURCE_ROLE_CHANGED')
        self.assertNotIn('document',result)
