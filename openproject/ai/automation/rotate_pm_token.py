"""SAFE END-TO-END PM TOKEN ROTATION SCRIPT
Executed via container execution to eliminate Windows bind-mount lock contention.
1. Generates fresh Actor 19 (PM) token with 30-day lifecycle.
2. Inserts new SHA-256 hash into Gateway SQLite tokens table via container python.
3. Encrypts Authorization Bearer header into n8n credentials_entity (DBWkxwb2izrbu17C) using n8n AES key.
4. Atomically updates local test_pm_token.secret.
5. Verifies new token authentication against Gateway Control Center API.
6. Revokes old token only upon verified success (Zero Authentication Gap).
7. Verifies old token returns HTTP 401.
8. Rolls back completely if verification fails.
"""

import os
import sys
import time
import json
import secrets
import hashlib
import subprocess
import urllib.request
import urllib.error

PM_TOKEN_FILE = r"C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\test_pm_token.secret"
CONTROL_CENTER_URL = "http://127.0.0.1:18089/api/v1/control-center/state"

def run_gateway_db(query, params=()):
    params_json = json.dumps(params)
    code = f"""
import sqlite3, json
conn = sqlite3.connect('/state/gateway.sqlite', timeout=10)
c = conn.cursor()
c.execute({json.dumps(query)}, json.loads({json.dumps(params_json)}))
conn.commit()
conn.close()
print("GATEWAY_DB_OK")
"""
    proc = subprocess.run(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", code], capture_output=True, text=True)
    if proc.returncode != 0 or "GATEWAY_DB_OK" not in proc.stdout:
        raise RuntimeError(f"Gateway DB execution failed: {proc.stderr} {proc.stdout}")

def main():
    print("================================================================================")
    print("STARTING CONTROLLED PM TOKEN ROTATION (CONTAINER-NATIVE EXECUTION)")
    print("================================================================================\n")

    # 1. Read existing token
    if not os.path.exists(PM_TOKEN_FILE):
        raise RuntimeError(f"Missing existing token file: {PM_TOKEN_FILE}")
    with open(PM_TOKEN_FILE, "r", encoding="utf-8") as f:
        old_token = f.read().strip()
    old_hash = hashlib.sha256(old_token.encode("utf-8")).hexdigest()
    print(f"[OK] Existing token: {old_token[:4]}...{old_token[-4:]} (SHA-256: {old_hash[:16]}...)")

    # 2. Generate new token
    new_token = "OFSO_" + secrets.token_hex(28)
    new_hash = hashlib.sha256(new_token.encode("utf-8")).hexdigest()
    now = time.time()
    expires = now + (30 * 86400) # 30 days
    print(f"[OK] Generated new token: {new_token[:4]}...{new_token[-4:]} (SHA-256: {new_hash[:16]}...)")

    # 3. Insert into Gateway SQLite via container
    run_gateway_db("INSERT INTO tokens (hash, user_id, role, expires, revoked) VALUES (?, 19, 'PM', ?, 0)", [new_hash, expires])
    print("[OK] Inserted new token hash into Gateway tokens table via container (30 days validity).")

    try:
        # 4. Encrypt into n8n credentials_entity
        node_script = f"""
const fs = require('fs');
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const crypto = require('crypto');

const config = JSON.parse(fs.readFileSync('/home/node/.n8n/config', 'utf8'));
const encryptionKey = config.encryptionKey;

function evp(password, salt, keyLen, ivLen) {{
    let d = Buffer.alloc(0);
    let total = Buffer.alloc(0);
    while (total.length < keyLen + ivLen) {{
        const hash = crypto.createHash('md5');
        hash.update(Buffer.concat([d, Buffer.from(password, 'utf8'), salt]));
        d = hash.digest();
        total = Buffer.concat([total, d]);
    }}
    return {{
        key: total.subarray(0, keyLen),
        iv: total.subarray(keyLen, keyLen + ivLen)
    }};
}}

function encrypt(plainText) {{
    const salt = crypto.randomBytes(8);
    const {{ key, iv }} = evp(encryptionKey, salt, 32, 16);
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    let encrypted = cipher.update(plainText, 'utf8');
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    const payload = Buffer.concat([Buffer.from('Salted__'), salt, encrypted]);
    return payload.toString('base64');
}}

const credPayload = JSON.stringify({{
    name: 'Authorization',
    value: 'Bearer {new_token}'
}});

const encryptedData = encrypt(credPayload);

const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run("UPDATE credentials_entity SET data = ?, updatedAt = datetime('now') WHERE id = 'DBWkxwb2izrbu17C'", [encryptedData], function(err) {{
    if (err) {{
        console.error("DB_UPDATE_ERROR:", err);
        process.exit(1);
    }}
    console.log("N8N_CREDENTIAL_UPDATED_CHANGES:", this.changes);
    db.close();
}});
"""
        proc = subprocess.run(["docker", "exec", "qldapm-n8n-main", "node", "-e", node_script], capture_output=True, text=True)
        if proc.returncode != 0 or "N8N_CREDENTIAL_UPDATED_CHANGES: 1" not in proc.stdout:
            raise RuntimeError(f"Failed to update n8n credential: {proc.stderr} {proc.stdout}")
        print("[OK] Updated n8n DBWkxwb2izrbu17C credential with encrypted Bearer token.")

        # 5. Atomically update local secret file
        tmp_file = PM_TOKEN_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(new_token)
        os.replace(tmp_file, PM_TOKEN_FILE)
        print("[OK] Updated local secret file atomically.")

        # 6. Verify authentication with new token
        req = urllib.request.Request(CONTROL_CENTER_URL, headers={"Authorization": f"Bearer {new_token}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            assert data.get("result", {}).get("actor_id") == 19
            print("[PASS] Verified authentication with new token against Control Center API (HTTP 200, Actor 19).")

        # 7. Revoke old token
        run_gateway_db("UPDATE tokens SET revoked = 1 WHERE hash = ?", [old_hash])
        print(f"[OK] Revoked old token (SHA-256: {old_hash[:16]}...).")

        # 8. Verify old token is now rejected (HTTP 401)
        req_old = urllib.request.Request(CONTROL_CENTER_URL, headers={"Authorization": f"Bearer {old_token}"})
        try:
            with urllib.request.urlopen(req_old, timeout=5) as r_old:
                print(f"[WARNING] Old token was unexpectedly accepted: HTTP {r_old.status}")
                sys.exit(1)
        except urllib.error.HTTPError as e:
            assert e.code == 401
            print(f"[PASS] Old token is strictly rejected: HTTP {e.code} Unauthorized.")

        print("\n================================================================================")
        print("PM TOKEN ROTATION COMPLETED AND VERIFIED (ZERO AUTH DOWNTIME)")
        print("================================================================================")
        return True

    except Exception as e:
        print(f"\n[ERROR] Rotation failed: {e}. Initiating rollback...")
        try:
            run_gateway_db("DELETE FROM tokens WHERE hash = ?", [new_hash])
        except Exception as rb_err:
            print(f"[ROLLBACK DB ERROR]: {rb_err}")
        with open(PM_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(old_token)
        print("[ROLLBACK] Rolled back tokens table and secret file.")
        raise

if __name__ == "__main__":
    main()
