"""Restore only the private backup into labelled disposable resources; never MAIN."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'openproject/ai'))
from automation.main_native_clone import main_native_clone

RUN = Path(__file__).parent
BACKUP = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/chatgpt-recovery-20261101T043043Z'
PRIVATE = BACKUP.parent / ('phase2-restore-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
PRIVATE.mkdir(exist_ok=False)
result = {'backup': str(BACKUP), 'restore_copy': str(PRIVATE), 'sqlite': {}, 'status': 'RUNNING'}


def counts(connection):
    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    return {t: connection.execute('SELECT count(*) FROM "' + t.replace('"', '""') + '"').fetchone()[0] for t in tables}


for name in ['gateway.sqlite', 'knowledge.sqlite']:
    target = PRIVATE / name
    shutil.copy2(BACKUP / name, target)
    with sqlite3.connect((BACKUP / name).as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(target) as restored:
        integrity = restored.execute('PRAGMA integrity_check').fetchone()[0]
        expected, actual = counts(source), counts(restored)
        schema = lambda c: c.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
        assert integrity == 'ok' and expected == actual and schema(source) == schema(restored)
        result['sqlite'][name] = {'integrity': integrity, 'schema_matches': True, 'row_counts': actual}

try:
    image = 'sha256:9b90e20fcb044c89b3260fc13f33c386923a6192a498f4655bd1272a44bbebb6'
    with main_native_clone(PRIVATE / 'native', candidate_web_image=image, source_dump_path=BACKUP / 'postgres.dump') as clone:
        def sql(query):
            return subprocess.check_output(['docker', 'exec', clone['database'], 'psql', '-U', 'postgres', '-d', 'openproject', '-XAtc', query], timeout=45).decode().strip()
        projects = sql('SELECT project_id,count(*),max(lock_version) FROM work_packages WHERE project_id IN (5,6) GROUP BY project_id ORDER BY project_id;')
        assert projects == '5|341|4\n6|7|9', projects
        parent = sql('SELECT id,project_id,status_id,lock_version FROM work_packages WHERE id=379;')
        assert parent == '379|6|7|4', parent
        count_query = sql("SELECT string_agg(format('SELECT %L,count(*) FROM %I.%I',tablename,schemaname,tablename),' UNION ALL ') FROM pg_tables WHERE schemaname='public';")
        rows = sql(count_query)
        table_counts = {name: int(value) for name, value in (line.rsplit('|', 1) for line in rows.splitlines())}
        assert len(table_counts) >= 200 and table_counts['work_packages'] >= 348
        result['postgres'] = {'projects': projects, 'parent': parent, 'row_counts': table_counts,
                              'schema_tables': len(table_counts), 'core_health': 'PASS',
                              'isolated_network': clone['network'], 'source_dump_sha256': clone['source_dump_sha256']}
    result['status'] = 'BACKUP_RESTORE_VERIFIED'
finally:
    (RUN / 'restore-drill-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'sqlite_databases': len(result['sqlite']), 'postgres_tables': result.get('postgres', {}).get('schema_tables')}, indent=2))
