"""Real disposable child processes, synthetic operator/gate only; no WSL/provider."""
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch
from automation import engineering_worker as worker


class WorkerProcessTests(unittest.TestCase):
    def run_child(self, signal, code, fence=0):
        popen = subprocess.Popen
        children = []
        def spawn(*args, **kwargs):
            child = popen([sys.executable, '-c', code], **kwargs)
            children.append(child)
            return child
        def operator(op, **args):
            return signal if op == 'signal' else {}
        with patch.object(worker.subprocess, 'Popen', side_effect=spawn), \
             patch.object(worker, 'operator', side_effect=operator), \
             patch.object(worker, 'gate') as gate, \
             patch.object(worker, 'wsl', return_value=Mock(returncode=fence)), \
             patch.object(worker, 'CURRENT_JOURNAL', None):
            try:
                return worker.agent_process('fixture', 'dev', 'fixture', 'fixture'), gate
            finally:
                for child in children:
                    if child.poll() is None: child.kill()
                    child.communicate(timeout=5)
                    self.assertIsNotNone(child.returncode)

    def signal(self, **values):
        return {'mode': 'AUTO', 'queue_state': 'executing', 'cancel_requested': False,
                'deadline': float('inf'), **values}

    def test_auto_survives_real_child_poll_and_collects_terminal_result(self):
        result, gate = self.run_child(self.signal(), 'import time;time.sleep(2.2);print("completed")')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), b'completed')
        gate.assert_not_called()

    def test_pause_cancel_and_failed_fence_terminate_real_child(self):
        for signal, fence, error in [(self.signal(mode='PAUSED'), 0, 'PAUSED_CHECKPOINT'),
                                     (self.signal(cancel_requested=True), 0, 'CANCELLED'),
                                     (self.signal(mode='OFF'), 1, 'OUTCOME_UNKNOWN')]:
            with self.subTest(error=error), self.assertRaisesRegex(RuntimeError, error):
                self.run_child(signal, 'import time;time.sleep(60)', fence)
