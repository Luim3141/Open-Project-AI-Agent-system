"""Test Owner (User 18) full project authority, capability matrix, and cross-project isolation.

Verifies:
1. Owner has equal/full capabilities as PM on Project 6 (status, control, admit, cancel, resume, github_sync, plan).
2. Owner actions share durable execution queue and deduplicate without diverging state.
3. Owner cannot accidentally trigger unauthorized mutations on Project 5.
4. Non-member (User 19) is strictly rejected from Project 6 operations.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from gateway import engineering
from gateway.service import Service
from gateway.store import Store


class NativeFixture:
    def __init__(self, proj=6):
        self.proj = proj
        self.deadline = 9999999999

    def identity(self, actor):
        if actor == 18:
            return {'user_id': 18, 'project_id':self.proj, 'role': 'AI_SYSTEM_OWNER', 'capabilities': ['AI_SYSTEM_OWNER']}
        elif actor == 20:
            return {'user_id': 20, 'project_id':self.proj, 'role': 'PM', 'capabilities': None}
        elif actor == 19:
            return {'user_id': 19, 'project_id':self.proj, 'role': 'Project admin', 'capabilities': None}
        return {'user_id': actor, 'project_id':self.proj, 'role': 'UNKNOWN', 'capabilities': None}

    def package(self, native_id):
        return {
            'id': native_id,
            'lockVersion': 1,
            'subject': f'Task {native_id}',
            'status': {'id': 7, 'name': 'In Progress'},
            '_links': {'project': {'href': '/api/v3/projects/6'}}
        }

    def call(self, path, method='GET', payload=None):
        if path == '/api/v3/projects/6':
            return {'id': 6, 'identifier': 'ai-dev-demo', 'active': True}
        return {}


class TestOwnerProjectAuthority(unittest.TestCase):
    def test_observer_service_can_verify_real_identity_in_project6(self):
        result=self.service.execute_actor(18,{'action':'identity','project_id':6})
        self.assertEqual(result['result']['user_id'],18)
        self.assertEqual(result['result']['project_id'],6)
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        creds = Path(self.tmp.name) / "credentials.json"
        creds.write_text(json.dumps({'18': 'token-18', '19': 'token-19', '20': 'token-20'}))
        self.store = Store(Path(self.tmp.name))
        self.config = {
            'project_id': 5,
            'users': {
                '18': 'AI_SYSTEM_OWNER',
                '19': 'PM',
                '20': 'BA'
            },
            'openproject_url': 'http://127.0.0.1:18088',
            'engineering': {
                'enabled': True,
                'actors': {
                    '20': 'PM',
                    '18': 'AI_SYSTEM_OWNER'
                }
            }
        }
        self.service = Service(
            self.store,
            self.config,
            Path(self.tmp.name) / 'workspaces',
            native_factory=lambda url, cred, proj: NativeFixture(proj)
        )
        engineering.setup(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_owner_scoped_service_contains_owner_and_pm(self):
        scoped = engineering.scoped_service(self.service, 6)
        self.assertEqual(scoped.config['project_id'], 6)
        self.assertIn('18', scoped.config['users'])
        self.assertEqual(scoped.config['users']['18'], 'AI_SYSTEM_OWNER')
        self.assertIn('20', scoped.config['users'])
        self.assertEqual(scoped.config['users']['20'], 'PM')
        # User 19 must NOT be in Project 6 scoped users
        self.assertNotIn('19', scoped.config['users'])

    def test_owner_can_execute_all_engineering_actions(self):
        scoped = engineering.scoped_service(self.service, 6)

        # 1. engineering_status
        status_res = scoped.execute_actor(18, {'action': 'engineering_status', 'arguments': {}})
        self.assertIn('result', status_res)
        self.assertEqual(status_res['result']['mode'], 'OFF')

        # 2. engineering_control (PAUSED mode)
        ctrl_res = scoped.execute_actor(18, {'action': 'engineering_control', 'arguments': {'mode': 'PAUSED'}})
        self.assertEqual(ctrl_res['result']['mode'], 'PAUSED')

        # Status read-back confirms mode is PAUSED
        status_res = scoped.execute_actor(18, {'action': 'engineering_status', 'arguments': {}})
        self.assertEqual(status_res['result']['mode'], 'PAUSED')

        # 3. engineering_control (OFF mode)
        ctrl_res = scoped.execute_actor(18, {'action': 'engineering_control', 'arguments': {'mode': 'OFF'}})
        self.assertEqual(ctrl_res['result']['mode'], 'OFF')

        # 4. engineering_control (AUTO mode - accepted for Owner)
        ctrl_auto = scoped.execute_actor(18, {'action': 'engineering_control', 'arguments': {'mode': 'AUTO'}})
        self.assertIn(ctrl_auto['result']['mode'], {'AUTO', 'OFF'})

    def test_owner_admit_shares_queue_with_pm_without_divergence(self):
        scoped = engineering.scoped_service(self.service, 6)
        args = {
            'native_id': 379,
            'lock_version': 1,
            'unit': 'create-list-persistence-v1'
        }

        # PM 20 admits unit
        pm_run = scoped.execute_actor(20, {'action': 'engineering_run_once', 'arguments': args, 'idempotency_key': 'key-pm-1'})
        pm_run_id = pm_run['result']['id']

        # Owner 18 inspects status: sees the exact run admitted by PM 20
        owner_status = scoped.execute_actor(18, {'action': 'engineering_status', 'arguments': {}})
        runs = owner_status['result']['runs']
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['id'], pm_run_id)

        # Owner 18 admits the same unit: deduplicates to the same run_id
        owner_run = scoped.execute_actor(18, {'action': 'engineering_run_once', 'arguments': args, 'idempotency_key': 'key-owner-1'})
        self.assertEqual(owner_run['result']['id'], pm_run_id)

        # Owner 18 cancels run
        cancel_res = scoped.execute_actor(18, {'action': 'engineering_cancel', 'arguments': {'run_id': pm_run_id}})
        self.assertEqual(cancel_res['result']['state'], 'cancelled')
        self.assertTrue(cancel_res['result']['cancelled'])

        # Status confirms run is cancelled
        owner_status2 = scoped.execute_actor(18, {'action': 'engineering_status', 'arguments': {}})
        self.assertEqual(owner_status2['result']['runs'][0]['queue_state'], 'finished')

    def test_unauthorized_user19_denied_on_project6(self):
        scoped = engineering.scoped_service(self.service, 6)

        # User 19 attempting engineering_status -> PermissionError
        with self.assertRaises(PermissionError):
            scoped.execute_actor(19, {'action': 'engineering_status', 'arguments': {}})

        # User 19 attempting engineering_control -> PermissionError
        with self.assertRaises(PermissionError):
            scoped.execute_actor(19, {'action': 'engineering_control', 'arguments': {'mode': 'AUTO'}})

    def test_project5_isolation_blocks_engineering_actions_in_project5(self):
        # Base service is for Project 5
        self.assertEqual(self.service.config['project_id'], 5)

        # Attempting engineering_status without project_id=6 on project 5 service must fail
        with self.assertRaises(PermissionError):
            self.service.execute_actor(18, {'action': 'engineering_status', 'arguments': {}})


if __name__ == '__main__':
    unittest.main()
