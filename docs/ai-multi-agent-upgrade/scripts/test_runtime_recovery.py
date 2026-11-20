import copy
import unittest

from check_runtime_recovery import verify


class RecoveryTests(unittest.TestCase):
    def test_running_must_recover_and_retired_must_stay_stopped(self):
        record = {'observed_at': 'fixture', 'containers': [
            {'name': 'qldapm-ai-stage-' + name, 'image': 'pinned', 'mounts': [],
             'ports': {}, 'restart': 'unless-stopped', 'status': status, 'health': health}
            for name, status, health in [('web', 'running', 'healthy'), ('radmin', 'exited', None)]],
            'databases': {}, 'gateways': {}, 'private_metadata': {},
            'http': {'18091': 200, '18092': 200}}
        verify(record, copy.deepcopy(record))
        for index, status, health, expected in [(0, 'exited', None, 'NOT_HEALTHY'),
                                                (1, 'running', 'healthy', 'STOPPED_SERVICE_RESTARTED')]:
            after = copy.deepcopy(record)
            after['containers'][index].update(status=status, health=health)
            with self.assertRaisesRegex(AssertionError, expected):
                verify(record, after)


if __name__ == '__main__':
    unittest.main()
