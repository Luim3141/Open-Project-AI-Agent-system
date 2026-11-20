import unittest
from unittest.mock import patch

from gateway.native import Native, NativeError


class NativeSummaryTests(unittest.TestCase):
    def test_scope_shape_and_canonical_order(self):
        native = Native('http://staging-web:8080', 'synthetic', 3)
        valid = {'actor': 7, 'project_id': 3, 'count': 2, 'by_status': {'NEW': 2}, 'overdue_ids': [9, 1]}
        with patch.object(native, 'call', return_value=valid) as call:
            self.assertEqual(native.summary(7)['overdue_ids'], [1, 9])
            call.assert_called_once_with('/api/v3/qldapm/daily_summary')
        for changed in ({'actor': 8}, {'project_id': 99}):
            with patch.object(native, 'call', return_value={**valid, **changed}), self.assertRaises(PermissionError):
                native.summary(7)
        for changed in ({'count': True}, {'by_status': {'NEW': 1}}, {'by_status': {'NEW': -2}},
                        {'overdue_ids': [1, 1]}, {'overdue_ids': [True]}, {'overdue_ids': [0]},
                        {'overdue_ids': [1, 2, 3]}):
            with patch.object(native, 'call', return_value={**valid, **changed}), self.assertRaises(NativeError):
                native.summary(7)
