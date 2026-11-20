"""Operator clone guard does not depend on or inspect any Staging source."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class MainNativeCloneTests(unittest.TestCase):
    def test_migrations_require_exact_versions_and_explicit_candidate_before_any_docker_call(self):
        from automation.main_native_clone import main_native_clone
        with tempfile.TemporaryDirectory() as folder,patch('automation.main_native_clone.subprocess.run') as docker:
            for versions in [('20261026000000',),('latest',),('20261026000000;other',),['20261026000000']]:
                with self.assertRaisesRegex(ValueError,'ISOLATED_EXACT_CANDIDATE_MIGRATIONS_REQUIRED'):
                    with main_native_clone(folder,migration_versions=versions):pass
            docker.assert_not_called()

    def test_restore_and_cleanup_are_limited_to_new_labelled_clone_resources(self):
        from automation.main_native_clone import owned_resource
        identifier='11111111-1111-4111-8111-111111111111'
        name='qldapm-main-qualification-'+identifier+'-db'
        def inspect(args,**kwargs):
            self.assertEqual(args[:2],['docker','inspect'])
            self.assertEqual(args[-1],name)
            return (identifier+'\n').encode()
        with patch('automation.main_native_clone.subprocess.check_output',side_effect=inspect):
            self.assertTrue(owned_resource(name,identifier))
        for bad in ['qldapm-openproject-db-1','qldapm-ai-stage-db-1',name+'-other','../../db']:
            with self.assertRaises(ValueError):owned_resource(bad,identifier)
        with patch('automation.main_native_clone.subprocess.check_output',return_value=b'other-label\n'):
            self.assertFalse(owned_resource(name,identifier))

    def test_bridge_key_cannot_mount_arbitrary_host_secrets_or_an_invalid_key(self):
        from automation.main_native_clone import main_native_clone
        with tempfile.TemporaryDirectory() as folder,patch('automation.main_native_clone.subprocess.run') as docker:
            root=Path(folder)/'clone';outside=Path(folder)/'secret';outside.write_bytes(b'x'*32)
            with self.assertRaisesRegex(ValueError,'ISOLATED_CLONE_OWN_KEY_REQUIRED'):
                with main_native_clone(root,ui_key_path=outside):pass
            empty=root/'empty.key';empty.write_bytes(b'')
            with self.assertRaisesRegex(ValueError,'ISOLATED_CLONE_OWN_KEY_REQUIRED'):
                with main_native_clone(root,ui_key_path=empty):pass
            docker.assert_not_called()


if __name__=='__main__':unittest.main()
