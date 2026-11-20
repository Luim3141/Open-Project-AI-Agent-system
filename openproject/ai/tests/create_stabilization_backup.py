import os
from pathlib import Path
import shutil
import subprocess

backup_dir = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/operator/pre-stabilization-20261020-0555"
backup_dir.mkdir(parents=True, exist_ok=True)
print(f"Creating backup directory: {backup_dir}")

# 1. PostgreSQL DB dump
sql_file = backup_dir / "staging_db_before_stabilization.sql"
print("Dumping staging DB to", sql_file)
with open(sql_file, "w", encoding="utf-8") as f:
    res = subprocess.run(
        ["docker", "exec", "-i", "qldapm-ai-stage-db-1", "pg_dump", "-U", "postgres", "-d", "openproject"],
        stdout=f, stderr=subprocess.PIPE, text=True, check=True
    )
print("DB Dump created successfully. Size:", sql_file.stat().st_size, "bytes")

# 2. Gateway sqlite copy
gw_state = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/stage-ai/gateway.sqlite"
if gw_state.exists():
    shutil.copy2(gw_state, backup_dir / "gateway_before_stabilization.sqlite")
    print("Gateway SQLite snapshot saved.")
else:
    # Read from container directly
    res = subprocess.run(
        ["docker", "exec", "qldapm-ai-stage-staging-gateway-1", "cat", "/state/gateway.sqlite"],
        capture_output=True, check=True
    )
    (backup_dir / "gateway_before_stabilization.sqlite").write_bytes(res.stdout)
    print("Gateway SQLite snapshot saved from container.")

print("Pre-stabilization backup completed 100% successfully.")
