import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.gemini import Gemini, MODEL
from gateway.store import Store, canonical, digest


class ReadinessTests(unittest.TestCase):
    def test_persisted_probe_bound_to_exact_policy_and_no_sdk_on_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = {'project': 'fixture', 'model': MODEL, 'key_sha256': digest('synthetic'),
                      'limits': {'rpm': 13, 'tpm': 225000, 'rpd': 450}}
            gemini = Gemini(root)
            with patch.object(Gemini, 'sdk_client', side_effect=AssertionError('no outbound')) as sdk:
                self.assertEqual(gemini.readiness(policy)['state'], 'READINESS_NOT_VERIFIED')
                receipt = {'passed': True, 'policy_sha256': digest(canonical(policy)),
                           'key_sha256': policy['key_sha256'], 'model': MODEL, 'checked_at': time.time() - 1}
                (root / 'gemini-readiness.json').write_text(json.dumps(receipt))
                self.assertEqual(Gemini(root).readiness(policy)['state'], 'READY')
                self.assertFalse(gemini.readiness(policy)['network_checked_now'])
                self.assertEqual(gemini.readiness({**policy, 'project': 'changed'})['state'], 'READINESS_NOT_VERIFIED')
                for reason, expected in [('GEMINI_QUOTA_429', 'WAITING_QUOTA'), ('GEMINI_TIMEOUT', 'PROVIDER_UNAVAILABLE'),
                                         ('GEMINI_AUTH_401', 'BLOCKED_KEY_OR_MODEL')]:
                    Store(root).block_gemini('fixture', reason)
                    self.assertEqual(Gemini(root).readiness(policy)['state'], expected)
                sdk.assert_not_called()
