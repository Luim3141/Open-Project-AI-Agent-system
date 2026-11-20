import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from validate_qdrant_snapshot import validate_snapshot


class SnapshotValidationTests(unittest.TestCase):
    def archive(self, content, name='0/wal/first-index'):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        path = Path(directory.name)/'fixture.snapshot'
        with tarfile.open(path, 'w:') as archive:
            member = tarfile.TarInfo(name); member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
        return path

    def test_valid_counter_does_not_claim_full_restore(self):
        result = validate_snapshot(self.archive(b'{"ack_index":382}'))
        self.assertEqual(result['status'], 'WAL_METADATA_VALID')
        self.assertIn('isolated restore', result['limitation'])

    def test_zero_counter_file_and_wrong_types_are_rejected(self):
        for content in (b'\0'*17, b'{"ack_index":true}', b'{"ack_index":-1}', b'[]'):
            with self.subTest(content=content):
                result = validate_snapshot(self.archive(content))
                self.assertEqual(result['status'], 'INVALID_WAL_METADATA')

    def test_traversal_and_missing_wal_metadata_do_not_pass(self):
        with self.assertRaisesRegex(ValueError, 'UNTRUSTED_SNAPSHOT'):
            validate_snapshot(self.archive(b'{}', '../0/wal/first-index'))
        self.assertEqual(validate_snapshot(self.archive(b'{}','config.json'))['status'], 'WAL_METADATA_NOT_FOUND')
