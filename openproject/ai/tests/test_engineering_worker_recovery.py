import subprocess
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from automation import engineering_worker as worker


class EngineeringWorkerRecoveryTests(unittest.TestCase):
    def test_gateway_reserved_cap_reaches_envelope_and_provider_gate(self):
        def operator(action, **kwargs):
            return {'calls': 3} if action == 'reserve' else {}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(worker, 'checkpoint'), \
             patch.object(worker, 'operator', side_effect=operator), \
             patch('automation.engineering_bootstrap.activate', return_value={}), \
             patch.object(worker, 'write_linux') as write, \
             patch.object(worker, 'CURRENT_JOURNAL', None), \
             patch.object(worker, 'gate', side_effect=RuntimeError('fixture-stop-before-provider')) as gate:
            with self.assertRaisesRegex(RuntimeError, 'fixture-stop-before-provider'):
                worker.inference('fixture-run', Path(directory), 'dev', 'dev-0', 'fixture', calls=12)
            envelope = json.loads(write.call_args.args[1].split('\n', 1)[0].removeprefix('Trusted engineering envelope: '))
            self.assertEqual(envelope['request_allowance'], 3)
            self.assertEqual(gate.call_args.args[0]['remaining'], 3)

    def process(self):
        process = Mock(returncode=0)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired('openclaw', 2), (b'completed', b'')]
        return process

    def test_active_auto_and_run_once_survive_a_poll_timeout(self):
        for mode in ('AUTO', 'RUN_ONCE'):
            with self.subTest(mode=mode):
                signal = {'mode': mode, 'queue_state': 'executing',
                          'cancel_requested': False, 'deadline': float('inf')}
                process = self.process()
                with patch.object(worker.subprocess, 'Popen', return_value=process), \
                     patch.object(worker, 'operator', return_value=signal), \
                     patch.object(worker, 'gate') as gate, \
                     patch.object(worker, 'wsl', return_value=Mock(returncode=0)) as wsl:
                    result = worker.agent_process('run', 'dev', 'session', 'prompt')
                self.assertEqual(result.stdout, b'completed')
                process.terminate.assert_not_called()
                gate.assert_not_called()
                wsl.assert_not_called()

    def test_auto_deadline_is_not_misreported_as_pause(self):
        signal = {'mode': 'AUTO', 'queue_state': 'executing',
                  'cancel_requested': False, 'deadline': 0}
        process = self.process()
        with patch.object(worker.subprocess, 'Popen', return_value=process), \
             patch.object(worker, 'operator', return_value=signal), \
             patch.object(worker, 'gate'), \
             patch.object(worker, 'wsl', return_value=Mock(returncode=0)), \
             patch.object(worker, 'CURRENT_JOURNAL', None):
            with self.assertRaisesRegex(RuntimeError, 'ENGINEERING_DEADLINE_EXCEEDED'):
                worker.agent_process('run', 'dev', 'session', 'prompt')
        process.terminate.assert_called_once()

    def test_pause_and_cancel_still_fence_the_process(self):
        for mode, cancelled, expected in (
                ('PAUSED', False, 'ENGINEERING_PAUSED_CHECKPOINT_REQUIRED'),
                ('OFF', False, 'ENGINEERING_PAUSED_CHECKPOINT_REQUIRED'),
                ('AUTO', True, 'ENGINEERING_CANCELLED')):
            with self.subTest(mode=mode, cancelled=cancelled):
                signal = {'mode': mode, 'queue_state': 'executing',
                          'cancel_requested': cancelled, 'deadline': float('inf')}
                process = self.process()
                with patch.object(worker.subprocess, 'Popen', return_value=process), \
                     patch.object(worker, 'operator', return_value=signal), \
                     patch.object(worker, 'gate') as gate, \
                     patch.object(worker, 'wsl', return_value=Mock(returncode=0)) as wsl, \
                     patch.object(worker, 'CURRENT_JOURNAL', None):
                    with self.assertRaisesRegex(RuntimeError, expected):
                        worker.agent_process('run', 'dev', 'session', 'prompt')
                process.terminate.assert_called_once()
                gate.assert_called_once_with()
                wsl.assert_called_once()


if __name__ == '__main__':
    unittest.main()
