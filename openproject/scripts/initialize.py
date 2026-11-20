"""Generate private runtime configuration without printing credentials."""
import argparse
import csv
import hashlib
import json
import secrets
import shutil
import subprocess
from pathlib import Path

TEAM = [
    ("hiepk40c@gmail.com", "ba-pm", "PM"),
    ("2101minhkhai@gmail.com", "pm", "BA"),
    ("nguyenduc6325@gmail.com", "be", "BE"),
    ("ttheduy1401@gmail.com", "fe", "FE"),
    ("Duyhungls2005@gmail.com", "qa", "QA"),
]
IMAGES = {
    "OP_IMAGE": "openproject/openproject:17.9.1-slim",
    "POSTGRES_IMAGE": "postgres:17",
    "CACHE_IMAGE": "memcached:1.6-alpine",
    "CADDY_IMAGE": "caddy:2-alpine",
    "HOCUSPOCUS_IMAGE": "openproject/hocuspocus:17.9.1",
    "CLOUDFLARED_IMAGE": "cloudflare/cloudflared:2026.10.0",
}


def initialize(runtime, source):
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "gate").mkdir(exist_ok=True)
    if (runtime / ".env").exists():
        if not (runtime / "bootstrap.json").exists():
            path = runtime / "accounts.json"
            accounts = json.loads(path.read_text(encoding="utf-8"))
            for account in [accounts["admin"], *accounts["users"]]:
                account["password"] = "Aa1!" + secrets.token_urlsafe(32)
            path.write_text(json.dumps(accounts, indent=2), encoding="utf-8")
        print("Existing private configuration retained.")
        return
    rows = list(csv.DictReader(source.open(encoding="utf-8-sig", newline="")))
    assert len(rows) == 329 and len({r["Source ID"] for r in rows}) == 329
    config = {}
    for key, image in IMAGES.items():
        digests = json.loads(subprocess.check_output(
            ["docker", "image", "inspect", image, "--format", "{{json .RepoDigests}}"], text=True))
        if not digests:
            raise RuntimeError(f"No image digest: {image}")
        config[key] = digests[0]
    config.update(POSTGRES_PASSWORD=secrets.token_hex(24), SECRET_KEY_BASE=secrets.token_hex(64),
                  COLLABORATIVE_SECRET=secrets.token_hex(32), RUNTIME_DIR=runtime.as_posix(),
                  ALLOWED_MAIL=",".join(t[0].lower() for t in TEAM),
                  OP_HOST="127.0.0.1:18088", OP_HTTPS="false", PROXY_SCHEME="http",
                  COLLABORATIVE_URL="ws://127.0.0.1:18088/hocuspocus")
    users = [dict(email=email, login=login, role=role, password="Aa1!" + secrets.token_urlsafe(32))
             for email, login, role in TEAM]
    credentials = {"admin": {"login": "op-owner", "password": "Aa1!" + secrets.token_urlsafe(32)}, "users": users}
    (runtime / "accounts.json").write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copyfile(source, runtime / "wbs-snapshot.csv")
    manifest = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "rows": 329, "images": config.copy()}
    for key in ("POSTGRES_PASSWORD", "SECRET_KEY_BASE", "COLLABORATIVE_SECRET"):
        manifest["images"].pop(key)
    (runtime / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (runtime / ".env").write_text("".join(f"{k}={v}\n" for k, v in config.items()), encoding="utf-8")
    (runtime / "gate" / "maintenance").touch()
    print("Private runtime created; 329-row source snapshot frozen; image digests pinned.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    initialize(args.runtime, args.source)
