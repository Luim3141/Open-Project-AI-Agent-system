import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import verify_ciphertext_copy as checker


class CiphertextCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.expected = {}
        for name, content in [('n8n-recovery-v1.aesgcm', b'synthetic ciphertext'),
                              ('portable_recovery_restore.js', b'synthetic verifier'),
                              ('FORMAT.json', b'{"synthetic":true}')]:
            (self.root / name).write_bytes(content)
            self.expected[name] = hashlib.sha256(content).hexdigest()
        pin = patch.object(checker, 'EXPECTED', self.expected)
        pin.start()
        self.addCleanup(pin.stop)

    def test_exact_copy_is_read_only_and_does_not_claim_restore_or_offhost(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = checker.verify(self.root)
        self.assertEqual(result['status'], 'CIPHERTEXT_COPY_BYTES_VERIFIED')
        self.assertFalse(result['key_read'])
        self.assertEqual(result['offhost_custody'], 'OWNER_ATTESTATION_PENDING')
        self.assertEqual(result['physical_restore'], 'NOT_TESTED')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_recovery_key_or_extra_file_is_rejected_before_hashing(self):
        (self.root / 'recovery.key').write_bytes(b'never read this key')
        with patch.object(checker, 'file_hash', side_effect=AssertionError('MUST_NOT_READ')):
            with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_FILE_SET_DENIED'):
                checker.verify(self.root)

    def test_tamper_is_rejected(self):
        (self.root / 'FORMAT.json').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_HASH_MISMATCH'):
            checker.verify(self.root)

    def test_missing_file_or_directory_instead_of_file_is_rejected(self):
        (self.root / 'FORMAT.json').unlink()
        with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_FILE_SET_DENIED'):
            checker.verify(self.root)
        (self.root / 'FORMAT.json').mkdir()
        with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_REGULAR_FILE_REQUIRED'):
            checker.verify(self.root)

    def test_symlinked_input_is_rejected(self):
        target = self.root / 'FORMAT.json'
        target.unlink()
        try:
            target.symlink_to(self.root / 'portable_recovery_restore.js')
        except OSError:
            self.skipTest('OS symlink privilege unavailable')
        with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_LINK_DENIED'):
            checker.verify(self.root)

    def test_oversize_input_fails_before_reading(self):
        with patch.object(checker, 'MAX_FILE_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_SIZE_DENIED'):
                checker.verify(self.root)

    def test_windows_reparse_point_is_rejected_without_symlink_privilege(self):
        with patch.object(Path, 'lstat', return_value=SimpleNamespace(st_file_attributes=1024)), \
                patch.object(Path, 'is_symlink', return_value=False), \
                patch.object(checker.stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024, create=True):
            with self.assertRaisesRegex(ValueError, 'CIPHERTEXT_LINK_DENIED'):
                checker.reject_link(self.root)


if __name__ == '__main__':
    unittest.main()
