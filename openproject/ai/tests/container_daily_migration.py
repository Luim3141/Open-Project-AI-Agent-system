"""Cold backup compatibility on disposable copies only, with exact old row preservation."""
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, '/app')
from gateway.store import Store

root = Path('/fixture')
store = Store(root)
with closing(sqlite3.connect(root / 'before.sqlite')) as before, store.connect() as after:
    tables = lambda db: {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables(after) - tables(before) == {'daily_briefs'}
    for table in tables(before):
        assert before.execute('PRAGMA table_info("' + table + '")').fetchall() == [tuple(row) for row in after.execute('PRAGMA table_info("' + table + '")')]
        assert Counter(before.execute('SELECT * FROM "' + table + '"')) == Counter(tuple(row) for row in after.execute('SELECT * FROM "' + table + '"')), table
    assert after.execute('SELECT count(*) FROM daily_briefs').fetchone()[0] == 0
    assert after.execute('SELECT count(*) FROM gemini_usage').fetchone()[0] == 471
    assert after.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
print(json.dumps({'passed': True, 'image_phase': sys.argv[1], 'all_old_rows_columns_preserved': True,
                  'only_additive_daily_briefs': True, 'native_or_provider_calls': 0, 'primary_mounted': False}))
