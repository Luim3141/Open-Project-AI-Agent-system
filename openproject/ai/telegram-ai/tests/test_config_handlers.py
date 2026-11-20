import tempfile
import unittest
from pathlib import Path


class ConfigTests(unittest.TestCase):
    def test_bounded_context_keeps_acceptance_even_after_large_artifacts(self):
        from app.tools import context_result
        value={'task_id':391,'artifacts':[{'content':'x'*10000} for _ in range(10)],
               'acceptance_status':'AWAITING_OWNER_APPROVAL','workflow_status':'COMPLETED',
               'source_conflicts':[{'reason':'HISTORICAL_DATA'}]}
        compact=context_result(value)
        self.assertTrue(compact['truncated'])
        self.assertEqual(compact['verified_summary']['acceptance_status'],'AWAITING_OWNER_APPROVAL')
        self.assertEqual(compact['verified_summary']['source_conflicts'], value['source_conflicts'])
    def test_owner_selected_flash_lite_is_the_default(self):
        from app.config import Settings
        self.assertEqual(Settings().gemini_model,'gemini-3.5-flash-lite')

    def test_explicit_local_key_overrides_optional_shared_file(self):
        from app.config import secret
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'key';path.write_text('existing')
            self.assertEqual(secret('new-local',str(path)),'new-local')
            self.assertEqual(secret('',str(path)),'existing')
    def test_missing_configuration_reports_names_without_secret(self):
        from app.config import Settings
        settings=Settings()
        self.assertIn('TELEGRAM_BOT_TOKEN',settings.missing())
        self.assertIn('QLDAPM_ALLOWED_PROJECT_IDS',settings.missing())
        self.assertNotIn('gemini_api_key',repr(settings))

    def test_project_scope_and_state_fingerprint_ignores_observation_time(self):
        from app.tools import state_fingerprint
        self.assertEqual(state_fingerprint({'revision':'a','observed_at':1}),state_fingerprint({'revision':'a','observed_at':2}))
        self.assertNotEqual(state_fingerprint({'revision':'a'}),state_fingerprint({'revision':'b'}))

    def test_long_messages_are_split_without_losing_text(self):
        from app.handlers import chunks
        text='Tiếng Việt ' * 1000
        parts=chunks(text)
        self.assertTrue(all(len(part)<=3800 for part in parts))
        self.assertEqual(''.join(parts),text)

    def test_tool_declarations_validate_against_installed_google_sdk(self):
        from app.tools import declarations
        from google.genai import types
        values=[types.FunctionDeclaration(**item) for item in declarations()]
        self.assertGreater(len(values),20)


if __name__=='__main__':unittest.main()
