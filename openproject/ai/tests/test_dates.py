import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.catalog import BUSINESS_PARAMETERS
from gateway.gemini import ProviderError
from gateway.presentation import action_requested, execution_report, requested_ids
from gateway.service import Service
from gateway.store import Store


class DateTests(unittest.TestCase):
    def test_native_calendar_normalization_is_preflighted_and_explained(self):
        class Native:
            def package(self, identifier):
                return {'id': identifier, 'lockVersion': 1, 'startDate': '2026-10-12', 'dueDate': '2026-12-31'}
            def call(self, path, method='GET', payload=None):
                if path.endswith('/form'):
                    return {'_embedded': {'payload': {'startDate': '2026-10-12', 'dueDate': '2026-12-31'}, 'validationErrors': {}}}
                assert payload['startDate'] == '2026-10-12', 'Use native form calendar result before write'
                return self.package(442)
        with tempfile.TemporaryDirectory() as folder:
            service = Service(Store(folder), {'gateway_mode': 'native'}, Path(folder) / 'workspaces')
            args = {'id':442,'lock_version':1,'changes':{'start_date':'2026-10-10','due_date':'2026-12-31'}}
            result=service.perform({'user_id':7,'role':'PM'},Native(),'update_work_package',args)
            self.assertEqual(result['date_adjustments']['start_date'], {'requested':'2026-10-10','actual':'2026-10-12'})
            report=execution_report([{'action':'update_work_package','arguments':args,
                'result':{'result':{**result,'native_confirmed':True}}}])
            self.assertIn('2026-10-12',report['text'])
            self.assertIn('lịch làm việc',report['text'])
            dates, adjustments = service.date_payload(Native(), {'id':442,'lockVersion':1,'startDate':None,'dueDate':None}, {'due_date':'2026-12-31'})
            self.assertEqual(dates, {'dueDate':'2026-12-31'})
            self.assertTrue(adjustments['start_date']['automatic'])

    def test_explicit_date_and_assignment_commands_are_recognized(self):
        for prompt in (
            'set ngày bắt đầu và ngày kết thúc cho task 442 là từ ngày 10/10/2026 đến ngày 31/12/2026',
            'thêm deadline cho subtask 442 là vào ngày 31/12/2026',
            'Subtask 442: set ngày bắt đầu 10/10/2026 và deadline 31/12/2026',
            'chuyển task 442 từ BE sang cho FE',
        ):
            with self.subTest(prompt=prompt):
                self.assertTrue(action_requested(prompt, 'update_work_package'))
                self.assertEqual(requested_ids(prompt), [442])
        self.assertFalse(action_requested('Thêm comment task 442: set ngày cho task 51', 'update_work_package'))
        self.assertFalse(action_requested('Đọc công việc 58: tạo task khác', 'create_work_package'))
        self.assertTrue(action_requested('thêm ngày start là 10/10/2026 và hạn cuối là 31/12/2026 cho subtasks 112', 'update_work_package'))
        self.assertEqual(requested_ids('thêm ngày start là 10/10/2026 và hạn cuối là 31/12/2026 cho subtasks 112'), [112])
        self.assertEqual(requested_ids('set deadline cho subtasks 112, 113 và 114 ngày 31/12/2026'), [112,113,114])
        self.assertEqual(requested_ids('set ngày cho ID 112'), [112])

    def test_start_date_is_in_model_contract_and_atomic_native_payload(self):
        self.assertIn('start_date', BUSINESS_PARAMETERS['update_work_package']['properties']['changes']['properties'])
        class Native:
            def __init__(self):
                self.item = {'id': 442, 'lockVersion': 0, 'startDate': None, 'dueDate': None}
                self.writes = []
            def package(self, identifier): return dict(self.item)
            def call(self, path, method='GET', payload=None):
                if path.endswith('/form'):
                    return {'_embedded': {'validationErrors': {}, 'payload': {**self.item, **payload}}}
                self.writes.append(payload)
                self.item.update(payload)
                self.item['lockVersion'] += 1
                return dict(self.item)
        with tempfile.TemporaryDirectory() as folder:
            service = Service(Store(folder), {'gateway_mode': 'native'}, Path(folder) / 'workspaces')
            native = Native()
            result = service.perform({'user_id': 7, 'role': 'PM'}, native, 'update_work_package', {
                'id': 442, 'lock_version': 0, 'changes': {'start_date': '2026-10-10', 'due_date': '2026-12-31'}})
            self.assertEqual(len(native.writes), 1)
            self.assertEqual(result['startDate'], '2026-10-10')
            self.assertEqual(result['dueDate'], '2026-12-31')
            for changes in ({'start_date': '2026-02-31'}, {'start_date': '2027-01-01'},
                            {'due_date': '2026-10-01'}, {'start_date': 20261015}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    service.perform({'user_id': 7, 'role': 'PM'}, native, 'update_work_package', {
                        'id': 442, 'lock_version': 1, 'changes': changes})
            self.assertEqual(len(native.writes), 1, 'Invalid ranges must not PATCH either date')
            cleared = service.perform({'user_id': 7, 'role': 'PM'}, native, 'update_work_package', {
                'id': 442, 'lock_version': 1, 'changes': {'start_date': None, 'due_date': None}})
            self.assertIsNone(cleared['startDate'])
            self.assertIsNone(cleared['dueDate'])

    def test_progress_never_claims_user_did_not_supply_data(self):
        report = execution_report([{'action': 'get_work_package', 'arguments': {'id': 51}, 'result': {'result': {'id': 51}}}], in_progress=True)
        self.assertNotIn('Chưa có dữ liệu', report['text'])
        self.assertIn('xử lý', report['text'])

    def test_provider_failure_does_not_replace_run_state_with_http_status(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            service = Service(store, {'gateway_mode': 'native'}, Path(folder) / 'workspaces')
            with patch.object(service.gemini, 'settings', return_value={}), patch('gateway.service.run_isolated', side_effect=ProviderError('GEMINI_UNAVAILABLE')):
                run = service.perform({'user_id': 7, 'role': 'PM'}, None, 'start_ai_run', {'prompt': 'set ngày cho task 442'})
                deadline = time.monotonic() + 2
                while store.run(7, run['id'])['state'] == 'running' or service.gemini.lock.locked():
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)
            result = store.run(7, run['id'])['result']
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['provider_http_status'], 503)


if __name__ == '__main__':
    unittest.main()
