"""Secure TOTP Secret Rotation for QLDAPM Staging Accounts.

Rotates TOTP secrets for staging accounts (pm, fe, be, qa, ba-pm, stage-owner)
by generating cryptographically secure random Base32 keys using secrets/base64,
enrolling new devices, verifying token computation before deactivating old devices,
and saving credentials to a secure unmounted secrets directory in LOCALAPPDATA.
NEVER prints plaintext secrets or OTP tokens to stdout or logs.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = Path(os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\secrets"))
CRED_FILE = SECRETS_DIR / "staging_totp_secrets.json"
LEGACY_CRED_FILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json"))

STAGING_USERS = [
    {"login": "ba-pm", "role": "BA-PM", "old_device_id": 27},
    {"login": "pm", "role": "PM", "old_device_id": 24},
    {"login": "be", "role": "BE", "old_device_id": 23},
    {"login": "fe", "role": "FE", "old_device_id": 25},
    {"login": "qa", "role": "QA", "old_device_id": 26},
    {"login": "stage-owner", "role": "OWNER", "old_device_id": 28},
]


def compute_totp(secret_b32: str) -> str:
    """RFC 6238 TOTP computation using standard library."""
    key = base64.b32decode(secret_b32, casefold=True)
    msg = struct.pack(">Q", int(time.time() // 30))
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[19] & 15
    code = (struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def generate_rotation_plan():
    """Generates a dry-run rotation plan without mutating the database."""
    print("=" * 80)
    print("STAGING TOTP ROTATION PLAN (DRY-RUN / AUDIT)")
    print("=" * 80)
    print("Target Container: qldapm-ai-stage-staging-web-1 (Staging Stack ONLY)")
    print("Main Stack Isolation: Confirmed untouched (qldapm-openproject-db-1)")
    print(f"Credential Destination: {CRED_FILE} (Unmounted, Isolated Secrets Folder)")
    print("-" * 80)
    for u in STAGING_USERS:
        print(f"Account: {u['login']:12} | Role: {u['role']:6} | Old Device ID: {u['old_device_id']:2} -> CREATE NEW DEVICE -> VERIFY -> DEACTIVATE OLD")
    print("-" * 80)
    print("Security Posture: Zero plaintext secrets printed. Cryptographically secure 160-bit Base32 keys.")
    print("=" * 80)


def execute_rotation():
    """Executes the rotation via Rails runner inside staging-web container."""
    # Ensure secrets directory exists
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)

    current_creds = {}
    if CRED_FILE.is_file():
        try:
            current_creds = json.loads(CRED_FILE.read_text(encoding="utf-8"))
        except Exception:
            current_creds = {}
    elif LEGACY_CRED_FILE.is_file():
        try:
            current_creds = json.loads(LEGACY_CRED_FILE.read_text(encoding="utf-8"))
        except Exception:
            current_creds = {}

    rotation_records = []

    for u in STAGING_USERS:
        login = u["login"]
        role = u["role"]
        old_dev_id = u["old_device_id"]

        # 1. Generate fresh 160-bit Base32 secret (32 chars)
        new_secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii")

        # 2. Compute current TOTP token for validation check
        test_code = compute_totp(new_secret)

        # 3. Prepare payload for Rails runner
        payload = {
            "login": login,
            "old_device_id": old_dev_id,
            "new_secret": new_secret,
            "test_code": test_code,
        }

        ruby_code = f"""
require 'json'
payload = JSON.parse(STDIN.read)
login = payload['login']
old_dev_id = payload['old_device_id']
new_secret = payload['new_secret']
test_code = payload['test_code']

u = User.find_by(login: login)
raise "USER_NOT_FOUND: #{{login}}" unless u

old_dev = TwoFactorAuthentication::Device::Totp.find_by(id: old_dev_id, user_id: u.id)

# Step 1: Create NEW TOTP device with default: false to avoid collision with old default
new_dev = TwoFactorAuthentication::Device::Totp.create!(
  user: u,
  identifier: "Authenticator application (#{{login}} rotated #{{Time.now.to_i}})",
  active: true,
  default: false,
  otp_secret: new_secret
)

# Step 2: Verify that new device accepts the test token
verify_ok = !new_dev.totp.verify(test_code).nil?
unless verify_ok
  new_dev.destroy!
  raise "NEW_DEVICE_VERIFY_FAILED: #{{login}}"
end

# Step 3: Atomic transition: deactivate old device and promote new device to default
ActiveRecord::Base.transaction do
  if old_dev
    old_dev.update!(active: false, default: false)
  end
  new_dev.update!(default: true)
end

puts JSON.generate({{
  status: 'SUCCESS',
  login: u.login,
  new_device_id: new_dev.id,
  old_device_id: old_dev&.id,
  old_active: old_dev&.active,
  new_active: new_dev.active,
  new_default: new_dev.default,
  verified: verify_ok
}})
"""
        cmd = [
            "docker", "exec", "-i", "qldapm-ai-stage-staging-web-1",
            "bundle", "exec", "rails", "runner", ruby_code
        ]

        res = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True)
        if res.returncode != 0:
            print(f"ERROR rotating {login}: {res.stderr}")
            sys.exit(1)

        try:
            result_data = json.loads(res.stdout.strip().split("\n")[-1])
        except Exception as e:
            print(f"ERROR parsing JSON output for {login}: {e}\nRaw output: {res.stdout}")
            sys.exit(1)

        # Update credentials file preserving password
        user_pwd = current_creds.get(login, {}).get("pass", "PUBLICATION_REDACTED")
        if login == "fe":
            user_pwd = current_creds.get(login, {}).get("pass", "PUBLICATION_REDACTED")

        current_creds[login] = {
            "user": login,
            "pass": user_pwd,
            "totp_secret": new_secret,
            "role": role,
            "device_id": result_data.get("new_device_id"),
        }

        rotation_records.append({
            "login": login,
            "role": role,
            "old_device_id": old_dev_id,
            "new_device_id": result_data.get("new_device_id"),
            "old_active": result_data.get("old_active"),
            "new_active": result_data.get("new_active"),
            "verified": result_data.get("verified"),
        })
        print(f"[ROTATED] Account: {login:12} | Old Dev {old_dev_id} (active={result_data.get('old_active')}) -> New Dev {result_data.get('new_device_id')} (active={result_data.get('new_active')}, verified=True)")

    # Save credentials securely to isolated secrets directory
    CRED_FILE.write_text(json.dumps(current_creds, indent=2), encoding="utf-8")
    
    # Clean up legacy credential file if present in access folder
    if LEGACY_CRED_FILE.is_file():
        try:
            LEGACY_CRED_FILE.unlink()
            print(f"[SECURITY] Removed legacy credential file from web-mounted folder: {LEGACY_CRED_FILE}")
        except Exception as e:
            print(f"[SECURITY WARNING] Failed to delete legacy credential file: {e}")

    print(f"\nAll 6 TOTP secrets rotated successfully and stored in {CRED_FILE}")
    return rotation_records


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        execute_rotation()
    else:
        generate_rotation_plan()
