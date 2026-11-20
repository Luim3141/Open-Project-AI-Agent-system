"""Compare pre-deploy cold SQLite with a verified cold copy of current readonly stage source."""
import json
import shutil
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path

sys.path.insert(0, "/trusted")
from local_backup import sqlite_snapshot

assert sys.argv[1:] in ([], ["api-read-denial"])
api_mode = sys.argv[1:] == ["api-read-denial"]
sqlite_snapshot(Path("/sources/gateway/gateway.sqlite"), Path("/tmp/after.sqlite"))
# A cold backup can retain WAL mode; allow SHM only beside a private disposable copy.
shutil.copyfile("/before.sqlite", "/tmp/before.sqlite")
with closing(sqlite3.connect("/tmp/before.sqlite")) as before, closing(sqlite3.connect("/tmp/after.sqlite")) as after:
    names = [r[0] for r in before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    assert names == [r[0] for r in after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for name in names:
        old_columns = before.execute('PRAGMA table_info("' + name + '")').fetchall()
        new_columns = after.execute('PRAGMA table_info("' + name + '")').fetchall()
        assert new_columns[:len(old_columns)] == old_columns, name
        if name == "audit" and not api_mode:
            assert [(r[1], r[2], r[3], r[4]) for r in new_columns[len(old_columns):]] == [
                ("project_id", "INTEGER", 0, None), ("run_id", "TEXT", 0, None),
                ("task_id", "TEXT", 0, None), ("trace_id", "TEXT", 0, None)]
        else:
            assert new_columns == old_columns, name
        projection = ",".join('"' + r[1] + '"' for r in old_columns)
        original = Counter(before.execute('SELECT * FROM "' + name + '"').fetchall())
        current = Counter(after.execute('SELECT ' + projection + ' FROM "' + name + '"').fetchall())
        if name == "audit" and api_mode:
            assert original <= current and sum(current.values()) - sum(original.values()) == 1
            extra = dict(zip([r[1] for r in old_columns], next(iter(current - original))))
            assert (extra["actor"], extra["action"], extra["target"], extra["outcome"]) == (None, "access_denied", "/api/v1/agent-runs", "INVALID_OR_EXPIRED_TOKEN")
        else:
            assert original == current, "PRIOR_TABLE_VALUES_CHANGED:" + name
    assert after.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
    assert after.execute("PRAGMA quick_check").fetchone()[0] == "ok"
print(json.dumps({"passed": True, "prior_gateway_table_values_preserved": True,
    "documented_new_denied_read_audit_rows": 1 if api_mode else 0,
    "original_columns_unchanged": True, "only_additive_four_nullable_audit_id_columns": not api_mode,
    "source_opened_readonly_through_verified_cold_copy": True, "usage_history_rows": 471}))
