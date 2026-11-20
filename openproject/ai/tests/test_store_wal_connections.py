import sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gateway.store import Store


class StoreWalTests(unittest.TestCase):
    def test_wal_is_persistent_without_reissuing_mode_changes_on_every_connection(self):
        statements=[];original=sqlite3.connect
        def tracked(*args,**kwargs):
            db=original(*args,**kwargs);db.set_trace_callback(statements.append);return db
        with tempfile.TemporaryDirectory() as root,patch('gateway.store.sqlite3.connect',side_effect=tracked):
            store=Store(Path(root))
            for _ in range(8):
                with store.connect() as db:self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0],'wal')
            try:
                with store.connect() as db:
                    db.execute("INSERT INTO audit(id,action) VALUES('rollback','fixture')")
                    raise ValueError('rollback')
            except ValueError:pass
            with store.connect() as db:self.assertIsNone(db.execute("SELECT id FROM audit WHERE id='rollback'").fetchone())
        self.assertEqual(sum(s.upper()=='PRAGMA JOURNAL_MODE=WAL' for s in statements),1)


if __name__=='__main__':unittest.main()
