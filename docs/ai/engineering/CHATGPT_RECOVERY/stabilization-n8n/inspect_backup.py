"""Inspect the DPAPI backup in memory; never write decrypted data or secrets."""
import base64
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tarfile

private = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/post30218-n8n-redaction'


def unprotect(path):
    ps = "Add-Type -AssemblyName System.Security; $b=[IO.File]::ReadAllBytes($env:QLDAPM_DPAPI_INPUT); $d=[Security.Cryptography.ProtectedData]::Unprotect($b,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser); [Console]::Write([Convert]::ToBase64String($d))"
    env = dict(os.environ, QLDAPM_DPAPI_INPUT=str(path))
    p = subprocess.run(['powershell', '-NoProfile', '-Command', ps], env=env, capture_output=True, check=True)
    return base64.b64decode(p.stdout, validate=True)


if __name__ == '__main__':
    archive = unprotect(private / 'n8n-cold-volume.tar.dpapi')
    env = unprotect(private / 'preserved.env.dpapi').decode()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:*') as tf:
        files = {m.name.removeprefix('./'): m for m in tf if m.isfile()}
        dbfile = next(m for name, m in files.items() if name == 'database.sqlite')
        configfile = next(m for name, m in files.items() if name == 'config')
        wal = any(name.endswith('-wal') and member.size for name, member in files.items())
        if wal:
            raise RuntimeError('Non-empty WAL: an in-memory database-only check would be incomplete')
        db_bytes = bytearray(tf.extractfile(dbfile).read())
        db_bytes[18:20] = b'\x01\x01'  # In-memory copy only: allow deserialize without filesystem WAL.
        db = sqlite3.connect(':memory:')
        db.deserialize(bytes(db_bytes))
        config = json.load(tf.extractfile(configfile))
        vars = dict(line.split('=', 1) for line in env.splitlines() if '=' in line)
        report = {'dpapi_decrypt': True, 'db_integrity': db.execute('pragma integrity_check').fetchone()[0],
                  'workflow_count': db.execute('select count(*) from workflow_entity').fetchone()[0],
                  'credential_count': db.execute('select count(*) from credentials_entity').fetchone()[0],
                  'key_present': bool(vars.get('N8N_ENCRYPTION_KEY')),
                  'config_key_matches_env': config.get('encryptionKey') == vars.get('N8N_ENCRYPTION_KEY'),
                  'archive_wal_present': any(name.endswith('-wal') for name in files),
                  'full_restore': 'NOT_RUN', 'credential_decrypt': 'NOT_RUN'}
        print(json.dumps(report))
