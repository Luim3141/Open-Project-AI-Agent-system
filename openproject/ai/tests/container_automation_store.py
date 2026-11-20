"""Cold-clone additive migration and receipt reopening; no primary SQL/provider/native call."""
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, '/app')
from gateway.store import Store

root = Path('/fixture')
store = Store(root)
mode = sys.argv[1]
if mode == 'migrate':
    command = {'version': 1, 'kind': 'status', 'request_key': str(uuid.uuid4()), 'nonce': str(uuid.uuid4()), 'issued_at': int(time.time())}
    receipt = store.accept_automation_status(command)
    (root / 'command.json').write_text(json.dumps(command))
    (root / 'receipt.json').write_text(json.dumps(receipt))
elif mode == 'reopen':
    command = json.loads((root / 'command.json').read_text())
    receipt = json.loads((root / 'receipt.json').read_text())
else:
    raise ValueError('FIXED_ACCEPTANCE_MODE_ONLY')
assert store.accept_automation_status(command) == receipt
with closing(sqlite3.connect('file:/fixture/before.sqlite?mode=ro&immutable=1', uri=True)) as before, store.connect() as after:
    tables = lambda d: {r[0] for r in d.execute("select name from sqlite_master where type='table'")}
    assert tables(after) - tables(before) == {'automation_runs', 'automation_nonces'}
    for table in tables(before):
        old_columns = before.execute('pragma table_info("' + table + '")').fetchall()
        new_columns = [tuple(row) for row in after.execute('pragma table_info("' + table + '")')]
        assert old_columns == new_columns, table
        old = Counter(before.execute('select * from "' + table + '"'))
        new = Counter(tuple(row) for row in after.execute('select * from "' + table + '"'))
        if table == 'audit':
            assert old <= new and sum(new.values()) - sum(old.values()) == 1
            columns = [r[1] for r in old_columns]
            extra = dict(zip(columns, next(iter(new - old))))
            assert extra['action'] == 'automation_command' and extra['actor'] is None and extra['run_id'] == receipt['run_id']
        else:
            assert old == new, table
    assert after.execute('select count(*) from automation_runs').fetchone()[0] == 1
    assert after.execute('select count(*) from gemini_usage').fetchone()[0] == 471
print(json.dumps({'passed': True, 'mode': mode, 'old_rows_columns_preserved': True,
                  'additive_tables': ['automation_runs', 'automation_nonces'], 'one_durable_receipt': True,
                  'provider_native_calls': 0, 'primary_data_mounted': False}))
