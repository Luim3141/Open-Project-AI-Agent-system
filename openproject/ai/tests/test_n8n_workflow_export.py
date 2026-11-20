import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from n8n_status_workflow import SOURCE, DAILY_SOURCE
from n8n_workflow_export import CURRENT_SOURCES, export, portable, verify_bundle


class WorkflowExportTests(unittest.TestCase):
    def test_live_fields_are_versioned_inactive_and_no_owner_edits_are_dropped(self):
        expected = json.loads(DAILY_SOURCE.read_text())
        actual = {**copy.deepcopy(expected), 'active': True, 'versionId': '11111111-1111-4111-8111-111111111111',
                  'shared': [{'user': {'password': 'must-never-export'}}]}
        self.assertEqual(portable(actual, expected), expected)
        for edit in ({'settings': {**expected['settings'], 'errorWorkflow': 'owner-edit'}},
                     {'nodes': [{**expected['nodes'][0], 'secret': 'must-never-export'}, *expected['nodes'][1:]]}):
            with self.assertRaises(PermissionError):
                portable({**actual, **edit}, expected)

    def test_two_workflow_export_roundtrip_tamper_path_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'export'
            class Client:
                def __init__(self, base): pass
                def workflow(self):
                    source = next(source for source in CURRENT_SOURCES if json.loads(source.read_text())['id'] == self.workflow_id)
                    return json.loads(source.read_text())
            with patch('n8n_workflow_export.LocalWorkflow', Client), patch('n8n_workflow_export.provision'):
                self.assertTrue(export(Path(temp), destination)['passed'])
                self.assertEqual(len(verify_bundle(destination)), 3)
                with self.assertRaises(FileExistsError):
                    export(Path(temp), destination)
            manifest = json.loads((destination / 'manifest.json').read_text())
            manifest['workflows'][0]['file'] = '../credentials.json'
            (destination / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                verify_bundle(destination)
