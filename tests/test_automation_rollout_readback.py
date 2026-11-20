"""Mocked read-back invariants only; no live mutation or credentials."""
import copy
import io
import json
import runpy
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import jira_admin_mcp as admin


class RolloutReadbackTests(unittest.TestCase):
    def test_scope_only_and_reject_unapproved_changes(self):
        ids = ('01a12eca-5f11-7ef3-9c33-3898c7b1e9f2', '01a12ee4-1276-76b4-ba01-49bdeda52f9d',
            '01a13075-71e9-7e0f-b65f-006ec2a4b83b', '01a13075-71e9-750f-9913-5e43ba4adaf0')
        old = [{'uuid': uuid, 'name': 'QAG3 fixture', 'state': 'ENABLED',
            'ruleScopeARIs': [admin.SCOPE_ARI], 'actor': {'type': 'unchanged'},
            'components': [{'type': 'retained', 'value': {'id': '10000'}}],
            'trigger': {'value': {'fromStatus': [], 'toStatus': []},
                'conditions': [{'value': 'project = QAG3 AND labels = qag3-test'}]}}
            for uuid in ids]
        current = copy.deepcopy(old)
        for rule in current: rule['trigger']['conditions'][0]['value'] = 'project = QAG3'
        current[0]['trigger']['value']['toStatus'] = [{'type': 'NAME', 'value': 'Done'}]
        script = Path(__file__).resolve().parents[1] / 'tools/verify_automation_rollout.py'

        def run(before, after):
            def request(method, path, **kwargs):
                self.assertEqual(method, 'GET')
                uuid = path.split('/')[-1]
                self.assertIn(uuid, ids)
                return {'rule': next(rule for rule in after if rule['uuid'] == uuid)}
            with patch.object(admin, 'preflight'), patch.object(admin, 'request', side_effect=request), \
                 patch.object(Path, 'read_text', return_value=json.dumps({'rules': before})), redirect_stdout(io.StringIO()):
                runpy.run_path(str(script), run_name='__main__')
        run(old, current)
        for change in ('actor', 'scope', 'component', 'disabled', 'still-test', 'event-filter'):
            bad = copy.deepcopy(current)
            if change == 'actor': bad[0]['actor'] = {'type': 'different'}
            elif change == 'scope': bad[0]['ruleScopeARIs'] = ['foreign']
            elif change == 'component': bad[0]['components'][0]['value']['id'] = 'different'
            elif change == 'disabled': bad[0]['state'] = 'DISABLED'
            elif change == 'still-test': bad[0]['trigger'] = old[0]['trigger']
            else: bad[0]['trigger']['value']['toStatus'] = [{'type': 'NAME', 'value': 'REVIEW'}]
            with self.subTest(change=change), self.assertRaises(AssertionError): run(old, bad)
        duplicate = copy.deepcopy(old)
        duplicate[-1] = duplicate[0]
        with self.assertRaises(AssertionError): run(duplicate, current)


if __name__ == '__main__': unittest.main()
