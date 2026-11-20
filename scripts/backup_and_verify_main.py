"""Comprehensive online backup of Main with clone restoration verification."""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'openproject/ai'))
from jira_sync_backup import command, inspect, database_state, read_database_state

DELIVERY_DIR = REPO / 'docs/ai-multi-agent-upgrade/run_20261021_final_delivery'
BACKUP_DIR = DELIVERY_DIR / 'backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=== STARTING MAIN PRE-DEPLOYMENT BACKUP ===", flush=True)
    web = inspect('qldapm-openproject-web-1')
    gateway = inspect('qldapm-ai-gateway-1')
    assert web['State']['Status'] == 'running', 'WEB_NOT_RUNNING'
    assert gateway['State']['Status'] == 'running', 'GATEWAY_NOT_RUNNING'

    # Step 1: Baseline database state (221 tables)
    print("1. Capturing Main PostgreSQL database state...", flush=True)
    state = database_state('qldapm-openproject-db-1')
    print(f"   Captured {len(state)} tables in PostgreSQL.", flush=True)
    (BACKUP_DIR / 'database-state.json').write_text(json.dumps(state, indent=2))

    # Step 2: pg_dump custom format (-Fc)
    dump_path = BACKUP_DIR / 'main-database.dump'
    print(f"2. Exporting binary PostgreSQL dump to {dump_path.name}...", flush=True)
    with dump_path.open('wb') as stream:
        result = subprocess.run(
            ['docker', 'exec', 'qldapm-openproject-db-1', 'pg_dump', '-U', 'postgres', '-Fc', 'openproject'],
            stdout=stream, stderr=subprocess.PIPE, timeout=180
        )
        assert result.returncode == 0, f"DUMP_FAILED: {result.stderr.decode()}"
    print(f"   PostgreSQL dump completed. Size: {dump_path.stat().st_size:,} bytes.", flush=True)

    # Step 3: SQLite Online Backup API from gateway
    sqlite_path = BACKUP_DIR / 'gateway.sqlite'
    print("3. Performing WAL-safe online backup of AI Gateway SQLite...", flush=True)
    code = r'''
import sqlite3, tempfile, os, sys
s = sqlite3.connect('file:/state/gateway.sqlite?mode=ro', uri=True)
busy = s.execute("SELECT count(*) FROM ai_runs WHERE state IN ('running','queued')").fetchone()[0]
busy += s.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running','failed_or_unknown')").fetchone()[0]
assert busy == 0, f'ACTIVE_OR_UNKNOWN_MAIN_WORK: busy={busy}'
with tempfile.TemporaryDirectory() as t:
    p = os.path.join(t, 'backup.sqlite')
    d = sqlite3.connect(p)
    s.backup(d)
    d.close()
    s.close()
    d = sqlite3.connect('file:' + p + '?immutable=1', uri=True)
    assert d.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    d.close()
    sys.stdout.buffer.write(open(p, 'rb').read())
'''
    sqlite_bytes = command(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], code.encode())
    sqlite_path.write_bytes(sqlite_bytes)
    print(f"   SQLite backup completed. Size: {sqlite_path.stat().st_size:,} bytes.", flush=True)

    # Step 4: Snapshot Project 5 Work Packages and Relations
    print("4. Snapshotting Project 5 Work Packages and Relations...", flush=True)
    wp_sql = "SELECT json_agg(t) FROM (SELECT id, subject, type_id, parent_id, assigned_to_id, status_id, start_date, due_date, schedule_manually, ignore_non_working_days, version_id, lock_version FROM work_packages WHERE project_id = 5 ORDER BY id) t;"
    rel_sql = "SELECT json_agg(t) FROM (SELECT id, from_id, to_id, relation_type, lag, description FROM relations WHERE from_id IN (SELECT id FROM work_packages WHERE project_id = 5) OR to_id IN (SELECT id FROM work_packages WHERE project_id = 5) ORDER BY id) t;"
    sprint_sql = "SELECT json_agg(t) FROM (SELECT id, name, start_date, end_date, project_id FROM sprints WHERE project_id = 5 ORDER BY id) t;"
    version_sql = "SELECT json_agg(t) FROM (SELECT id, name, effective_date, status, sharing, project_id FROM versions WHERE project_id = 5 ORDER BY id) t;"

    def psql_query(sql):
        out = command(['docker', 'exec', '-i', 'qldapm-openproject-db-1', 'psql', '-XqAt', '-U', 'postgres', '-d', 'openproject'], sql.encode())
        return json.loads(out.decode().strip() or '[]')

    wps = psql_query(wp_sql)
    rels = psql_query(rel_sql)
    sprints = psql_query(sprint_sql)
    versions = psql_query(version_sql)

    project5_snapshot = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'project_id': 5,
        'work_packages_count': len(wps),
        'relations_count': len(rels),
        'sprints_count': len(sprints),
        'versions_count': len(versions),
        'work_packages': wps,
        'relations': rels,
        'sprints': sprints,
        'versions': versions
    }
    (BACKUP_DIR / 'project5-baseline-snapshot.json').write_text(json.dumps(project5_snapshot, indent=2))
    print(f"   Project 5 snapshot: {len(wps)} WPs, {len(rels)} relations, {len(sprints)} sprints, {len(versions)} versions.", flush=True)

    # Step 5: Test restoration into clone DB
    print("5. Testing restoration into clone DB (qldapm-rd-db-20261021)...", flush=True)
    test_db = f"verify_restore_{int(time.time())}"
    command(['docker', 'exec', 'qldapm-rd-db-20261021', 'createdb', '-U', 'postgres', test_db])
    try:
        with dump_path.open('rb') as stream:
            res = subprocess.run(
                ['docker', 'exec', '-i', 'qldapm-rd-db-20261021', 'pg_restore', '-U', 'postgres', '--no-owner', '--exit-on-error', '-d', test_db],
                stdin=stream, capture_output=True, timeout=180
            )
            assert res.returncode == 0, f"RESTORE_FAILED: {res.stderr.decode()}"
        print(f"   Restored dump into temporary test database '{test_db}'.", flush=True)

        # Compare table states
        restored_state = read_database_state(
            lambda s: command(['docker', 'exec', '-i', 'qldapm-rd-db-20261021', 'psql', '-XqAt', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', test_db], s.encode())
        )
        assert restored_state == state, "FINGERPRINT_MISMATCH_BETWEEN_ORIGINAL_AND_RESTORED"
        print(f"   Restored state matches original Main DB 100% ({len(restored_state)} tables verified).", flush=True)
    finally:
        # Drop temporary verify db
        command(['docker', 'exec', 'qldapm-rd-db-20261021', 'dropdb', '-U', 'postgres', test_db])
        print(f"   Cleaned up temporary test database '{test_db}'.", flush=True)

    # Step 6: Verify SQLite backup cold integrity
    import sqlite3
    con = sqlite3.connect(f"file:{sqlite_path}?immutable=1", uri=True)
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    assert integrity == 'ok', 'SQLITE_INTEGRITY_CHECK_FAILED'
    print("   SQLite cold integrity check: PASS.", flush=True)

    # Step 7: Generate file manifest and receipt
    print("6. Generating backup manifest and receipt...", flush=True)
    hashes = {}
    for p in BACKUP_DIR.rglob('*'):
        if p.is_file():
            hashes[p.relative_to(BACKUP_DIR).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()

    receipt = {
        'at': datetime.now(timezone.utc).isoformat(),
        'target': 'main',
        'project_id': 5,
        'core_image': web['Image'],
        'gateway_image': gateway['Image'],
        'pg_tables': len(state),
        'work_packages_count': len(wps),
        'relations_count': len(rels),
        'online_backup': True,
        'restore_verified': True,
        'sqlite_integrity': 'PASS',
        'hashes': hashes
    }
    (BACKUP_DIR / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    print("=== MAIN PRE-DEPLOYMENT BACKUP & RESTORE VERIFICATION PASSED ===", flush=True)
    print(json.dumps({k: receipt[k] for k in ('target', 'pg_tables', 'work_packages_count', 'restore_verified', 'sqlite_integrity')}, indent=2))

if __name__ == '__main__':
    main()
