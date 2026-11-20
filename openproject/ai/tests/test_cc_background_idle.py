import tempfile,time,unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gateway.store import Store
from gateway import engineering_github_operations as operations,engineering_github_poll as github,engineering_status_sync as native_sync,engineering,engineering_lifecycle


class IdlePollingTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.service=SimpleNamespace(store=Store(Path(tmp.name)),config={'project_id':6,'engineering':{'github_sync':{'enabled':True,'actor':18,'interval_seconds':300}}})

    def test_warm_engineering_schema_reads_do_not_wait_for_an_unrelated_writer(self):
        for initialize in (engineering_lifecycle.setup,engineering.setup):
            initialize(self.service.store)
        original=self.service.store.connect
        @contextmanager
        def nonblocking():
            with original() as db:
                db.execute('PRAGMA busy_timeout=0')
                yield db
        with original() as writer:
            writer.execute('BEGIN IMMEDIATE')
            with patch.object(self.service.store,'connect',nonblocking):
                for initialize in (engineering_lifecycle.setup,engineering.setup):
                    initialize(self.service.store)
            self.assertEqual(writer.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],'OFF')

    def test_idle_poll_does_not_acquire_a_sqlite_writer_lock(self):
        with self.service.store.connect() as db:
            operations.setup(db)
            db.execute('CREATE TABLE engineering_github_poll(project INTEGER PRIMARY KEY,next_at REAL NOT NULL,lease TEXT,lease_until REAL NOT NULL,error TEXT)')
            db.execute('INSERT INTO engineering_github_poll VALUES(6,?,NULL,0,NULL)',(time.time()+300,))
        writes=[];original=self.service.store.connect
        @contextmanager
        def traced():
            with original() as db:
                db.set_trace_callback(lambda sql:writes.append(sql) if sql.upper().startswith(('BEGIN IMMEDIATE','CREATE','UPDATE','INSERT','DELETE')) else None)
                yield db
        with patch.object(self.service.store,'connect',traced):
            for _ in range(20):self.assertEqual(github.tick(self.service)['reason'],'NOT_DUE')
        self.assertEqual(writes,[],'idle background work contends with UI reads for a SQLite writer lock')

    def test_native_observer_is_bounded_before_scanning_completed_sources(self):
        self.service.config['engineering']['status_sync']={'enabled':True}
        with patch.object(native_sync,'sources',return_value=[]) as scan:
            for _ in range(20):native_sync.tick(self.service)
        self.assertEqual(scan.call_count,1)
