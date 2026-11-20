import tempfile
import unittest
from unittest.mock import patch

from tests.test_engineering_auto_mode import make_service
from gateway import engineering


class RegisteredSourcesStatusTests(unittest.TestCase):
    def test_real_status_with_registered_sources_uses_fresh_actor_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            service=make_service(directory)
            service.config['file_sources']={'pm-source':{'project_id':6,'allowed_roles':['PM'],'path':'PRIVATE_HOST_PATH'},
                'ba-source':{'project_id':6,'allowed_roles':['BA']},'p5-source':{'project_id':5,'allowed_roles':['PM']}}
            with patch('gateway.engineering_github_sync.fetch_pull_requests',return_value=[]),patch('gateway.engineering_health.integration_health',return_value=[]):
                owner=engineering.status(service,18)
                pm=engineering.status(service,20)
            self.assertEqual({r['source_key'] for r in owner['knowledge_sources']},{'pm-source','ba-source'})
            self.assertEqual(pm['knowledge_sources'],[{'source_key':'pm-source','label':'pm-source'}])
            self.assertNotIn('PRIVATE_HOST_PATH',str(owner['knowledge_sources']))
            self.assertEqual(len(owner['workflow_status']),16)
