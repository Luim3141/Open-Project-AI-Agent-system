"""Write routing with multi-agent enabled; synthetic Native/provider, zero external calls."""
import unittest
from unittest.mock import patch
from gateway.live_agents import LiveConfig
from tests import test_remaining_integration as fixture


class MainWriteRoutingTests(unittest.TestCase):
    setUp = fixture.RemainingIntegrationTests.setUp
    command = fixture.RemainingIntegrationTests.command
    def test_pm_write_uses_existing_business_worker_with_inferred_parent_scope(self):
        with patch.object(self.service.gemini, 'multi_agent_settings', return_value=LiveConfig(enabled=True)), \
             patch.object(self.service.gemini, 'validate_prompt', return_value={}), \
             patch.object(self.service.gemini, 'structured', side_effect=AssertionError('NO_PROVIDER')):
            for scope in ([], [2]):
                r = self.command('start_ai_run', {'prompt':
                    'Tạo 1 subtask mới tên là test cho task 2, giao cho QA, tự sử dụng các agent thích hợp để làm.',
                    'allow_routine_writes': True, 'write_scope_ids': scope}, key='write-'+str(scope))
                self.assertEqual(r.status_code, 200, r.text)
                with self.store.connect() as db:
                    import json
                    payload = json.loads(db.execute('select payload from ai_queue where id=?', (r.json()['result']['id'],)).fetchone()[0])
                self.assertTrue(payload['allow_routine_writes'])
                self.assertEqual(payload['write_scope_ids'], [2])
                self.assertNotIn('engine', payload)

    def test_write_without_consent_returns_to_proposal_capable_business_worker(self):
        with patch.object(self.service.gemini, 'multi_agent_settings', return_value=LiveConfig(enabled=True)), \
             patch.object(self.service.gemini, 'validate_prompt', return_value={}):
            r = self.command('start_ai_run', {'prompt':'Tạo subtask cho task 2, giao QA'}, key='proposal')
            self.assertEqual(r.status_code, 200, r.text)
            with self.store.connect() as db:
                import json
                p = json.loads(db.execute('select payload from ai_queue where id=?', (r.json()['result']['id'],)).fetchone()[0])
            self.assertFalse(p['allow_routine_writes'])
            self.assertNotIn('engine', p)

    def test_non_pm_create_is_denied_before_provider_even_with_checkbox(self):
        with patch.object(self.service.gemini, 'multi_agent_settings', return_value=LiveConfig(enabled=True)), \
             patch.object(self.service.gemini, 'validate_prompt', side_effect=AssertionError('NO_PROVIDER')):
            r = self.command('start_ai_run', {'prompt':'Tạo subtask cho task 2, giao QA',
                'allow_routine_writes': True}, actor=8, key='denied')
            self.assertEqual(r.status_code, 403, r.text)
            self.assertEqual(r.json()['error'], 'PM_ONLY_BUSINESS_WRITE_REQUIRED')

    def test_explicit_parent_scope_is_native_validated_before_enqueue(self):
        with patch.object(self.service.gemini, 'multi_agent_settings', return_value=LiveConfig(enabled=True)), \
             patch.object(self.service.gemini, 'validate_prompt', side_effect=AssertionError('NO_PROVIDER')):
            r = self.command('start_ai_run', {'prompt':'Tạo subtask cho task 999',
                'allow_routine_writes': True, 'write_scope_ids':[999]}, key='scope')
            self.assertEqual(r.status_code, 403, r.text)
            self.assertEqual(r.json()['error'], 'NATIVE_READ_DENIED')

    def test_client_actor_cannot_impersonate_pm(self):
        response=self.client.post('/api/v1/commands',headers={'Authorization':'Bearer '+self.tokens[8]},
            json={'actor':7,'action':'create_work_package','arguments':{'parent_id':2},'idempotency_key':'forged'})
        self.assertIn(response.status_code,(403,422))
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from proposals').fetchone()[0],0)

if __name__ == '__main__': unittest.main()
