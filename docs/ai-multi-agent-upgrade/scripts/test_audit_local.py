import json
import tempfile
import unittest
from pathlib import Path
from audit_local import container_summary, private_metadata


class AuditTests(unittest.TestCase):
    def test_container_projection_never_exports_env_values_or_health_logs(self):
        info = {'Name': '/fixture', 'Image': 'sha256:fixture',
                'Config': {'Env': ['API_KEY=NEVER_EXPORT'], 'Labels': {'com.docker.compose.project': 'qldapm-ai'}},
                'State': {'Status': 'running', 'Health': {'Status': 'healthy', 'Log': ['NEVER_EXPORT']}},
                'HostConfig': {'RestartPolicy': {'Name': 'unless-stopped'}, 'PortBindings': {}},
                'Mounts': [], 'NetworkSettings': {'Networks': {'private': {}}}}
        result = container_summary(info)
        self.assertEqual(result['environment_names'], ['API_KEY'])
        self.assertNotIn('NEVER_EXPORT', json.dumps(result))

    def test_private_projection_only_exports_presence_and_policy_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('gateway', 'stage-ai'):
                folder = root / name
                folder.mkdir()
                (folder / 'config.json').write_text(json.dumps({'project_id': 3, 'users': {'7': 'PM'}, 'secret': 'NEVER_EXPORT'}))
                for file in ('gemini.key', 'credentials.json', 'ui.key'):
                    (folder / file).write_text('NEVER_EXPORT')
            result = private_metadata(root)
            self.assertEqual(result['stage-ai']['files']['gemini.key'], 'PRESENT')
            self.assertFalse(result['stage-ai']['provider_enabled'])
            self.assertNotIn('NEVER_EXPORT', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
