"""Account for actual read-only Core bridge audit/nonces, preserving every other Gateway value."""
import json
import shutil
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path

sys.path.insert(0, "/trusted")
from local_backup import sqlite_snapshot

sqlite_snapshot(Path("/sources/gateway/gateway.sqlite"), Path("/tmp/after.sqlite"))
shutil.copyfile("/before.sqlite", "/tmp/before.sqlite")
with closing(sqlite3.connect("/tmp/before.sqlite")) as before, closing(sqlite3.connect("/tmp/after.sqlite")) as after:
    names = [r[0] for r in before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    assert names == [r[0] for r in after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for name in names:
        assert before.execute('PRAGMA table_info("' + name + '")').fetchall() == after.execute('PRAGMA table_info("' + name + '")').fetchall()
        if name not in {"audit", "ui_nonces"}:
            assert Counter(before.execute('SELECT * FROM "' + name + '"')) == Counter(after.execute('SELECT * FROM "' + name + '"')), name
    original = Counter(before.execute("SELECT * FROM audit"))
    current = Counter(after.execute("SELECT * FROM audit"))
    assert original <= current
    columns = [r[1] for r in before.execute("PRAGMA table_info(audit)")]
    extra = [dict(zip(columns, row)) for row in (current - original).elements()]
    expected = Counter({(actor, action): amount for actor in (6, 7, 8, 9, 10)
        for action, amount in (("identity", 1), ("list_agent_runs", 1), ("get_permissions", 1), ("transport", 3))})
    assert Counter((r["actor"], r["action"]) for r in extra) == expected
    for row in extra:
        assert (row["target"], row["outcome"]) == (("/internal/ui", "200") if row["action"] == "transport" else ("qldapm-local", "ok"))
    old_nonces = dict(before.execute("SELECT nonce,expires FROM ui_nonces"))
    new_nonces = dict(after.execute("SELECT nonce,expires FROM ui_nonces"))
    added = new_nonces.keys() - old_nonces.keys()
    removed = old_nonces.keys() - new_nonces.keys()
    assert len(added) == 15
    final_consume_at = max(new_nonces[n] for n in added) - 60
    assert all(old_nonces[n] <= final_consume_at + 0.01 for n in removed)
    assert all(old_nonces[n] == new_nonces[n] for n in old_nonces.keys() & new_nonces.keys())
    assert after.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
print(json.dumps({"passed": True, "all_prior_audit_retained": True, "exact_signed_read_audit_rows": len(extra),
    "exact_new_one_use_nonces": len(added), "only_previously_expired_nonces_pruned": len(removed),
    "all_other_gateway_rows_and_columns_unchanged": True, "usage_history_rows": 471}))
