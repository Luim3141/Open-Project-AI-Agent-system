"""Temporary synthetic SQLite/archive checks; never open live Windows Gateway WAL."""
from pathlib import Path
from contextlib import closing
import sqlite3
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from jira_sync_backup import read_database_state
from local_backup import archive, backup_machine_key, backup_n8n_owner, files, sqlite_snapshot


class LocalBackupTests(unittest.TestCase):
    def test_second_brain_snapshot_restores_fts_chunks_and_acl_metadata(self):
        from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
        from gateway.knowledge_ingestion import KnowledgeIngester
        from gateway.knowledge_classifier import classify_document, KnowledgeDocType
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'knowledge.sqlite';target=root/'restored.sqlite'
            store=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(source)))
            doc=classify_document(KnowledgeDocType.WORK_PACKAGE,'3','actor:7:wp:2',
                'Knowledge backup fixture','Synthetic backup content',metadata={'actor_id':7,'native_id':2,'lock_version':1})
            KnowledgeIngester(storage=store).ingest(doc)
            sqlite_snapshot(source,target)
            restored=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(target)))
            self.assertEqual(restored.count_documents(),store.count_documents())
            with closing(sqlite3.connect(target)) as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                self.assertGreater(db.execute('SELECT COUNT(*) FROM knowledge_chunks').fetchone()[0],0)
                self.assertGreater(db.execute("SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH 'backup'").fetchone()[0],0)

    def test_machine_secret_is_optional_before_enrollment_and_exact_private_bytes_after(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / 'automation.key', root / 'automation-backup.key'
            self.assertFalse(backup_machine_key(source, target))
            source.write_bytes(b'a' * 64)
            self.assertTrue(backup_machine_key(source, target))
            self.assertEqual(target.read_bytes(), source.read_bytes())
            source.write_bytes(b'INVALID')
            with self.assertRaisesRegex(ValueError, 'KEY_INVALID'):
                backup_machine_key(source, root / 'invalid.key')

    def test_owner_backup_is_required_after_claim_and_copied_only_to_private_backup(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / 'n8n.sqlite'
            with closing(sqlite3.connect(snapshot)) as database:
                database.execute('create table settings(key text,value text)')
                database.execute("insert into settings values('userManagement.isInstanceOwnerSetUp','false')")
                database.commit()
            source, target = root / 'owner.json', root / 'owner-backup.json'
            self.assertFalse(backup_n8n_owner(source, target, snapshot))
            with closing(sqlite3.connect(snapshot)) as database:
                database.execute("update settings set value='true'")
                database.commit()
            with self.assertRaisesRegex(ValueError, 'CREDENTIAL_BACKUP_REQUIRED'):
                backup_n8n_owner(source, target, snapshot)
            source.write_text(json.dumps({'schema_version': 1, 'endpoint': 'http://localhost:5678', 'password': 'FixtureAa9!'}))
            self.assertTrue(backup_n8n_owner(source, target, snapshot))
            self.assertEqual(source.read_bytes(), target.read_bytes())
            source.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'SOURCE_INVALID'):
                backup_n8n_owner(source, root / 'invalid.json', snapshot)

    def test_waiting_intents_allow_backup_but_executing_legacy_and_unknown_jobs_block(self):
        from local_backup import active_work
        from gateway.store import Store
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            store.enqueue_run(7, {"prompt": "synthetic", "allow_routine_writes": False, "write_scope_ids": []})
            with store.connect() as database:
                self.assertEqual(active_work(database), 0)
            store.claim_run()
            with store.connect() as database:
                self.assertEqual(active_work(database), 1)
                database.execute("DELETE FROM ai_queue")
                self.assertEqual(active_work(database), 1)
                database.execute("UPDATE ai_runs SET state='failed_or_unknown'")
                database.execute("INSERT INTO jobs(id,state) VALUES('synthetic','failed_or_unknown')")
                self.assertEqual(active_work(database), 1)

    def test_wal_without_sidecars_never_opens_the_readonly_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            with closing(sqlite3.connect(source)) as database:
                database.execute('pragma journal_mode=WAL')
                database.execute('create table items(value text)')
                database.execute("insert into items values ('retained')")
                database.commit()
            self.assertFalse(source.with_name(source.name + '-shm').exists())
            before = source.read_bytes()
            real_connect = sqlite3.connect
            def readonly_mount(path, *args, **kwargs):
                if str(path).startswith(source.as_uri()) or str(path) == str(source):
                    raise sqlite3.OperationalError('readonly fixture cannot create SHM')
                return real_connect(path, *args, **kwargs)
            target = root / 'snapshot.sqlite'
            with patch('local_backup.sqlite3.connect', side_effect=readonly_mount):
                sqlite_snapshot(source, target)
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(source.with_name(source.name + '-shm').exists())
            with closing(real_connect(target)) as restored:
                self.assertEqual(restored.execute('select value from items').fetchall(), [('retained',)])

    def test_snapshot_keeps_committed_wal_and_excludes_uncommitted_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            with closing(sqlite3.connect(source)) as writer:
                writer.execute('pragma journal_mode=WAL')
                writer.execute('create table items(value text)')
                writer.execute("insert into items values ('committed')")
                writer.commit()
                writer.execute("insert into items values ('uncommitted')")
                # Windows locks SHM byte ranges; DB/WAL are the persistent snapshot inputs.
                before = {p.name: p.read_bytes() for p in root.glob('source.sqlite*') if not p.name.endswith('-shm')}
                target = root / 'snapshot.sqlite'
                sqlite_snapshot(source, target)
                self.assertEqual({p.name: p.read_bytes() for p in root.glob('source.sqlite*') if not p.name.endswith('-shm')}, before)
                with closing(sqlite3.connect(target)) as restored:
                    self.assertEqual(restored.execute('select value from items').fetchall(), [('committed',)])

    def test_snapshot_rejects_source_commit_during_copy(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            with closing(sqlite3.connect(source)) as writer:
                writer.execute('create table items(value text)')
                writer.commit()
            real_copy = shutil.copyfile
            def changed_copy(incoming, outgoing):
                result = real_copy(incoming, outgoing)
                if Path(incoming) == source:
                    with closing(sqlite3.connect(source)) as writer:
                        writer.execute("insert into items values ('concurrent commit')")
                        writer.commit()
                return result
            target = root / 'snapshot.sqlite'
            with patch('local_backup.shutil.copyfile', side_effect=changed_copy):
                with self.assertRaisesRegex(ValueError, 'SQLITE_SOURCE_CHANGED_DURING_COPY'):
                    sqlite_snapshot(source, target)
            self.assertFalse(target.exists())

    def test_missed_days_trigger_one_backup_and_no_replay_flood(self):
        import local_backup
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            def completed():
                local_backup.save(output / 'last-success.json', {'at': 1_000_000, 'id': 'fixture'})
                return {'passed': True}
            with patch.object(local_backup, 'OUTPUT', output), \
                    patch.object(local_backup.time, 'time', return_value=1_000_000), \
                    patch.object(local_backup.time, 'sleep', side_effect=[None, None, RuntimeError('end-test')]), \
                    patch.object(local_backup, 'once', side_effect=completed) as backup, patch('builtins.print'):
                with self.assertRaisesRegex(RuntimeError, 'end-test'):
                    local_backup.watch()
                self.assertEqual(backup.call_count, 1)

    def test_live_wal_snapshot_restores_committed_data_without_touching_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            with closing(sqlite3.connect(source)) as writer:
                writer.execute('PRAGMA journal_mode=WAL')
                writer.execute('create table items(id integer primary key, value text)')
                writer.execute("insert into items(value) values ('retained')")
                writer.commit()
                checkpoint = root / 'snapshot.sqlite'
                checksum = sqlite_snapshot(source, checkpoint)
                self.assertEqual(len(checksum), 64)
                with closing(sqlite3.connect(checkpoint)) as restored:
                    self.assertEqual(restored.execute('pragma journal_mode').fetchone()[0], 'delete')
                    self.assertEqual(restored.execute('select value from items').fetchall(), [('retained',)])
                with self.assertRaisesRegex(ValueError, 'TARGET_EXISTS'):
                    sqlite_snapshot(source, checkpoint)
                self.assertEqual(writer.execute('select count(*) from items').fetchone()[0], 1)

    def test_archive_keeps_nested_payload_named_like_root_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'
            (root / 'binaryData').mkdir(parents=True)
            (root / 'database.sqlite-wal').write_bytes(b'fixture')
            (root / 'binaryData/database.sqlite-user-upload').write_bytes(b'keep')
            target = Path(directory) / 'files.tar'
            entries = archive(root, target, ('database.sqlite',))
            self.assertEqual(len(entries), 1)
            with tarfile.open(target) as incoming:
                self.assertEqual(incoming.getnames(), ['./binaryData/database.sqlite-user-upload'])
            with self.assertRaisesRegex(ValueError, 'DIRECTORY_MISSING'):
                files(root / 'missing')

    def test_database_fingerprint_rejects_untrusted_table_identifier(self):
        with self.assertRaisesRegex(ValueError, 'DATABASE_TABLE_SCOPE_INVALID'):
            read_database_state(lambda sql: b'bad;table\n')
