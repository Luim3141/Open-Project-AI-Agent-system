"""Control Center must recheck native membership before reading stored actor data."""
import unittest
from unittest.mock import patch

from gateway.native import NativeError
from tests import test_control_center as fixture


class ControlCenterAuthorizationTests(unittest.TestCase):
    setUp = fixture.ControlCenterTests.setUp
    headers = fixture.ControlCenterTests.headers
    seed_task_and_run = fixture.ControlCenterTests.seed_task_and_run
    def test_revoked_membership_denies_cached_actor_data(self):
        self.seed_task_and_run(actor=7)
        self.fixture.state.roles.pop(7)
        response = self.client.get('/api/v1/control-center/state', headers=self.headers(7))
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('INSTRUCTION_FOR_ACTOR_7', response.text)
        self.assertNotIn('role_permissions', response.text)

    def test_changed_native_role_denies_stale_config(self):
        self.fixture.state.roles[7] = 'BE'
        response = self.client.get('/api/v1/control-center/state', headers=self.headers(7))
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('can_mutate_business', response.text)

    def test_native_outage_does_not_invent_pm_authority(self):
        with patch.object(self.service, 'native_actor', side_effect=NativeError(503, 'OPENPROJECT_503')):
            response = self.client.get('/api/v1/control-center/state', headers=self.headers(7))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('can_mutate_business', response.text)
