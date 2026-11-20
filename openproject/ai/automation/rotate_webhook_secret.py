"""ROTATE WEBHOOK SECRET
Generates a fresh cryptographically secure random token, updates webhook_secret.json,
encrypts into n8n credentials_entity (2w9dSdmYbywZDuMB) using n8n's native encryption key,
restarts n8n container, and verifies old tokens are rejected while new token works.
"""

import os
import sys
import json
import secrets
import subprocess
import time
import urllib.request
import urllib.error

WEBHOOK_JSON_PATH = r"C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\webhook_secret.json"

# 1. Read current token
with open(WEBHOOK_JSON_PATH, "r", encoding="utf-8") as f:
    old_data = json.load(f)
    old_token = old_data.get("webhook_token") or old_data.get("secret")

# 2. Generate new token
new_token = "qldapm_wh_" + secrets.token_urlsafe(32)

print(f"Old token: {old_token[:6]}...{old_token[-6:]}")
print(f"New token generated: {new_token[:6]}...{new_token[-6:]}")

# 3. Encrypt and update inside n8n container
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
    name: 'X-QLDAPM-Webhook-Token',
    value: '{new_token}'
}});

const encryptedData = encrypt(credPayload);

const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run("UPDATE credentials_entity SET data = ?, updatedAt = datetime('now') WHERE id = '2w9dSdmYbywZDuMB'", [encryptedData], function(err) {{
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

print("[OK] n8n credentials_entity 2w9dSdmYbywZDuMB updated with encrypted new token.")

# 4. Update webhook_secret.json atomically
temp_path = WEBHOOK_JSON_PATH + ".tmp"
with open(temp_path, "w", encoding="utf-8") as f:
    json.dump({"webhook_token": new_token}, f, indent=2)
os.replace(temp_path, WEBHOOK_JSON_PATH)
print("[OK] webhook_secret.json updated.")

# 5. Restart n8n container cleanly so credential cache reloads
print("Restarting qldapm-n8n-main container...")
subprocess.run(["docker", "restart", "qldapm-n8n-main"], check=True, capture_output=True)

# Wait for n8n to be ready
print("Waiting for n8n to become ready...")
for _ in range(30):
    try:
        with urllib.request.urlopen("http://127.0.0.1:5679/healthz", timeout=2) as r:
            if r.status == 200:
                print("n8n is ready!")
                break
    except Exception:
        time.sleep(1)

# 6. Verify security boundary
print("\n--- Verifying Webhook Token Rotation ---")

# Test 6a: Old token lxNOtbFJ... must be rejected (403)
req_old = urllib.request.Request("http://127.0.0.1:5679/webhook/qldapm-monitoring", data=b"{}", headers={
    "Content-Type": "application/json",
    "X-QLDAPM-Webhook-Token": old_token
})
try:
    with urllib.request.urlopen(req_old, timeout=5) as resp:
        print(f"[ERROR] Old token was unexpectedly accepted: HTTP {resp.status}")
        sys.exit(1)
except urllib.error.HTTPError as e:
    print(f"[PASS] Old token correctly rejected: HTTP {e.code}")
    assert e.code == 403

# Test 6b: Leaked token qldapm-prod-webhook-secret-v1-20261022 must be rejected (403)
req_leak = urllib.request.Request("http://127.0.0.1:5679/webhook/qldapm-monitoring", data=b"{}", headers={
    "Content-Type": "application/json",
    "X-QLDAPM-Webhook-Token": "qldapm-prod-webhook-secret-v1-20261022"
})
try:
    with urllib.request.urlopen(req_leak, timeout=5) as resp:
        print(f"[ERROR] Leaked token was unexpectedly accepted: HTTP {resp.status}")
        sys.exit(1)
except urllib.error.HTTPError as e:
    print(f"[PASS] Leaked historical token correctly rejected: HTTP {e.code}")
    assert e.code == 403

# Test 6c: New token must be accepted (200)
req_new = urllib.request.Request("http://127.0.0.1:5679/webhook/qldapm-monitoring", data=b"{}", headers={
    "Content-Type": "application/json",
    "X-QLDAPM-Webhook-Token": new_token
})
try:
    with urllib.request.urlopen(req_new, timeout=5) as resp:
        print(f"[PASS] New token accepted: HTTP {resp.status}")
        assert resp.status == 200
except Exception as e:
    print(f"[ERROR] New token failed: {e}")
    sys.exit(1)

print("\nROTATION COMPLETED AND VERIFIED SUCCESSFULLY!")
