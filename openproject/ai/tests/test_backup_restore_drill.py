"""Data Backup & Restore Drill Test Suite (P09-05).
Verifies consistent, atomic backup and restore across:
1. SQLite WAL (AI Gateway store, tasks, usage, proposals) with PRAGMA integrity check.
2. n8n Community workflow SQLite database and encryption key.
3. Postgres database dump and assets archive verification via manifest checksums.
"""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from local_backup import archive, backup_machine_key, backup_n8n_owner, sqlite_snapshot


class BackupRestoreDrillTests(unittest.TestCase):
    def test_sqlite_wal_backup_and_restore_roundtrip(self):
        """Verifies SQLite database with active WAL journal can be snapshotted and restored without corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_db = root / "source.sqlite"
            snapshot_db = root / "snapshot.sqlite"
            restored_db = root / "restored.sqlite"

            # 1. Initialize SQLite database in WAL mode with test records
            with closing(sqlite3.connect(source_db)) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("CREATE TABLE proposals (id INTEGER PRIMARY KEY, title TEXT, status TEXT)")
                db.execute("CREATE TABLE tokens (actor INTEGER, balance INTEGER)")
                for i in range(1, 101):
                    db.execute("INSERT INTO proposals VALUES (?, ?, ?)", (i, f"Proposal #{i}", "APPROVED"))
                db.execute("INSERT INTO tokens VALUES (10, 500)")
                db.commit()

            # 2. Take WAL-consistent snapshot
            sqlite_snapshot(source_db, snapshot_db)
            self.assertTrue(snapshot_db.exists())

            # 3. Restore to a new location (simulating restore drill)
            with closing(sqlite3.connect(snapshot_db)) as src, closing(sqlite3.connect(restored_db)) as dst:
                src.backup(dst)

            # 4. Integrity check on restored database
            with closing(sqlite3.connect(restored_db)) as db:
                integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
                self.assertEqual(integrity.lower(), "ok")

                proposal_count = db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
                self.assertEqual(proposal_count, 100)

                balance = db.execute("SELECT balance FROM tokens WHERE actor=10").fetchone()[0]
                self.assertEqual(balance, 500)

    def test_n8n_encryption_key_and_credentials_backup_restore(self):
        """Verifies n8n workflow encryption keys and owner credentials backup and restore consistency."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_owner = root / "owner.json"
            backup_owner = root / "owner-backup.json"
            restored_owner = root / "owner-restored.json"
            n8n_db = root / "n8n.sqlite"

            # Setup n8n database with instance owner set up
            with closing(sqlite3.connect(n8n_db)) as db:
                db.execute("CREATE TABLE settings (key TEXT, value TEXT)")
                db.execute("INSERT INTO settings VALUES ('userManagement.isInstanceOwnerSetUp', 'true')")
                db.commit()

            owner_payload = {
                "schema_version": 1,
                "endpoint": "http://localhost:5678",
                "password": "SecurePUBLICATION_REDACTED",
                "encryptionKey": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            }
            source_owner.write_text(json.dumps(owner_payload))

            # Backup
            self.assertTrue(backup_n8n_owner(source_owner, backup_owner, n8n_db))
            self.assertEqual(backup_owner.read_text(), source_owner.read_text())

            # Restore simulation
            restored_owner.write_text(backup_owner.read_text())
            restored_data = json.loads(restored_owner.read_text())
            self.assertEqual(restored_data["encryptionKey"], owner_payload["encryptionKey"])
            self.assertEqual(restored_data["password"], owner_payload["password"])

    def test_backup_archive_manifest_checksum_verification(self):
        """Verifies backup tar archive produces verifiable SHA-256 manifest and restores identically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "stage-data"
            data_dir.mkdir()
            archive_file = root / "backup.tar"
            extract_dir = root / "restored-data"
            extract_dir.mkdir()

            # Create sample state files
            (data_dir / "database.dump").write_bytes(b"PG_DUMP_SYNTHETIC_HEADER_" + b"x" * 2048)
            (data_dir / "config.json").write_text(json.dumps({"project_id": 5, "mode": "native"}))
            (data_dir / "tokens.json").write_text(json.dumps({"active_tokens": 20}))

            # Generate archive and manifest
            manifest = archive(data_dir, archive_file)
            self.assertEqual(len(manifest), 3)

            # Extract archive to simulated restore target
            import tarfile
            with tarfile.open(archive_file, "r") as stream:
                stream.extractall(extract_dir)

            # Verify every restored file matches original SHA-256
            for line in manifest:
                expected_hash, rel_path = line.split("  ")
                clean_path = rel_path.lstrip("./")
                restored_file = extract_dir / clean_path
                self.assertTrue(restored_file.exists(), f"Missing restored file {clean_path}")
                actual_hash = hashlib.sha256(restored_file.read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash, f"Hash mismatch on {clean_path}")


if __name__ == "__main__":
    unittest.main()
