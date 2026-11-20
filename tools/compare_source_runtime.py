import hashlib
import json
from pathlib import Path
import subprocess

def get_local_sha256(path):
    p = Path(path)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

def get_container_file_sha256(container, container_path):
    cmd = ["docker", "exec", container, "sha256sum", container_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        return r.stdout.strip().split()[0]
    return f"ERROR: {r.stderr.strip()}"

files_gateway = [
    ("openproject/ai/gateway/engineering.py", "/app/gateway/engineering.py"),
    ("openproject/ai/gateway/engineering_operator.py", "/app/gateway/engineering_operator.py"),
    ("openproject/ai/gateway/store.py", "/app/gateway/store.py"),
    ("openproject/ai/gateway/service.py", "/app/gateway/service.py"),
    ("openproject/ai/gateway/permissions.py", "/app/gateway/permissions.py"),
    ("openproject/ai/gateway/catalog.py", "/app/gateway/catalog.py"),
    ("openproject/ai/gateway/engineering_units.py", "/app/gateway/engineering_units.py"),
    ("openproject/ai/gateway/engineering_lifecycle.py", "/app/gateway/engineering_lifecycle.py"),
    ("openproject/ai/gateway/engineering_state_sync.py", "/app/gateway/engineering_state_sync.py"),
    ("openproject/ai/gateway/engineering_github_sync.py", "/app/gateway/engineering_github_sync.py"),
    ("openproject/ai/gateway/engineering_auto.py", "/app/gateway/engineering_auto.py"),
    ("openproject/ai/gateway/engineering_reporting.py", "/app/gateway/engineering_reporting.py"),
]

files_core = [
    ("openproject/ai/core/overlay/app/models/qldapm/rbac.rb", "/app/app/models/qldapm/rbac.rb"),
    ("openproject/ai/core/overlay/lib/api/v3/qldapm/gates_api.rb", "/app/lib/api/v3/qldapm/gates_api.rb"),
    ("openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb", "/app/app/controllers/qldapm_ai_controller.rb"),
    ("openproject/ai/core/overlay/app/views/qldapm_ai/engineering.html.erb", "/app/app/views/qldapm_ai/engineering.html.erb"),
]

print("=== GATEWAY CONTAINER (qldapm-ai-gateway-1) FILE HASH COMPARISON ===")
for local_p, cont_p in files_gateway:
    l_hash = get_local_sha256(local_p)
    c_hash = get_container_file_sha256("qldapm-ai-gateway-1", cont_p)
    match = (l_hash == c_hash)
    print(f"File: {local_p}")
    print(f"  Local SHA256:     {l_hash}")
    print(f"  Container SHA256: {c_hash}")
    print(f"  Match:            {match}")

print("\n=== CORE CONTAINER (qldapm-openproject-web-1) FILE HASH COMPARISON ===")
for local_p, cont_p in files_core:
    l_hash = get_local_sha256(local_p)
    c_hash = get_container_file_sha256("qldapm-openproject-web-1", cont_p)
    match = (l_hash == c_hash)
    print(f"File: {local_p}")
    print(f"  Local SHA256:     {l_hash}")
    print(f"  Container SHA256: {c_hash}")
    print(f"  Match:            {match}")
