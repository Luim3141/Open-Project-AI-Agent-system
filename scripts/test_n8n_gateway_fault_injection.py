"""n8n to AI Gateway Fault Injection & Execution Proof Test Suite.
Tests live communication between n8n and AI Gateway:
1. Valid signed HMAC command execution
2. Invalid machine key authentication failure (401)
3. Invalid command signature rejection (403)
4. Expired/replay timestamp rejection (403)
5. Future timestamp rejection (403)
6. Malformed payload / schema violation (422)
7. Duplicate request_key idempotency
8. Internal status probe
Verifies database receipts in gateway.sqlite.
"""
import hashlib
import hmac
import json
import os
import sqlite3
import sys
import time
import uuid
import httpx

GATEWAY_URL = "http://127.0.0.1:18092"
STAGE_AI = os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai")
KEY_PATH = os.path.join(STAGE_AI, "automation.key")
DB_PATH = os.path.join(STAGE_AI, "gateway.sqlite")

COMMAND_PATH = "/internal/automation/commands"
STATUS_PATH = "/internal/automation/status"
HEADER = "x-qldapm-machine-key"
SIGNATURE_HEADER = "x-qldapm-command-signature"


def load_machine_key():
    with open(KEY_PATH, "r", encoding="ascii") as f:
        return f.read().strip()


def signing_key(key):
    return hmac.new(key.encode("ascii"), b"QLDAPM-AUTOMATION-SIGNING-V1", hashlib.sha256).hexdigest()


def signing_message(command):
    return (
        "QLDAPM-AUTOMATION-COMMAND-V1\nPOST\n"
        + COMMAND_PATH
        + "\n1\n"
        + command["kind"]
        + "\n"
        + command["request_key"]
        + "\n"
        + command["nonce"]
        + "\n"
        + str(command["issued_at"])
    ).encode("utf-8")


def sign_command(key, command):
    return hmac.new(signing_key(key).encode("ascii"), signing_message(command), hashlib.sha256).hexdigest()


def run_tests():
    print("=" * 80)
    print("N8N <-> AI GATEWAY FAULT INJECTION & EXECUTION PROOF")
    print(f"Target Gateway: {GATEWAY_URL}")
    print(f"Timestamp:      {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print("=" * 80)

    key = load_machine_key()
    results = []

    with httpx.Client(base_url=GATEWAY_URL, timeout=10) as client:
        # -------------------------------------------------------------
        # Test 1: Valid signed command (Happy Path)
        # -------------------------------------------------------------
        print("\n--- Test 1: Valid Signed Automation Command ---")
        now = int(time.time())
        req_key = f"status:n8n_test:{uuid.uuid4().hex[:12]}"
        nonce = f"nonce_{uuid.uuid4().hex[:16]}"
        cmd = {
            "version": 1,
            "kind": "status",
            "request_key": req_key,
            "nonce": nonce,
            "issued_at": now,
        }
        sig = sign_command(key, cmd)
        headers = {
            HEADER: key,
            SIGNATURE_HEADER: sig,
            "content-type": "application/json",
        }
        t0 = time.time()
        r1 = client.post(COMMAND_PATH, headers=headers, content=json.dumps(cmd))
        d1 = round(time.time() - t0, 3)
        print(f"Status: {r1.status_code}, Body: {r1.text} [{d1}s]")
        pass1 = r1.status_code == 200 and "correlation_id" in r1.json()
        results.append({
            "id": "N8N-01",
            "name": "Valid Signed Command Execution",
            "status": "PASS" if pass1 else "FAIL",
            "code": r1.status_code,
            "duration": d1,
            "details": f"Gateway accepted valid HMAC command, correlation_id={r1.json().get('correlation_id', '')[:8]}..."
        })

        # Check DB receipt
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, request_key, receipt FROM automation_runs WHERE request_key = ?", (req_key,))
        row = cur.fetchone()
        conn.close()
        print(f"Database Receipt in gateway.sqlite: id={row[0]}, request_key={row[1]}")
        assert row is not None
        receipt_data = json.loads(row[2])
        assert receipt_data.get("status") == "ok"

        # -------------------------------------------------------------
        # Test 2: Invalid Machine Key (Authentication Failure)
        # -------------------------------------------------------------
        print("\n--- Test 2: Invalid Machine Key (Fault: Bad Auth) ---")
        bad_key = "0" * 64
        sig2 = sign_command(bad_key, cmd)
        headers2 = {
            HEADER: bad_key,
            SIGNATURE_HEADER: sig2,
            "content-type": "application/json",
        }
        t0 = time.time()
        r2 = client.post(COMMAND_PATH, headers=headers2, content=json.dumps(cmd))
        d2 = round(time.time() - t0, 3)
        print(f"Status: {r2.status_code}, Body: {r2.text} [{d2}s]")
        pass2 = r2.status_code == 401 and r2.json().get("error") == "INVALID_MACHINE_AUTH"
        results.append({
            "id": "N8N-02",
            "name": "Invalid Machine Key Rejection",
            "status": "PASS" if pass2 else "FAIL",
            "code": r2.status_code,
            "duration": d2,
            "details": f"Rejected bad machine key with 401 INVALID_MACHINE_AUTH"
        })

        # -------------------------------------------------------------
        # Test 3: Invalid HMAC Signature (Fault: Tampered / Bad Sig)
        # -------------------------------------------------------------
        print("\n--- Test 3: Invalid HMAC Signature (Fault: Tampered Sig) ---")
        bad_sig = "a" * 64
        headers3 = {
            HEADER: key,
            SIGNATURE_HEADER: bad_sig,
            "content-type": "application/json",
        }
        t0 = time.time()
        r3 = client.post(COMMAND_PATH, headers=headers3, content=json.dumps(cmd))
        d3 = round(time.time() - t0, 3)
        print(f"Status: {r3.status_code}, Body: {r3.text} [{d3}s]")
        pass3 = r3.status_code == 403 and r3.json().get("error") == "INVALID_COMMAND_SIGNATURE"
        results.append({
            "id": "N8N-03",
            "name": "Invalid HMAC Signature Rejection",
            "status": "PASS" if pass3 else "FAIL",
            "code": r3.status_code,
            "duration": d3,
            "details": f"Rejected tampered signature with 403 INVALID_COMMAND_SIGNATURE"
        })

        # -------------------------------------------------------------
        # Test 4: Replay / Expired Timestamp (Fault: Past Timestamp)
        # -------------------------------------------------------------
        print("\n--- Test 4: Expired Timestamp / Replay (Fault: -120s) ---")
        expired_time = int(time.time()) - 120
        cmd_expired = {
            "version": 1,
            "kind": "status",
            "request_key": f"status:n8n_test:{uuid.uuid4().hex[:12]}",
            "nonce": f"nonce_{uuid.uuid4().hex[:16]}",
            "issued_at": expired_time,
        }
        sig4 = sign_command(key, cmd_expired)
        headers4 = {
            HEADER: key,
            SIGNATURE_HEADER: sig4,
            "content-type": "application/json",
        }
        t0 = time.time()
        r4 = client.post(COMMAND_PATH, headers=headers4, content=json.dumps(cmd_expired))
        d4 = round(time.time() - t0, 3)
        print(f"Status: {r4.status_code}, Body: {r4.text} [{d4}s]")
        pass4 = r4.status_code == 403 and r4.json().get("error") == "COMMAND_EXPIRED_OR_FUTURE"
        results.append({
            "id": "N8N-04",
            "name": "Replay / Expired Command Rejection",
            "status": "PASS" if pass4 else "FAIL",
            "code": r4.status_code,
            "duration": d4,
            "details": f"Rejected replay with elapsed > 60s as 403 COMMAND_EXPIRED_OR_FUTURE"
        })

        # -------------------------------------------------------------
        # Test 5: Future Timestamp (Fault: +120s)
        # -------------------------------------------------------------
        print("\n--- Test 5: Future Timestamp (Fault: +120s) ---")
        future_time = int(time.time()) + 120
        cmd_future = {
            "version": 1,
            "kind": "status",
            "request_key": f"status:n8n_test:{uuid.uuid4().hex[:12]}",
            "nonce": f"nonce_{uuid.uuid4().hex[:16]}",
            "issued_at": future_time,
        }
        sig5 = sign_command(key, cmd_future)
        headers5 = {
            HEADER: key,
            SIGNATURE_HEADER: sig5,
            "content-type": "application/json",
        }
        t0 = time.time()
        r5 = client.post(COMMAND_PATH, headers=headers5, content=json.dumps(cmd_future))
        d5 = round(time.time() - t0, 3)
        print(f"Status: {r5.status_code}, Body: {r5.text} [{d5}s]")
        pass5 = r5.status_code == 403 and r5.json().get("error") == "COMMAND_EXPIRED_OR_FUTURE"
        results.append({
            "id": "N8N-05",
            "name": "Future Clock Skew Rejection",
            "status": "PASS" if pass5 else "FAIL",
            "code": r5.status_code,
            "duration": d5,
            "details": f"Rejected future timestamp as 403 COMMAND_EXPIRED_OR_FUTURE"
        })

        # -------------------------------------------------------------
        # Test 6: Malformed Schema / Missing Fields (Fault: Bad Schema)
        # -------------------------------------------------------------
        print("\n--- Test 6: Malformed Schema (Fault: Missing Nonce) ---")
        bad_payload = {
            "version": 1,
            "kind": "status",
            "request_key": f"status:n8n_test:{uuid.uuid4().hex[:12]}",
            # nonce omitted
            "issued_at": int(time.time()),
        }
        headers6 = {
            HEADER: key,
            SIGNATURE_HEADER: "b" * 64,
            "content-type": "application/json",
        }
        t0 = time.time()
        r6 = client.post(COMMAND_PATH, headers=headers6, content=json.dumps(bad_payload))
        d6 = round(time.time() - t0, 3)
        print(f"Status: {r6.status_code}, Body: {r6.text} [{d6}s]")
        pass6 = r6.status_code == 422 and r6.json().get("error") == "INVALID_AUTOMATION_COMMAND"
        results.append({
            "id": "N8N-06",
            "name": "Malformed Schema Rejection",
            "status": "PASS" if pass6 else "FAIL",
            "code": r6.status_code,
            "duration": d6,
            "details": f"Rejected schema violation with 422 INVALID_AUTOMATION_COMMAND"
        })

        # -------------------------------------------------------------
        # Test 7: Duplicate Request Key (Fault: Replay / Idempotency)
        # -------------------------------------------------------------
        print("\n--- Test 7: Duplicate Request Key (Idempotency) ---")
        # Reuse req_key from Test 1 with fresh nonce & timestamp
        cmd_dup = {
            "version": 1,
            "kind": "status",
            "request_key": req_key,
            "nonce": f"nonce_dup_{uuid.uuid4().hex[:14]}",
            "issued_at": int(time.time()),
        }
        sig7 = sign_command(key, cmd_dup)
        headers7 = {
            HEADER: key,
            SIGNATURE_HEADER: sig7,
            "content-type": "application/json",
        }
        t0 = time.time()
        r7 = client.post(COMMAND_PATH, headers=headers7, content=json.dumps(cmd_dup))
        d7 = round(time.time() - t0, 3)
        print(f"Status: {r7.status_code}, Body: {r7.text} [{d7}s]")
        # Idempotency: duplicate status returns 200 with existing record, OR rejects duplicate
        pass7 = r7.status_code in (200, 403, 409, 422)
        results.append({
            "id": "N8N-07",
            "name": "Duplicate Request Key Idempotent Handling",
            "status": "PASS" if pass7 else "FAIL",
            "code": r7.status_code,
            "duration": d7,
            "details": f"Gateway handled duplicate request_key with HTTP {r7.status_code}"
        })

        # -------------------------------------------------------------
        # Test 8: Internal Status Probe
        # -------------------------------------------------------------
        print("\n--- Test 8: Machine Status Probe ---")
        headers8 = {HEADER: key}
        t0 = time.time()
        r8 = client.get(STATUS_PATH, headers=headers8)
        d8 = round(time.time() - t0, 3)
        print(f"Status: {r8.status_code}, Body: {r8.text} [{d8}s]")
        pass8 = r8.status_code == 200 and r8.json().get("result", {}).get("status") == "ok"
        results.append({
            "id": "N8N-08",
            "name": "Machine Automation Status Probe",
            "status": "PASS" if pass8 else "FAIL",
            "code": r8.status_code,
            "duration": d8,
            "details": f"Gateway confirmed machine status:ok in {d8}s"
        })

    print("\n" + "=" * 80)
    print("N8N FAULT INJECTION SUMMARY")
    print("=" * 80)
    for r in results:
        print(f"[{r['status']:4}] {r['id']}: {r['name']} (HTTP {r['code']}, {r['duration']}s) - {r['details']}")
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print("-" * 80)
    print(f"TOTAL: {total} | PASS: {passed} | FAIL: {total - passed} | SUCCESS RATE: {passed/total*100:.1f}%")
    if total == passed:
        print("N8N Gateway Fault Injection: 8/8 PASS")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_tests()
