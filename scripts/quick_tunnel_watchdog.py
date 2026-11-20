"""Quick Tunnel Continuous Auto-Healing Watchdog & Recovery Verification Script.
Monitors qldapm-ai-stage-quick-tunnel-1 health, measures auto-recovery time,
and verifies native web synchronization.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import httpx

ACCESS_DIR = os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\access")
CURRENT_URL_FILE = os.path.join(ACCESS_DIR, "current-url.json")
CONTAINER_NAME = "qldapm-ai-stage-quick-tunnel-1"


def get_current_url_info():
    if os.path.exists(CURRENT_URL_FILE):
        try:
            with open(CURRENT_URL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    return {"error": "file_not_found"}


def get_container_health(container_name=CONTAINER_NAME):
    cmd = ["docker", "inspect", container_name]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {"status": "not_found", "healthy": False}
    try:
        data = json.loads(res.stdout)[0]
        state = data.get("State", {})
        status = state.get("Status")
        health = state.get("Health", {}).get("Status")
        return {
            "status": status,
            "health": health,
            "running": state.get("Running", False),
            "restarting": state.get("Restarting", False),
            "healthy": health == "healthy",
            "uptime_started": state.get("StartedAt"),
        }
    except Exception as e:
        return {"status": "parse_error", "healthy": False, "error": str(e)}


def probe_public_url(url, timeout=10):
    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(url)
            duration = time.time() - t0
            return {
                "ok": resp.status_code in (200, 302),
                "status_code": resp.status_code,
                "duration": round(duration, 3),
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "duration": round(time.time() - t0, 3)}


def run_benchmark():
    print("=" * 80)
    print("QUICK TUNNEL AUTO-RECOVERY BENCHMARK (WAVE 3)")
    print(f"Target Container:  {CONTAINER_NAME}")
    print(f"Timestamp:         {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print("=" * 80)

    # 1. Baseline status
    print("\n--- Phase 1: Pre-Failure Baseline ---")
    base_health = get_container_health()
    base_url_info = get_current_url_info()
    base_url = base_url_info.get("url")
    print(f"Initial Container State: Status={base_health.get('status')}, Health={base_health.get('health')}")
    print(f"Initial Registered URL:  {base_url}")
    
    base_probe = probe_public_url(base_url)
    print(f"Initial Public Probe:    HTTP {base_probe.get('status_code')} in {base_probe.get('duration')}s")
    if not base_probe.get("ok"):
        print("WARNING: Baseline probe not OK, proceeding with recovery test anyway.")

    # 2. Inject Failure (Restart tunnel container)
    print("\n--- Phase 2: Simulating Transient Tunnel Outage (Restart) ---")
    t_start = time.time()
    restart_res = subprocess.run(["docker", "restart", CONTAINER_NAME], capture_output=True, text=True)
    t_restart_cmd = time.time() - t_start
    print(f"Docker restart issued: exit_code={restart_res.returncode} ({round(t_restart_cmd, 3)}s)")

    # 3. Monitor container health restoration
    print("\n--- Phase 3: Watchdog Monitoring Health & Tunnel Connection ---")
    t_healthy = None
    deadline = time.time() + 90
    while time.time() < deadline:
        h = get_container_health()
        if h.get("healthy"):
            t_healthy = time.time() - t_start
            print(f"Container regained 'healthy' state in {round(t_healthy, 3)}s")
            break
        time.sleep(1)

    if not t_healthy:
        print("FAIL: Container did not become healthy within 90s")
        return {"status": "FAIL", "reason": "healthcheck_timeout"}

    # 4. Monitor staging-web synchronization (current-url.json)
    print("\n--- Phase 4: Monitoring Hostname Synchronization by quick_tunnel_web.rb ---")
    t_synced = None
    new_url = None
    deadline = time.time() + 90
    while time.time() < deadline:
        url_info = get_current_url_info()
        cand_url = url_info.get("url")
        status_native = url_info.get("native_web")
        if cand_url and cand_url != base_url and status_native == "ready":
            t_synced = time.time() - t_start
            new_url = cand_url
            print(f"URL updated to {new_url} (native_web={status_native}) in {round(t_synced, 3)}s")
            break
        time.sleep(1)

    if not new_url:
        print("FAIL: quick_tunnel_web.rb did not publish updated ready state with new hostname within 90s")
        return {"status": "FAIL", "reason": "sync_timeout"}

    # 5. External probe verification
    print("\n--- Phase 5: Verifying Public HTTP Response at Recovered URL ---")
    t_public_ok = None
    deadline = time.time() + 45
    while time.time() < deadline:
        p = probe_public_url(new_url)
        if p.get("ok"):
            t_public_ok = time.time() - t_start
            print(f"Public HTTPS probe succeeded: HTTP {p.get('status_code')} in {p.get('duration')}s (Total Elapsed: {round(t_public_ok, 3)}s)")
            break
        time.sleep(1)

    if not t_public_ok:
        print("FAIL: Public URL not responding with HTTP 200/302 within 45s")
        return {"status": "FAIL", "reason": "public_probe_timeout"}

    total_time = round(t_public_ok, 3)
    print("\n" + "=" * 80)
    print("AUTO-RECOVERY BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Pre-Failure URL:              {base_url}")
    print(f"Post-Recovery URL:             {new_url}")
    print(f"Tunnel Health Regained:        {round(t_healthy, 3)}s")
    print(f"Native Web Host Synchronized:  {round(t_synced, 3)}s")
    print(f"Public HTTPS Service Restored: {round(t_public_ok, 3)}s")
    print(f"Total Recovery Duration:       {total_time}s")
    print("RESULT: PASS")
    print("=" * 80)

    return {
        "status": "PASS",
        "pre_url": base_url,
        "post_url": new_url,
        "t_healthy": round(t_healthy, 3),
        "t_synced": round(t_synced, 3),
        "t_public_ok": round(t_public_ok, 3),
        "total_recovery_duration": total_time,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true", help="Run auto-recovery benchmark")
    parser.add_argument("--check", action="store_true", help="Check current health status")
    args = parser.parse_args()

    if args.benchmark or len(sys.argv) == 1:
        run_benchmark()
    elif args.check:
        h = get_container_health()
        u = get_current_url_info()
        print(f"Health: {json.dumps(h, indent=2)}")
        print(f"URL: {json.dumps(u, indent=2)}")
