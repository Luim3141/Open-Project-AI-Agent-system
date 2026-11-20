import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class MainPortOperatorTests(unittest.TestCase):
    def test_hosts_command_keeps_main_gateway_and_internal_hosts(self):
        script = Path(__file__).resolve().parents[1] / 'manage_local.py'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'gateway').mkdir()
            config = root / 'gateway' / 'config.json'
            config.write_text(json.dumps({'project_id': 5, 'hosts': [], 'maintenance': True}))
            subprocess.run([sys.executable, str(script), 'hosts', '--runtime', str(root)], check=True, capture_output=True)
            actual = json.loads(config.read_text())
            self.assertEqual(actual['project_id'], 5)
            self.assertFalse(actual['maintenance'])
            for host in ('127.0.0.1:18089', 'localhost:18089', 'gateway:8090', 'qldapm-ai-gateway-1:8090'):
                self.assertIn(host, actual['hosts'])
            subprocess.run([sys.executable, str(script), 'hosts', '--runtime', str(root), '--host', 'example.test'],
                           check=True, capture_output=True)
            self.assertIn('example.test', json.loads(config.read_text())['hosts'])


if __name__ == '__main__':
    unittest.main()
