from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gateway.engineering_planning import integration_base
from gateway.store import Store


class IntegrationBaseTests(unittest.TestCase):
    def test_only_verified_release_with_exact_dependency_ancestry_can_be_new_unit_base(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory));service=SimpleNamespace(store=store)
            release={'state':'DEPLOYED_TO_DEMO','head_sha':'b'*40,'branch':'codex/demo-integration-20261103'}
            with patch('gateway.engineering_github_details.verified_release',return_value=release):
                self.assertEqual(integration_base(service,'a'*40),{})
                with store.connect() as db:
                    db.execute('create table engineering_github_release_ancestry(head_sha text,release_sha text,verified real)')
                    db.execute('insert into engineering_github_release_ancestry values(?,?,0)',('a'*40,'b'*40))
                self.assertEqual(integration_base(service,'a'*40),{'base_sha':'b'*40,'base_branch':release['branch']})
                self.assertEqual(integration_base(service,'c'*40),{})
                release['head_sha']='d'*40
                self.assertEqual(integration_base(service,'a'*40),{})
