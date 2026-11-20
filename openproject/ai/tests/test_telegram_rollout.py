import tempfile
import unittest
from pathlib import Path

from automation.telegram_rollout import source_diff, replacement_env, approved_sources, initialize_files


class TelegramRolloutTests(unittest.TestCase):
    def test_observer_action_uses_existing_view_permission(self):
        source = Path(__file__).resolve().parents[1] / 'core/overlay/config/initializers/qldapm_gates.rb'
        actions = source.read_text(encoding='utf-8').split('permission(:view_work_packages)', 1)[1].split('clear_caches', 1)[0]
        self.assertIn('qldapm_ai/observer', actions.split())
        controller = source.parents[2] / 'app/controllers/qldapm_ai_controller.rb'
        self.assertIn('observer', controller.read_text(encoding='utf-8').split('include?(action_name)', 1)[0].rsplit('%w[', 1)[1].split(']')[0].split())

    def test_source_diff_keeps_existing_and_new_code_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'gateway').mkdir()
            (root / 'gateway/app.py').write_text('new')
            (root / 'gateway/new.py').write_text('added')
            (root / 'gateway/private.key').write_text('secret')
            result = source_diff(root, {'gateway/app.py': 'old'})
            self.assertEqual(set(result), {'gateway/app.py', 'gateway/new.py'})

    def test_image_env_replacement_is_exact_and_keeps_other_settings(self):
        self.assertEqual(replacement_env('AI_IMAGE=old\nKEY=preserve\n', 'AI_IMAGE', 'new'),
                         'AI_IMAGE=new\nKEY=preserve\n')
        with self.assertRaises(ValueError):
            replacement_env('AI_IMAGE=a\nAI_IMAGE=b\n', 'AI_IMAGE', 'new')

    def test_unrelated_source_drift_is_never_deployed(self):
        changes = {'gateway/agent_observer.py': 'a', 'gateway/intent_evals.py': 'b',
                   'gateway/private.key': 'c', 'core/overlay/app/views/qldapm_ai/observer.html.erb': 'd'}
        self.assertEqual(set(approved_sources(changes)),
                         {'gateway/agent_observer.py', 'core/overlay/app/views/qldapm_ai/observer.html.erb'})

    def test_initialization_keeps_existing_credentials_and_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initialize_files(root)
            (root / '.env').write_text('TELEGRAM_BOT_TOKEN=preserved\n')
            key = (root / 'secrets/notification.key').read_bytes()
            initialize_files(root)
            self.assertEqual((root / '.env').read_text(), 'TELEGRAM_BOT_TOKEN=preserved\n')
            self.assertEqual((root / 'secrets/notification.key').read_bytes(), key)


if __name__ == '__main__':
    unittest.main()
